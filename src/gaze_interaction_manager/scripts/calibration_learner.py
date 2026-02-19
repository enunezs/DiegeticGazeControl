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
        self.grid_data = {}  # {(bx, by): [[ex1, ey1], [ex2, ey2], ...]}

        # --- Tournament State ---
        self.active_model_name = "Bias"
        self.active_model_objs = None  # Initialize here
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

        if len(msg.gaze_samples) != len(msg.target_samples):
            self.get_logger().error("Mismatched sample counts in segment!")
            return

        # segment_raw_errors = []
        all_target_x = []
        all_target_y = []

        # Iterate through matched pairs
        # target = msg.target_pixel

        for gaze, target in zip(msg.gaze_samples, msg.target_samples):

            # Calculate error vector for this sample
            err = [gaze.x - target.x, gaze.y - target.y]

            # Dont append if too big (>200px)
            if np.linalg.norm(err) > 200:
                continue

            # 1. Global Database (for the raw scatter plot)
            self.db_gaze.append([gaze.x, gaze.y])
            self.db_error.append(err)
            if len(self.db_gaze) > 5000:
                self.db_gaze.pop(0)
                self.db_error.pop(0)

            # 2. Sample-Level Binning (Split data correctly across bins)
            bx, by = int(target.x // self.bin_size), int(target.y // self.bin_size)

            # 3. Accumulative Storage (Combine data instead of overwriting)
            if (bx, by) not in self.grid_data:
                self.grid_data[(bx, by)] = []
            self.grid_data[(bx, by)].append(err)

            # segment_raw_errors.append(err)
            all_target_x.append(target.x)
            all_target_y.append(target.y)

        # if segment_raw_errors:
        #     # Determine the representative location for this segment (for binning)
        #     # TODO ERROR Not correct, should be based on gaze, and shoiuld be split based on bins, not averaged. We want to capture the error distribution across the segment, not just one point.

        #     avg_target_x = np.mean(
        #         all_target_x
        #     )  # -> Do we want to bin based on the average target position of the segment? This seems more accurate than using the first target point, especially if the segment has multiple samples that might span a small area.
        #     avg_target_y = np.mean(all_target_y)

        #     bx, by = int(avg_target_x // self.bin_size), int(
        #         avg_target_y // self.bin_size
        #     )

        #     # Store the median error for this specific grid bin
        #     self.grid_data[(bx, by)] = np.median(segment_raw_errors, axis=0)

        # 4. Filter for Tournament
        if len(self.grid_data) > 3:
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
            return None, None

        try:
            if self.get_parameter("use_ransac").value:
                # RANSAC: Hard rejection of outliers
                base = LinearRegression(fit_intercept=False)

                # Ensure RANSAC has at least as many samples as features
                min_samples = max(feat.shape[1] + 1, 5)
                if len(X) < min_samples:
                    return None, None

                reg_x = RANSACRegressor(
                    estimator=base, min_samples=min_samples, max_trials=100
                ).fit(feat, Y[:, 0])
                reg_y = RANSACRegressor(
                    estimator=base, min_samples=min_samples, max_trials=100
                ).fit(feat, Y[:, 1])
            else:
                # Traditional: Huber (robust weighting)
                reg_x = HuberRegressor(fit_intercept=False, epsilon=1.35).fit(
                    feat, Y[:, 0]
                )
                reg_y = HuberRegressor(fit_intercept=False, epsilon=1.35).fit(
                    feat, Y[:, 1]
                )

            # Note: RANSAC objects have 'estimator_' attribute for the underlying fit
            model_x = reg_x.estimator_ if hasattr(reg_x, "estimator_") else reg_x
            model_y = reg_y.estimator_ if hasattr(reg_y, "estimator_") else reg_y

            pred_x = reg_x.predict(feat)
            score = np.sqrt(np.mean((Y[:, 0] - pred_x) ** 2))

            return score, (model_x, model_y)

        except Exception as e:
            self.get_logger().debug(f"Solver {name} failed: {e}")
            return None, None

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
        # 1. Prepare training data from bins
        X_train, Y_train = [], []

        for (bx, by), error_list in self.grid_data.items():
            # Represent the bin by its center coordinate
            X_train.append(
                [
                    bx * self.bin_size + self.bin_size / 2,
                    by * self.bin_size + self.bin_size / 2,
                ]
            )

            # Use the median error of ALL samples ever recorded in this bin
            # This makes the calibration much more stable over time
            Y_train.append(np.median(error_list, axis=0))

        if not X_train:
            return
        X_train, Y_train = np.array(X_train), np.array(Y_train)

        # 2. Setup Tournament
        best_adj_score = float("inf")
        winner_name = self.active_model_name
        winner_results = None

        # Model complexity penalty (approximate BIC logic)
        penalties = {"Bias": 1, "Linear": 3, "Conical": 10, "Quadratic": 15, "KNN": 10}

        # Calculate current time in minutes
        elapsed_min = (
            (self.get_clock().now() - self.start_time).nanoseconds / 1e9 / 60.0
        )
        self.history_time.append(elapsed_min)

        # 3. Evaluate Models
        for name in self.model_names:
            if name == "KNN":
                score, res = self.solve_knn(X_train, Y_train)
            else:
                score, res = self.solve_parametric(X_train, Y_train, name)

            rec_score = score if score is not None else float("inf")
            self.model_scores[name] = rec_score
            self.history_scores[name].append(score if score is not None else np.nan)

            if score is not None:
                adj_score = score + (penalties.get(name, 0) * 0.5)
                if adj_score < best_adj_score:
                    best_adj_score = adj_score
                    winner_name = name
                    winner_results = res

        # 4. Update Active Model
        if winner_results:
            self.apply_winner(winner_name, winner_results)

    def apply_winner(self, name, results):
        self.active_model_name = name
        self.active_model_objs = (
            results  # <--- Add this line to store the sklearn models
        )
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
            # results[0] is the model for X error, results[1] is for Y error
            cx[3] = float(results[0].coef_[0])  # x-pos impact on x-error
            cx[4] = float(results[0].coef_[1])  # y-pos impact on x-error
            cx[5] = float(results[0].coef_[2])  # intercept for x-error

            cy[3] = float(results[1].coef_[0])  # x-pos impact on y-error
            cy[4] = float(results[1].coef_[1])  # y-pos impact on y-error
            cy[5] = float(results[1].coef_[2])  # intercept for y-error

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

        self.coeffs_x = cx
        self.coeffs_y = cy

        self.model_pub.publish(msg)

    def predict_on_grid(self, Xc, Yc):
        # 1. Handle KNN (Already uses objects)
        if self.active_model_name == "KNN" and self.knn_model_x:
            pts = np.c_[Xc.flatten(), Yc.flatten()]
            px = self.knn_model_x.predict(pts).reshape(Xc.shape)
            py = self.knn_model_y.predict(pts).reshape(Yc.shape)

        # 2. Handle Parametric Models using stored objects (The Fix)
        elif hasattr(self, "active_model_objs") and self.active_model_objs is not None:
            feat = self.get_features(
                np.c_[Xc.flatten(), Yc.flatten()], self.active_model_name
            )

            # Use the sklearn object's predict method
            px = self.active_model_objs[0].predict(feat).reshape(Xc.shape)
            py = self.active_model_objs[1].predict(feat).reshape(Xc.shape)
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
        if draw_raw and len(self.db_gaze) > 0:
            gaze_pts = np.array(self.db_gaze)
            err_vecs = np.array(self.db_error)
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
                alpha=0.1,
                width=0.001,
            )

        # --- LAYER 2: BINNED TRUTH ---
        if draw_binned and len(self.grid_data) > 0:
            bx_centers, by_centers, b_err_x, b_err_y = [], [], [], []
            for (bx, by), error_list in self.grid_data.items():
                median_err = np.median(error_list, axis=0)
                bx_centers.append(bx * self.bin_size + self.bin_size / 2)
                by_centers.append(by * self.bin_size + self.bin_size / 2)
                b_err_x.append(median_err[0])
                b_err_y.append(median_err[1])

            self.ax_main.quiver(
                bx_centers,
                by_centers,
                b_err_x,
                b_err_y,
                angles="xy",
                scale_units="xy",
                scale=1,
                color="black",
                alpha=0.4,
                width=0.002,
            )

        # --- LAYER 3: PREDICTION (The Complete Surface) ---
        if draw_pred and self.active_model_name:
            px, py = self.predict_on_grid(Xc, Yc)
            residual_mags = np.full(Xc.shape, np.nan)

            for (bx, by), error_list in self.grid_data.items():
                iy, ix = by, bx
                if iy < Xc.shape[0] and ix < Xc.shape[1]:
                    # FIX: Calculate median of the list before comparing to prediction
                    median_err = np.median(error_list, axis=0)
                    res_x = median_err[0] - px[iy, ix]
                    res_y = median_err[1] - py[iy, ix]
                    residual_mags[iy, ix] = np.sqrt(res_x**2 + res_y**2)

            cmap = plt.get_cmap("jet")
            norm = plt.Normalize(vmin=0, vmax=50)
            final_colors = cmap(norm(residual_mags))

            no_data_mask = np.isnan(residual_mags)
            final_colors[no_data_mask] = [0.7, 0.7, 0.7, 0.2]

            self.ax_main.quiver(
                Xc.flatten(),
                Yc.flatten(),
                px.flatten(),
                py.flatten(),
                color=final_colors.reshape(-1, 4),
                angles="xy",
                scale_units="xy",
                scale=1,
                alpha=0.8,
                width=0.004,
            )

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
            # Clean the history: replace inf/nan with a high number (500) for plotting
            raw_y = np.array(self.history_scores[name], dtype=float)

            if len(raw_y) == 0:
                continue

            has_data = True
            y_plot = np.where(np.isfinite(raw_y), raw_y, 500.0)
            # Cap at 500 so the plot doesn't explode
            y_plot = np.clip(y_plot, 0, 500)

            # Use specific color, make the active model thicker
            is_active = name == self.active_model_name
            alpha = 1.0 if is_active else 0.4
            linewidth = 2.5 if is_active else 1.0

            self.ax_tourney.plot(
                self.history_time,
                y_plot,
                label=name,
                color=self.model_colors[name],
                alpha=alpha,
                linewidth=linewidth,
            )

            # Add a point at the end of the line for the active one
            if is_active:
                self.ax_tourney.scatter(
                    self.history_time[-1],
                    y_plot[-1],
                    color=self.model_colors[name],
                    s=40,
                    zorder=5,
                )

        # self.ax_tourney.set_ylim(
        #     0,
        #     max(
        #         50,
        #         max(max(scores) for scores in self.history_scores.values() if scores),
        #     ),
        # )
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
