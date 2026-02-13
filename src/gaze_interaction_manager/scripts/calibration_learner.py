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
from scipy.stats import binned_statistic_2d
import matplotlib.cm as cm
import time

# Machine Learning Imports
from sklearn.linear_model import HuberRegressor
from sklearn.neighbors import KNeighborsRegressor


class CalibrationLearner(Node):
    def __init__(self):
        super().__init__("calibration_learner")

        # --- Parameters ---
        ## Toggles for visualization layers
        self.declare_parameter("publish_data_quiver", True)
        self.declare_parameter("show_raw_samples", True)
        self.declare_parameter("show_prediction", True)
        self.declare_parameter("show_binned_truth", True)

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

        # --- History Tracking ---
        self.start_time = None
        self.history_time = []  # In minutes
        self.history_scores = {name: [] for name in self.model_names}
        # Define fixed colors for models for visual consistency over time
        self.model_colors = {
            "Bias": "#1f77b4",  # Blue
            "Linear": "#ff7f0e",  # Orange
            "Quadratic": "#2ca02c",  # Green
            "Conical": "#d62728",  # Red
            "KNN": "#9467bd",  # Purple
        }

        # --- Plotting ---
        self.fig_main, self.ax_main = plt.subplots(figsize=(8, 6), dpi=100)
        self.canvas_main = FigureCanvasAgg(self.fig_main)
        # Wider plot for time series
        self.fig_tourney, self.ax_tourney = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas_tourney = FigureCanvasAgg(self.fig_tourney)

        # --- ROS Setup ---
        self.bridge = CvBridge()
        self.create_subscription(
            InteractionSegment, "calibration/interaction_segment", self.segment_cb, 10
        )
        self.model_pub = self.create_publisher(
            CalibrationModel, "calibration/model_update", 10
        )
        self.image_pub = self.create_publisher(Image, "calibration/data_quiver", 10)

        self.tourney_pub = self.create_publisher(
            Image, "calibration/tournament_status", 10
        )

        self.get_logger().info("Tournament Calibration Learner Initialized.")

    def segment_cb(self, msg: InteractionSegment):
        if self.start_time is None:
            self.start_time = self.get_clock().now()

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
            if self.get_parameter("publish_data_quiver").value:
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

        # Calculate current time in minutes
        elapsed_min = (
            (self.get_clock().now() - self.start_time).nanoseconds / 1e9 / 60.0
        )
        self.history_time.append(elapsed_min)

        for name in self.model_names:
            score, res = (
                self.solve_knn(X_train, Y_train)
                if name == "KNN"
                else self.solve_parametric(X_train, Y_train, name)
            )
            # Cap the score for history and leaderboard at 500
            # display_score = min(score, 500.0)
            self.model_scores[name] = score
            self.history_scores[name].append(score)

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
        if not self.db_gaze:
            return

        # Get current toggle states
        draw_raw = self.get_parameter("show_raw_samples").value
        draw_binned = self.get_parameter("show_binned_truth").value
        draw_pred = self.get_parameter("show_prediction").value

        # Data Prep
        gaze_pts = np.array(self.db_gaze)
        err_vecs = np.array(self.db_error)

        # Grid Prep (Match aggregator bin size)
        x_edges = np.arange(0, self.x_max + self.bin_size, self.bin_size)
        y_edges = np.arange(0, self.y_max + self.bin_size, self.bin_size)
        Xc, Yc = np.meshgrid(
            (x_edges[:-1] + x_edges[1:]) / 2, (y_edges[:-1] + y_edges[1:]) / 2
        )

        self.ax_main.clear()

        # --- LAYER 1: RAW SAMPLES (Colored by angle) ---
        if draw_raw:
            angles = np.arctan2(err_vecs[:, 1], err_vecs[:, 0])
            colors = cm.hsv((angles + np.pi) / (2 * np.pi))
            self.ax_main.quiver(
                gaze_pts[:, 0],
                gaze_pts[:, 1],
                err_vecs[:, 0],
                err_vecs[:, 1],
                color=colors,
                angles="xy",
                scale_units="xy",
                scale=1,
                alpha=0.4,
                width=0.0015,
            )

        # --- LAYER 2: BINNED TRUTH (Median vector per bin, Gray) ---
        avg_x, avg_y = None, None
        if draw_binned or draw_pred:
            # We compute this from raw db_gaze to show "Truth" regardless of model
            avg_x, _, _, _ = binned_statistic_2d(
                gaze_pts[:, 0],
                gaze_pts[:, 1],
                err_vecs[:, 0],
                "median",
                [x_edges, y_edges],
            )
            avg_y, _, _, _ = binned_statistic_2d(
                gaze_pts[:, 0],
                gaze_pts[:, 1],
                err_vecs[:, 1],
                "median",
                [x_edges, y_edges],
            )

            if draw_binned:
                mask = ~np.isnan(avg_x.T)
                self.ax_main.quiver(
                    Xc[mask],
                    Yc[mask],
                    avg_x.T[mask],
                    avg_y.T[mask],
                    angles="xy",
                    scale_units="xy",
                    scale=1,
                    color="gray",
                    alpha=0.6,
                    width=0.003,
                )

        # --- LAYER 3: PREDICTION (Active Tournament Model, Colored by residual) ---
        if draw_pred and self.active_model_name:
            px, py = self.predict_on_grid(Xc, Yc)

            # Color by distance from the binned truth
            if avg_x is not None:
                # avg_x is (NX, NY), px is (NY, NX), so we transpose avg to match
                diff = np.sqrt((px - avg_x.T) ** 2 + (py - avg_y.T) ** 2)
                diff_c = np.clip(diff, 0, 50)  # Max color at 50px error
                cmap = cm.jet
            else:
                diff_c = "blue"
                cmap = None

            self.ax_main.quiver(
                Xc,
                Yc,
                px,
                py,
                diff_c,
                angles="xy",
                scale_units="xy",
                scale=1,
                cmap=cmap,
                alpha=0.8,
                width=0.004,
            )

        # Final Render Settings for Main Plot
        self.ax_main.set_xlim(0, self.x_max)
        self.ax_main.set_ylim(self.y_max, 0)
        self.ax_main.set_title(f"Active Model: {self.active_model_name}")
        self.ax_main.set_axis_off()
        self.fig_main.tight_layout(pad=0)

        # --- TOURNAMENT SCOREBOARD ---
        self.ax_tourney.clear()
        for name in self.model_names:
            y_data = self.history_scores[name]
            if not y_data:
                continue

            # Use specific color, make the active model thicker
            is_active = name == self.active_model_name
            alpha = 1.0 if is_active else 0.4
            linewidth = 2.5 if is_active else 1.0

            self.ax_tourney.plot(
                self.history_time,
                y_data,
                label=name,
                color=self.model_colors[name],
                alpha=alpha,
                linewidth=linewidth,
            )

            # Add a point at the end of the line for the active one
            if is_active:
                self.ax_tourney.scatter(
                    self.history_time[-1],
                    y_data[-1],
                    color=self.model_colors[name],
                    s=40,
                    zorder=5,
                )

        self.ax_tourney.set_ylim(0, 505)  # Capped at 500 (+ buffer)
        self.ax_tourney.set_xlabel("Time (minutes)")
        self.ax_tourney.set_ylabel("LOOCV Error (pixels)")
        self.ax_tourney.set_title("Model Performance Over Time")
        self.ax_tourney.grid(True, linestyle="--", alpha=0.6)
        self.ax_tourney.legend(loc="upper right", fontsize="small")

        # --- Publish Both Images ---
        self.canvas_main.draw()
        self.canvas_tourney.draw()

        img_main = cv2.cvtColor(
            np.asarray(self.canvas_main.buffer_rgba()), cv2.COLOR_RGBA2BGR
        )
        img_tourney = cv2.cvtColor(
            np.asarray(self.canvas_tourney.buffer_rgba()), cv2.COLOR_RGBA2BGR
        )

        msg_main = self.bridge.cv2_to_imgmsg(img_main, "bgr8")
        msg_main.header.stamp = self.get_clock().now().to_msg()
        msg_main.header.frame_id = "gaze_debug"

        msg_tourney = self.bridge.cv2_to_imgmsg(img_tourney, "bgr8")
        msg_tourney.header.stamp = msg_main.header.stamp

        self.image_pub.publish(msg_main)
        self.tourney_pub.publish(msg_tourney)


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
