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
from sklearn.linear_model import RANSACRegressor, LinearRegression


class CalibrationLearner(Node):
    def __init__(self):
        super().__init__("calibration_learner")

        # --- Parameters ---
        ## Toggles for visualization layers
        self.declare_parameter("publish_data_quiver", True)
        self.declare_parameter("show_raw_samples", True)
        self.declare_parameter("show_prediction", True)
        self.declare_parameter("show_binned_truth", True)
        self.declare_parameter("use_ransac", True)

        # --- Aggregator ---
        self.db_gaze = []
        self.db_error = []
        self.grid_data = {}  # {(bin_x, bin_y): median_error_vector}
        self.bin_size = 100
        self.x_max, self.y_max = 1600, 1200

        # --- Tournament State ---
        self.active_model_name = "Bias"
        self.model_names = ["Bias", "Linear"]

        # self.model_names = ["Bias", "Linear", "Quadratic", "Conical"]
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
            if self.get_parameter("use_ransac").value:
                # RANSAC: Hard rejection of outliers
                base = LinearRegression(fit_intercept=False)
                reg_x = RANSACRegressor(estimator=base, min_samples=0.5).fit(
                    feat, Y[:, 0]
                )
                reg_y = RANSACRegressor(estimator=base, min_samples=0.5).fit(
                    feat, Y[:, 1]
                )
            else:
                # Traditional: Huber (robust weighting)
                reg_x = HuberRegressor(fit_intercept=False).fit(feat, Y[:, 0])
                reg_y = HuberRegressor(fit_intercept=False).fit(feat, Y[:, 1])

            # Note: RANSAC objects have 'estimator_' attribute for the underlying fit
            model_x = reg_x.estimator_ if hasattr(reg_x, "estimator_") else reg_x
            model_y = reg_y.estimator_ if hasattr(reg_y, "estimator_") else reg_y

            # # We use fit_intercept=False because our features ALREADY include a column of ones.
            # # This ensures the number of coefficients matches the number of feature columns.
            # reg_x = HuberRegressor(fit_intercept=False, epsilon=1.35).fit(feat, Y[:, 0])
            # reg_y = HuberRegressor(fit_intercept=False, epsilon=1.35).fit(feat, Y[:, 1])

            # Hat Matrix LOOCV shortcut for certainty/fit quantification
            # XTX_inv = np.linalg.pinv(feat.T @ feat)
            # H = np.sum((feat @ XTX_inv) * feat, axis=1)
            # res_x = Y[:, 0] - reg_x.predict(feat)
            # # Prevent division by zero if H is 1
            # loocv_x = np.mean((res_x / (1 - np.clip(H, 0, 0.99) + 1e-6)) ** 2)
            # return np.sqrt(loocv_x), (reg_x, reg_y)

            pred_x = reg_x.predict(feat)
            score = np.sqrt(np.mean((Y[:, 0] - pred_x) ** 2))

            return score, (model_x, model_y)

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
            if name == "KNN":
                score, res = self.solve_knn(X_train, Y_train)
            else:
                score, res = self.solve_parametric(X_train, Y_train, name)

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
            # "KNN": CalibrationModel.TYPE_KNN_GRID,
        }
        msg.model_type = mapping.get(name, CalibrationModel.TYPE_BIAS)
        # Feature matrix as [x^2, y^2, xy, x, y, ones]

        # Initialize with zeros
        cx = [0.0] * 6
        cy = [0.0] * 6

        if name == "Bias":
            # Feature matrix was [ones], so coef_[0] is the constant offset
            cx[5] = float(results[0].coef_[0])
            cy[5] = float(results[1].coef_[0])

        elif name == "Linear":
            # Feature matrix was [x, y, ones]
            cx[3] = float(results[0].coef_[0])  # x
            cx[4] = float(results[1].coef_[1])  # y
            cx[5] = float(results[0].coef_[2])  # intercept (ones)

        elif name == "Quadratic":
            # Feature matrix was [x^2, y^2, xy, x, y, ones]
            # These map 1:1 to our [0, 1, 2, 3, 4, 5] structure
            cx = [float(c) for c in results[0].coef_]
            cy = [float(c) for c in results[1].coef_]

        elif name == "Conical":
            # For conical, since it doesn't fit the [x^2...1] polynomial exactly,
            # we can still pass the main coefficients or handle it as a special case.
            # For now, let's just pass the linear/bias parts:
            cx[3], cx[4], cx[5] = (
                float(results[0].coef_[0]),
                float(results[0].coef_[1]),
                float(results[0].coef_[3]),
            )
            cy[3], cy[4], cy[5] = (
                float(results[1].coef_[0]),
                float(results[1].coef_[1]),
                float(results[1].coef_[3]),
            )

        elif name == "KNN":
            pass
            # self.knn_model_x, self.knn_model_y = results
            # msg.coeffs_x, msg.coeffs_y = [], []

        msg.coeffs_x = cx
        msg.coeffs_y = cy
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

        # 1. Main Gaze Plot
        img_main = self.draw_gaze_overlay()

        # 2. Tournament Plot
        img_tourney = self.draw_tournament_stats()

        # --- Publish Both Images ---
        msg_main = self.bridge.cv2_to_imgmsg(img_main, "bgr8")
        msg_main.header.stamp = self.get_clock().now().to_msg()
        msg_main.header.frame_id = "gaze_debug"

        msg_tourney = self.bridge.cv2_to_imgmsg(img_tourney, "bgr8")
        msg_tourney.header.stamp = msg_main.header.stamp

        self.image_pub.publish(msg_main)
        self.tourney_pub.publish(msg_tourney)

    def draw_gaze_overlay(self):
        self.ax_main.clear()

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

        # --- LAYER 1: RAW SAMPLES ---
        if draw_raw and len(gaze_pts) > 0:
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
                alpha=0.2,
                width=0.001,
            )

        # --- LAYER 2: BINNED TRUTH ---
        avg_x, avg_y = None, None
        if (draw_binned or draw_pred) and len(gaze_pts) > 0:
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

        # --- LAYER 3: PREDICTION (The Complete Surface) ---
        if draw_pred and self.active_model_name:
            px, py = self.predict_on_grid(Xc, Yc)

            # 1. Initialize Residual Mags with NaN
            residual_mags = np.full(Xc.shape, np.nan)

            # 2. Fill residuals where ground truth exists in our aggregator
            for (bx, by), truth_vec in self.grid_data.items():
                iy, ix = by, bx  # Indices in the grid
                if iy < Xc.shape[0] and ix < Xc.shape[1]:
                    res_x = truth_vec[0] - px[iy, ix]
                    res_y = truth_vec[1] - py[iy, ix]
                    residual_mags[iy, ix] = np.sqrt(res_x**2 + res_y**2)

            # 3. Create a Manual Color Array
            # This ensures arrows are drawn even if they have no residual to compare to
            try:
                cmap = plt.colormaps.get_cmap("jet")
            except AttributeError:
                cmap = plt.get_cmap("jet")

            # Normalize residuals (0 to 50px) for the colormap
            norm = plt.Normalize(vmin=0, vmax=50)
            # Map residual magnitudes to RGBA (Result is shape [H, W, 4])
            # Note: NaNs in the norm/cmap process usually result in the first color or transparent
            final_colors = cmap(norm(residual_mags))

            # 4. Identify "No Data" bins and set them to gray
            # residual_mags is NaN where no calibration points exist in that bin
            no_data_mask = np.isnan(residual_mags)
            final_colors[no_data_mask] = [0.7, 0.7, 0.7, 0.3]  # Light Gray, low alpha

            # 5. Plot the full grid
            # Flatten everything to avoid broadcasting issues
            self.ax_main.quiver(
                Xc.flatten(),
                Yc.flatten(),
                px.flatten(),
                py.flatten(),
                color=final_colors.reshape(-1, 4),  # Flatten [H, W, 4] to [N, 4]
                angles="xy",
                scale_units="xy",
                scale=1,
                alpha=0.8,
                width=0.004,
            )

        # Final Render Settings
        self.ax_main.set_xlim(0, self.x_max)
        self.ax_main.set_ylim(self.y_max, 0)
        self.ax_main.set_title(f"Active Model: {self.active_model_name}")
        self.ax_main.set_axis_off()
        self.fig_main.tight_layout(pad=0)
        self.canvas_main.draw()

        return cv2.cvtColor(
            np.asarray(self.canvas_main.buffer_rgba()), cv2.COLOR_RGBA2BGR
        )

    def draw_tournament_stats(self):
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
        self.ax_tourney.set_title(
            f"Model Performance Over Time (R: {self.get_parameter('use_ransac').value})"
        )
        self.ax_tourney.grid(True, linestyle="--", alpha=0.6)
        self.ax_tourney.legend(loc="upper right", fontsize="small")

        self.canvas_tourney.draw()
        return cv2.cvtColor(
            np.asarray(self.canvas_tourney.buffer_rgba()), cv2.COLOR_RGBA2BGR
        )


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
