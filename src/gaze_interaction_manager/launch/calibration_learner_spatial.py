#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from gaze_interaction_manager.msg import InteractionSegment, CalibrationModel

import numpy as np
import cv2
from cv_bridge import CvBridge
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.cm as cm
import matplotlib.gridspec as gridspec


# Machine Learning Imports
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import RANSACRegressor, LinearRegression
from sklearn.model_selection import ShuffleSplit


# ==========================================
# 1. SHARED RESOURCE: SPATIAL RESERVOIR
# ==========================================
class SpatialReservoir:
    def __init__(self, cfg):
        self.cfg = cfg
        self.bins = {}  # (bx, by) -> deque
        self.bin_size = cfg.get("bin_size", 100)
        self.max_samples = cfg.get("samples_per_bin", 10)
        self.val_size = cfg.get("val_size", 2)

    def add_segment(self, gx, gy, ex, ey):
        """Processes a new segment into the shared spatial bins."""
        stride = self.cfg.get("thinning_stride", 30)
        gx_t, gy_t, ex_t, ey_t = gx[::stride], gy[::stride], ex[::stride], ey[::stride]

        for i in range(len(gx_t)):
            # Basic outlier rejection before binning
            if abs(ex_t[i]) > 250 or abs(ey_t[i]) > 250:
                continue

            bid = (int(gx_t[i] // self.bin_size), int(gy_t[i] // self.bin_size))
            if bid not in self.bins:
                self.bins[bid] = deque(maxlen=self.max_samples)

            self.bins[bid].append((gx_t[i], gy_t[i], ex_t[i], ey_t[i]))

    def get_train_val_split(self):
        """Returns flattened arrays for training and validation."""
        train_list, val_list = [], []
        for samples in self.bins.values():
            s_list = list(samples)
            if len(s_list) > self.val_size:
                val_list.extend(s_list[-self.val_size :])
                train_list.extend(s_list[: -self.val_size])
            else:
                val_list.extend(s_list)
        return np.array(train_list), np.array(val_list)


# ==========================================
# 2. THE MATHEMATICAL MODELS
# ==========================================
class GazeCorrectionFramework:
    """
    Unified Gaze Compensation Engine - Validated Logic
    Used as a competitor within the Tournament.
    """

    def __init__(self, name, features, config, trigger_bins=15):
        self.name = name
        self.cfg = config
        self.trigger_bins = trigger_bins
        self.cx, self.cy = self.cfg.get("center_x", 800), self.cfg.get("center_y", 600)

        # Internal State (Models and Coefficients)
        self.params = {"x": None, "y": None}
        self.models = {"x": None, "y": None}
        self.prequential_errors = []
        self.unlock_moments = {}

        # Recipe Definition
        self.master_recipe = features
        self.is_identity = "identity" in self.master_recipe
        # Start simple (Bias) unless it's the raw/identity model
        self.current_features = self.master_recipe if self.is_identity else ["bias"]

        # Screen Constants
        self.feature_library = {
            "identity": lambda dx, dy, r, r2: [],
            "bias": lambda dx, dy, r, r2: [np.ones_like(dx)],
            "lin_x": lambda dx, dy, r, r2: [dx / self.cx],
            "lin_y": lambda dx, dy, r, r2: [dy / self.cy],
            "quad_x": lambda dx, dy, r, r2: [(dx**2 * np.sign(dx)) / self.cx**2],
            "quad_y": lambda dx, dy, r, r2: [(dy**2 * np.sign(dy)) / self.cy**2],
            'cross_xy':   lambda dx, dy, r, r2: [(dx * dy) / (self.cx * self.cy)],

            'radial':    lambda dx, dy, r, r2: [(dx * r) / self.cx**2, (dy * r) / self.cy**2],
            # 'rad_simple': lambda dx, dy, r, r2: [dx * r, dy * r], 
            "radial_2": lambda dx, dy, r, r2: [
                (dx * r2) / self.cx**3,
                (dy * r2) / self.cy**3,
            ],
            # 'rad_scale_2': lambda dx, dy, r, r2: [dx * r2, dy * r2], 
            'radial_universal': lambda dx, dy, r, r2: [(dx*r2)/self.cx**3, (dy*r2)/self.cy**3, dx/self.cx, dy/self.cy, np.ones_like(dx)],

            "full_conic": lambda dx, dy, r, r2: [
                dx**2 / self.cx**2,
                dy**2 / self.cy**2,
                (dx * dy) / (self.cx * self.cy),
                dx / self.cx,
                dy / self.cy,
                np.ones_like(dx),
            ],
            "sig_x": lambda dx, dy, r, r2: [np.tanh(dx / (self.cx / 2))],
            "sig_y": lambda dx, dy, r, r2: [np.tanh(dy / (self.cy / 2))],
            "sigmoid": lambda dx, dy, r, r2: [
                np.tanh(dx / 400),
                np.tanh(dy / 300),
                np.ones_like(dx),
            ],
            'cub_x':      lambda dx, dy, r, r2: [(dx**3) / self.cx**3],
            'cub_y':      lambda dx, dy, r, r2: [(dy**3) / self.cy**3],
            'tangent_x':  lambda dx, dy, r, r2: [(2*dx*dy) / self.cx**2, (r2 + 2*dx**2) / self.cx**2],
            'tangent_y':  lambda dx, dy, r, r2: [(r2 + 2*dy**2) / self.cy**2, (2*dx*dy) / self.cy**2]
        }

    def _get_matrix(self, dx, dy, features):
        if not features or features == ["identity"]:
            return np.zeros((len(dx), 0))

        r2, r = dx**2 + dy**2, np.sqrt(dx**2 + dy**2)
        cols = []
        for f in features:
            cols.extend(self.feature_library[f](dx, dy, r, r2))
        return np.column_stack(cols)

    def _get_solver(self, key):
        """Solver factory. Handles shape changes for Huber warm_start."""
        if self.is_identity:
            return None

        s_type = self.cfg.get("solver", "huber")
        alpha = self.cfg.get("solver_alpha", 0.1)

        n_cols = self._get_matrix(
            np.array([0]), np.array([0]), self.current_features
        ).shape[1]
        m = self.models.get(key)

        if s_type == "huber":
            if m is None or (hasattr(m, "coef_") and len(m.coef_) != n_cols):
                return HuberRegressor(
                    epsilon=1.35,
                    max_iter=1000,
                    alpha=alpha,
                    warm_start=True,
                    fit_intercept=False,
                )
            return m
        if s_type == "ridge":
            return Ridge(alpha=alpha, fit_intercept=False)

        if s_type == "linear":
            return LinearRegression(fit_intercept=False)
        return Ridge(alpha=alpha)

    def predict(self, gx, gy):
        if self.is_identity or self.params["x"] is None or len(self.params["x"]) == 0:
            return np.zeros_like(gx), np.zeros_like(gy)

        dx, dy = gx - self.cx, gy - self.cy
        A = self._get_matrix(dx, dy, self.current_features)
        return A @ self.params["x"], A @ self.params["y"]

    def train(self, train_samples, n_bins, event_idx):
        if self.is_identity:
            return

        # Step 1: Handle model graduation (Bias -> Master Recipe)
        if self.current_features == ["bias"] and n_bins >= self.trigger_bins:
            self.current_features = self.master_recipe
            self.unlock_moments["activation"] = event_idx
            self.models = {"x": None, "y": None}  # Reset solvers for shape change

        # Step 2: Solver Fit
        if len(train_samples) < 3:
            return

        data = np.array(train_samples)
        train_gx, train_gy, train_ex, train_ey = (
            data[:, 0],
            data[:, 1],
            data[:, 2],
            data[:, 3],
        )
        train_dx, train_dy = train_gx - self.cx, train_gy - self.cy

        A = self._get_matrix(train_dx, train_dy, self.current_features)
        mx, my = self._get_solver("x"), self._get_solver("y")

        # self.params["x"], self.params["y"] = mx.coef_, my.coef_

        # Fit models
        self.models["x"] = mx.fit(A, train_ex)
        self.models["y"] = my.fit(A, train_ey)

        # Save coefficients
        self.params["x"], self.params["y"] = (
            self.models["x"].coef_,
            self.models["y"].coef_,
        )


class CalibrationLearner(Node):
    def __init__(self):
        super().__init__("calibration_learner_reservoir")

        # --- Shared Reservoir ---
        self.cfg = {
            "center_x": 800,
            "center_y": 600,
            "screen_w": 1600,
            "screen_h": 1200,
            "bin_size": 100,
            "samples_per_bin": 10,
            "val_size": 2,
            "thinning_stride": 25,
            # "trigger_bins": 12,
        }
        # self.reservoir = SpatialReservoir(self.cfg)

        # --- The Shared Data Structure ---
        self.reservoir = {}  # (bx, by) -> deque
        self.raw_history = []  # Global RMSE for "Identity" baseline

        # --- Competitors ---
        self.competitors = [
            GazeCorrectionFramework("Raw", ["identity"], self.cfg, trigger_bins=0),
            GazeCorrectionFramework("Bias", ["bias"], self.cfg, trigger_bins=4),
            GazeCorrectionFramework("Basic Radial", ["bias", "radial_2"], self.cfg, trigger_bins=15),
            GazeCorrectionFramework("Complete Radial", ["radial_universal","bias"], self.cfg, trigger_bins=25),
            GazeCorrectionFramework("Conic", ["bias", "full_conic"], self.cfg, trigger_bins=15),
            GazeCorrectionFramework("Radial + Sigmoid", ["bias", "sigmoid"], self.cfg, trigger_bins=15),
            GazeCorrectionFramework("Hybrid", ["bias", "sigmoid", "tangent_x", "tangent_y"], self.cfg, trigger_bins=15),

        ]
        self.active_idx = 1
        self.event_count = 0

        # --- ROS Setup ---

        ## Toggles for visualization layers
        self.declare_parameter("publish_data_quiver", True)
        self.declare_parameter("show_raw_samples", True)
        self.declare_parameter("show_prediction", True)
        self.declare_parameter("show_binned_truth", True)
        self.declare_parameter("use_ransac", False)

        self.declare_parameter("cv_iterations", 5)
        self.declare_parameter("test_size", 0.1)  # 20% for validation

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

        # --- Plotting ---
        self.fig_main, self.ax_main = plt.subplots(figsize=(8, 6), dpi=100)
        self.fig_tourney, self.ax_tourney = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas_main = FigureCanvasAgg(self.fig_main)
        self.canvas_tourney = FigureCanvasAgg(self.fig_tourney)

    def segment_cb(self, msg: InteractionSegment):
        if self.start_time is None:
            self.start_time = self.get_clock().now()

        if len(msg.gaze_samples) != len(msg.target_samples):
            self.get_logger().error("Mismatched sample counts in segment!")
            return

        # TODO: not append if sample error greater than 200

        # 1. Parse Segment
        gx = np.array([p.x for p in msg.gaze_samples])
        gy = np.array([p.y for p in msg.gaze_samples])
        tx = np.array([p.x for p in msg.target_samples])
        ty = np.array([p.y for p in msg.target_samples])

        # Error relative to target (Ground Truth)
        ex, ey = gx - tx, gy - ty

        # 2. Phase 1: Prequential Evaluation (TEST)
        # Evaluate all models BEFORE they learn from this segment
        best_aulc = float("inf")
        for i, model in enumerate(self.competitors):
            if model.params["x"] is not None:
                px, py = model.predict(gx, gy)
                rmse = np.sqrt(np.mean((ex - px) ** 2 + (ey - py) ** 2))
            else:
                rmse = np.sqrt(np.mean(ex**2 + ey**2))

            model.prequential_errors.append(rmse)

            # Winner selection (exclude 'Raw')
            if i > 0:
                aulc = np.mean(model.prequential_errors)
                if aulc < best_aulc:
                    best_aulc = aulc
                    self.active_idx = i

        # 3. Phase 2: Update Shared Reservoir (DATA MANAGEMENT)
        stride = self.cfg["thinning_stride"]
        gx_t, gy_t, ex_t, ey_t = gx[::stride], gy[::stride], ex[::stride], ey[::stride]

        for i in range(len(gx_t)):
            if abs(ex_t[i]) > 400 or abs(ey_t[i]) > 400:
                continue
            bid = (
                int(gx_t[i] // self.cfg["bin_size"]),
                int(gy_t[i] // self.cfg["bin_size"]),
            )
            if bid not in self.reservoir:
                self.reservoir[bid] = deque(maxlen=self.cfg["samples_per_bin"])
            self.reservoir[bid].append((gx_t[i], gy_t[i], ex_t[i], ey_t[i]))

        # 4. PHASE 3: SHARED TRAINING
        # Gather all data from bins once
        train_pool = []
        for samples in self.reservoir.values():
            s_list = list(samples)
            # Use Stratified Split logic (Newest for Val, Older for Train)
            if len(s_list) > self.cfg["val_size"]:
                train_pool.extend(s_list[: -self.cfg["val_size"]])
            else:
                train_pool.extend(s_list)

        train_data = np.array(train_pool)
        n_bins = len(self.reservoir)

        for model in self.competitors:
            model.train(train_data, n_bins, self.event_count)

        self.event_count += 1
        self.publish_model_update()
        self.publish_visuals(gx, gy, ex, ey)

    def publish_model_update(self):
        winner = self.competitors[self.active_idx]
        if winner.params["x"] is None:
            return

        msg = CalibrationModel()
        # Initialize 6-slot coefficients with zeros
        cx = [0.0] * 6
        cy = [0.0] * 6
        px, py = winner.params["x"], winner.params["y"]

        W, H = 800.0, 600.0

        if winner.name == "Bias":
            msg.model_type = CalibrationModel.TYPE_BIAS
            cx[5], cy[5] = float(px[0]), float(py[0])

        elif winner.name == "Linear":
            msg.model_type = CalibrationModel.TYPE_LINEAR
            # Recipe: [dx/W, dy/H, 1]
            cx[3], cx[4], cx[5] = px[0] / W, px[1] / H, px[2]
            cy[3], cy[4], cy[5] = py[0] / W, py[1] / H, py[2]

        elif winner.name == "Radial":
            msg.model_type = CalibrationModel.TYPE_CONICAL  # Re-using type 3 for Radial
            # Recipe: [(dx*r2)/W^3, (dy*r2)/H^3, 1] (Example based on your radial_2)
            cx[0], cx[5] = px[0] / (W**3), px[2]
            cy[1], cy[5] = py[1] / (H**3), py[2]

        elif winner.name == "Conic":
            msg.model_type = CalibrationModel.TYPE_QUADRATIC
            # Recipe: [dx2/W2, dy2/H2, dxdy/WH, dx/W, dy/H, 1]
            cx = [
                px[0] / (W**2),
                px[1] / (H**2),
                px[2] / (W * H),
                px[3] / W,
                px[4] / H,
                px[5],
            ]
            cy = [
                py[0] / (W**2),
                py[1] / (H**2),
                py[2] / (W * H),
                py[3] / W,
                py[4] / H,
                py[5],
            ]

        elif winner.name == "Sigmoid":
            msg.model_type = 4  # TYPE_KNN_GRID slots
            # Recipe: [tanh(dx/400), tanh(dy/300), 1]
            cx[3], cx[5] = px[0], px[2]
            cy[4], cy[5] = py[1], py[2]

        msg.coeffs_x = [float(c) for c in cx]
        msg.coeffs_y = [float(c) for c in cy]
        self.model_pub.publish(msg)

    def publish_visuals(self, gx, gy, ex, ey):
        winner = self.competitors[self.active_idx]
        raw = self.competitors[0]

        # Use Agg backend for speed & thread safety
        fig = plt.figure(figsize=(12, 5))
        gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1])

        # Subplot 1: Tournament Curve
        ax_t = fig.add_subplot(gs[0])
        ev_r = np.arange(len(winner.prequential_errors))
        ax_t.plot(
            np.cumsum(raw.prequential_errors) / (ev_r + 1), "r--", label="Raw Hardware"
        )
        ax_t.plot(
            np.cumsum(winner.prequential_errors) / (ev_r + 1),
            "b-",
            lw=2,
            label=f"Active: {winner.name}",
        )
        ax_t.set_title("AULC Progress")
        ax_t.legend()

        # Subplot 2: Spatial Field
        ax_f = fig.add_subplot(gs[1])
        gw, gh = self.cfg["screen_w"], self.cfg["screen_h"]
        gx_g, gy_g = np.meshgrid(np.linspace(0, gw, 15), np.linspace(0, gh, 12))
        px, py = winner.predict(gx_g.ravel(), gy_g.ravel())
        ax_f.quiver(
            gx_g,
            gy_g,
            px.reshape(gx_g.shape),
            py.reshape(gy_g.shape),
            color="green",
            scale=1,
            scale_units="xy",
        )
        ax_f.set_xlim(0, gw)
        ax_f.set_ylim(gh, 0)
        ax_f.set_title("Current Field")

        # Convert and Publish
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        img = cv2.cvtColor(np.asarray(canvas.buffer_rgba()), cv2.COLOR_RGBA2BGR)
        self.image_pub.publish(self.bridge.cv2_to_imgmsg(img, "bgr8"))

        plt.clf()
        plt.close(fig)

    def publish_plots(self, cur_gx, cur_gy, cur_ex, cur_ey):
        # --- DRAW TOURNAMENT (Line Chart with Shading) ---
        self.fig_tourney.clear()
        ax = self.fig_tourney.add_subplot(111)

        active = self.models[self.active_model_name]
        raw = self.models["Raw"]

        ev_range = np.arange(len(active.prequential_errors))
        raw_aulc = np.cumsum(raw.prequential_errors) / (ev_range + 1)
        mod_aulc = np.cumsum(active.prequential_errors) / (ev_range + 1)

        ax.plot(raw_aulc, color="firebrick", ls="--", label="Raw Baseline")
        ax.plot(mod_aulc, color="navy", lw=2, label=f"Active: {self.active_model_name}")

        # Gain/Loss Shading
        ax.fill_between(
            ev_range,
            raw_aulc,
            mod_aulc,
            where=(mod_aulc <= raw_aulc),
            color="skyblue",
            alpha=0.3,
        )
        ax.fill_between(
            ev_range,
            raw_aulc,
            mod_aulc,
            where=(mod_aulc > raw_aulc),
            color="hotpink",
            alpha=0.3,
        )

        ax.set_title("Learning Progress (AULC)")
        ax.set_ylim(0, 150)
        ax.legend(loc="upper right")

        # Convert to ROS Image
        canvas = FigureCanvasAgg(self.fig_tourney)
        canvas.draw()
        img = cv2.cvtColor(np.asarray(canvas.buffer_rgba()), cv2.COLOR_RGBA2BGR)
        self.tourney_pub.publish(self.bridge.cv2_to_imgmsg(img, "bgr8"))

        # --- DRAW QUIVER (Spatial View) ---
        self.fig_main.clear()
        gs = gridspec.GridSpec(1, 2)
        ax_q = self.fig_main.add_subplot(gs[0])
        ax_f = self.fig_main.add_subplot(gs[1])

        # Quiver Panel (Current Reservoir + Current Segment)
        train_pool, val_pool = active.get_reservoir_split()
        if len(train_pool) > 0:
            ax_q.quiver(
                train_pool[:, 0],
                train_pool[:, 1],
                train_pool[:, 2],
                train_pool[:, 3],
                color="blue",
                alpha=0.3,
                scale=1,
                scale_units="xy",
            )
        ax_q.quiver(
            cur_gx,
            cur_gy,
            cur_ex,
            cur_ey,
            color="black",
            scale=1,
            scale_units="xy",
            label="Last Segment",
        )
        ax_q.set_xlim(0, 1600)
        ax_q.set_ylim(1200, 0)
        ax_q.set_title("Spatial Reservoir")

        # Field Panel
        gx_grid, gy_grid = np.meshgrid(
            np.linspace(0, 1600, 15), np.linspace(0, 1200, 10)
        )
        px, py = active.predict(gx_grid.ravel(), gy_grid.ravel())
        ax_f.quiver(
            gx_grid,
            gy_grid,
            px.reshape(gx_grid.shape),
            py.reshape(gy_grid.shape),
            color="green",
            scale=1,
            scale_units="xy",
        )
        ax_f.set_xlim(0, 1600)
        ax_f.set_ylim(1200, 0)
        ax_f.set_title(f"Field: {self.active_model_name}")

        canvas_main = FigureCanvasAgg(self.fig_main)
        canvas_main.draw()
        img_main = cv2.cvtColor(
            np.asarray(canvas_main.buffer_rgba()), cv2.COLOR_RGBA2BGR
        )
        self.image_pub.publish(self.bridge.cv2_to_imgmsg(img_main, "bgr8"))


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
