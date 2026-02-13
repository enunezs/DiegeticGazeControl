#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from gaze_interaction_manager.msg import InteractionSegment, CalibrationModel

import numpy as np
import cv2
from cv_bridge import CvBridge
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

# Machine Learning Imports
from sklearn.linear_model import HuberRegressor
from sklearn.neighbors import KNeighborsRegressor


class CalibrationLearner(Node):
    def __init__(self):
        super().__init__("calibration_learner")

        # --- Parameters ---
        self.declare_parameter("show_raw_samples", True)
        self.declare_parameter("show_prediction", True)
        self.declare_parameter("publish_debug_image", True)

        # --- Aggregator ---
        self.db_gaze = []
        self.db_error = []
        self.grid_data = {}  # {(bin_x, bin_y): median_error_vector}
        self.bin_size = 40
        self.x_max, self.y_max = 1600, 1200

        # --- Tournament State ---
        self.active_model_name = "Bias"
        self.model_names = ["Bias", "Linear", "Quadratic", "Conical", "KNN"]
        self.model_scores = {name: float("inf") for name in self.model_names}
        self.coeffs_x = None
        self.coeffs_y = None
        self.knn_model_x = None
        self.knn_model_y = None

        # --- Plotting ---
        self.fig_main, self.ax_main = plt.subplots(figsize=(8, 6), dpi=100)
        self.canvas_main = FigureCanvasAgg(self.fig_main)
        self.fig_tourney, self.ax_tourney = plt.subplots(figsize=(4, 5), dpi=100)
        self.canvas_tourney = FigureCanvasAgg(self.fig_tourney)

        # --- ROS Setup ---
        self.bridge = CvBridge()
        self.create_subscription(
            InteractionSegment, "calibration/interaction_segment", self.segment_cb, 10
        )
        self.model_pub = self.create_publisher(
            CalibrationModel, "calibration/model_update", 10
        )
        self.image_pub = self.create_publisher(
            Image, "calibration/debug_plot_image", 10
        )
        self.tourney_pub = self.create_publisher(
            Image, "calibration/tournament_status", 10
        )

        self.get_logger().info("Tournament Calibration Learner Initialized.")

    def segment_cb(self, msg: InteractionSegment):
        target = msg.target_pixel
        segment_raw_errors = []
        for s in msg.samples:
            self.db_gaze.append([s.x, s.y])
            err = [s.x - target.x, s.y - target.y]
            self.db_error.append(err)
            segment_raw_errors.append(err)

        if segment_raw_errors:
            bx, by = int(target.x // self.bin_size), int(target.y // self.bin_size)
            self.grid_data[(bx, by)] = np.median(segment_raw_errors, axis=0)

        if len(self.grid_data) > 1:
            self.run_model_tournament()
            if self.get_parameter("publish_debug_image").value:
                self.publish_plots()

    def get_features(self, X, model_name):
        """Generates feature matrices. IMPORTANT: Includes 'ones' column for intercept."""
        if model_name == "Bias":
            return np.ones((len(X), 1))
        elif model_name == "Linear":
            return np.c_[X, np.ones(len(X))]
        elif model_name == "Quadratic":
            return np.c_[
                X[:, 0] ** 2,
                X[:, 1] ** 2,
                X[:, 0] * X[:, 1],
                X[:, 0],
                X[:, 1],
                np.ones(len(X)),
            ]
        elif model_name == "Conical":
            r = np.sqrt((X[:, 0] - 800) ** 2 + (X[:, 1] - 600) ** 2).reshape(-1, 1)
            return np.c_[X, r, np.ones(len(X))]
        return None

    def solve_parametric(self, X, Y, name):
        feat = self.get_features(X, name)
        # Check if we have enough points for the number of features
        if feat is None or len(X) < feat.shape[1]:
            return float("inf"), None

        try:
            # We use fit_intercept=False because our features ALREADY include a column of ones.
            # This ensures the number of coefficients matches the number of feature columns.
            reg_x = HuberRegressor(fit_intercept=False, epsilon=1.35).fit(feat, Y[:, 0])
            reg_y = HuberRegressor(fit_intercept=False, epsilon=1.35).fit(feat, Y[:, 1])

            # Hat Matrix LOOCV shortcut for certainty/fit quantification
            XTX_inv = np.linalg.pinv(feat.T @ feat)
            H = np.sum((feat @ XTX_inv) * feat, axis=1)
            res_x = Y[:, 0] - reg_x.predict(feat)
            # Prevent division by zero if H is 1
            loocv_x = np.mean((res_x / (1 - np.clip(H, 0, 0.99) + 1e-6)) ** 2)
            return np.sqrt(loocv_x), (reg_x, reg_y)
        except:
            return float("inf"), None

    def solve_knn(self, X, Y):
        if len(X) < 5:
            return float("inf"), None
        try:
            knn_x = KNeighborsRegressor(
                n_neighbors=min(len(X) - 1, 5), weights="distance"
            ).fit(X, Y[:, 0])
            knn_y = KNeighborsRegressor(
                n_neighbors=min(len(X) - 1, 5), weights="distance"
            ).fit(X, Y[:, 1])
            # Manual LOOCV for KNN
            errors = []
            for i in range(len(X)):
                X_sub, Y_sub = np.delete(X, i, axis=0), np.delete(Y, i, axis=0)
                test = KNeighborsRegressor(n_neighbors=min(len(X_sub), 3)).fit(
                    X_sub, Y_sub[:, 0]
                )
                errors.append((Y[i, 0] - test.predict(X[i].reshape(1, -1))) ** 2)
            return np.sqrt(np.mean(errors)), (knn_x, knn_y)
        except:
            return float("inf"), None

    def run_model_tournament(self):
        X_train = np.array(
            [
                (k[0] * self.bin_size, k[1] * self.bin_size)
                for k in self.grid_data.keys()
            ]
        )
        Y_train = np.array(list(self.grid_data.values()))

        best_score = float("inf")
        winner_name = self.active_model_name
        winner_results = None

        # Model complexity penalty (approximate BIC logic)
        penalties = {"Bias": 1, "Linear": 3, "Conical": 4, "Quadratic": 6, "KNN": 10}

        for name in self.model_names:
            score, res = (
                self.solve_knn(X_train, Y_train)
                if name == "KNN"
                else self.solve_parametric(X_train, Y_train, name)
            )
            self.model_scores[name] = score

            adj_score = score + (penalties[name] * 0.5)
            if adj_score < best_score and score != float("inf"):
                best_score = adj_score
                winner_name = name
                winner_results = res

        if winner_results:
            self.apply_winner(winner_name, winner_results)

    def apply_winner(self, name, results):
        self.active_model_name = name
        msg = CalibrationModel()

        mapping = {
            "Bias": CalibrationModel.TYPE_BIAS,
            "Linear": CalibrationModel.TYPE_LINEAR,
            "Quadratic": CalibrationModel.TYPE_QUADRATIC,
            "Conical": CalibrationModel.TYPE_CONICAL,
            "KNN": CalibrationModel.TYPE_KNN_GRID,
        }
        msg.model_type = mapping.get(name, CalibrationModel.TYPE_BIAS)

        if name == "KNN":
            self.knn_model_x, self.knn_model_y = results
            msg.coeffs_x, msg.coeffs_y = [], []
        else:
            self.coeffs_x = results[0].coef_.tolist()
            self.coeffs_y = results[1].coef_.tolist()
            msg.coeffs_x, msg.coeffs_y = self.coeffs_x, self.coeffs_y

        self.model_pub.publish(msg)

    def predict_on_grid(self, Xc, Yc):
        if self.active_model_name == "KNN" and self.knn_model_x:
            pts = np.c_[Xc.flatten(), Yc.flatten()]
            px = self.knn_model_x.predict(pts).reshape(Xc.shape)
            py = self.knn_model_y.predict(pts).reshape(Yc.shape)
        elif self.coeffs_x is not None:
            feat = self.get_features(
                np.c_[Xc.flatten(), Yc.flatten()], self.active_model_name
            )
            px = (feat @ np.array(self.coeffs_x)).reshape(Xc.shape)
            py = (feat @ np.array(self.coeffs_y)).reshape(Yc.shape)
        else:
            return np.zeros_like(Xc), np.zeros_like(Yc)

        return np.clip(px, -250, 250), np.clip(py, -250, 250)

    def publish_plots(self):
        # Setup Grid
        x_edges = np.arange(0, self.x_max + self.bin_size, self.bin_size)
        y_edges = np.arange(0, self.y_max + self.bin_size, self.bin_size)
        Xc, Yc = np.meshgrid(
            (x_edges[:-1] + x_edges[1:]) / 2, (y_edges[:-1] + y_edges[1:]) / 2
        )

        # Main Plot
        self.ax_main.clear()
        if self.get_parameter("show_raw_samples").value and self.db_gaze:
            gpts = np.array(self.db_gaze)
            self.ax_main.scatter(gpts[:, 0], gpts[:, 1], s=1, alpha=0.1, c="gray")

        if self.get_parameter("show_prediction").value:
            px, py = self.predict_on_grid(Xc, Yc)
            self.ax_main.quiver(
                Xc,
                Yc,
                px,
                py,
                color="blue",
                alpha=0.5,
                scale=1,
                scale_units="xy",
                angles="xy",
            )

        self.ax_main.set_xlim(0, self.x_max)
        self.ax_main.set_ylim(self.y_max, 0)
        self.ax_main.set_title(f"Active: {self.active_model_name}")

        # Tournament Plot
        self.ax_tourney.clear()
        names = list(self.model_scores.keys())
        scores = [
            self.model_scores[n] if self.model_scores[n] != float("inf") else 0
            for n in names
        ]
        colors = ["gold" if n == self.active_model_name else "skyblue" for n in names]
        bars = self.ax_tourney.barh(names, scores, color=colors)
        self.ax_tourney.set_title("LOOCV Scoreboard")
        self.ax_tourney.invert_yaxis()
        self.ax_tourney.bar_label(bars, fmt="%.1f px", padding=3)

        # Publish
        self.canvas_main.draw()
        self.canvas_tourney.draw()
        img_m = cv2.cvtColor(
            np.asarray(self.canvas_main.buffer_rgba()), cv2.COLOR_RGBA2BGR
        )
        img_t = cv2.cvtColor(
            np.asarray(self.canvas_tourney.buffer_rgba()), cv2.COLOR_RGBA2BGR
        )
        self.image_pub.publish(self.bridge.cv2_to_imgmsg(img_m, "bgr8"))
        self.tourney_pub.publish(self.bridge.cv2_to_imgmsg(img_t, "bgr8"))


def main():
    rclpy.init()
    node = CalibrationLearner()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
