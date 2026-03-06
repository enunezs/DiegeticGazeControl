#!/usr/bin/env python3

# ROS2 Imports
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from gaze_interaction_manager.msg import InteractionSegment, CalibrationModel

# Other Imports
import numpy as np
import cv2
from cv_bridge import CvBridge
from collections import deque

# Matplotlib for Visualization
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.gridspec as gridspec

# import matplotlib.cm as cm

# Machine Learning Imports
from sklearn.linear_model import (
    HuberRegressor,
    Ridge,
    RANSACRegressor,
    LinearRegression,
)

# from sklearn.neighbors import KNeighborsRegressor
# from sklearn.model_selection import ShuffleSplit


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
        self.stride = cfg.get("thinning_stride", 25)

    def add_segment(self, gx, gy, ex, ey):
        """Processes a new segment into the shared spatial bins."""
        stride = self.stride

        gx_t, gy_t, ex_t, ey_t = gx[::stride], gy[::stride], ex[::stride], ey[::stride]

        for i in range(len(gx_t)):
            # Basic outlier rejection
            if abs(ex_t[i]) > 200 or abs(ey_t[i]) > 200:
                continue

            # Binning
            bid = (int(gx_t[i] // self.bin_size), int(gy_t[i] // self.bin_size))
            if bid not in self.bins:
                self.bins[bid] = deque(maxlen=self.max_samples)

            self.bins[bid].append((gx_t[i], gy_t[i], ex_t[i], ey_t[i]))

    def get_train_val_split(self):
        """Returns a flattened numpy array of training and validation samples."""
        train_list, val_list = [], []
        for samples in self.bins.values():
            s_list = list(samples)
            if len(s_list) > self.val_size:
                # FIFO: Use older data for training, keep newest for "Exam" (Validation)
                val_list.extend(s_list[-self.val_size :])  # Newest for BIC/Val
                train_list.extend(s_list[: -self.val_size])  # Older for Training
            else:
                val_list.extend(s_list)

        return np.array(train_list), np.array(val_list)

    def __len__(self):
        return len(self.bins)


# ==========================================
# 2. THE MATHEMATICAL MODELS
# ==========================================
class GazeCorrectionFramework:
    """
    Unified Gaze Compensation Engine - Validated Logic
    Used as a competitor within the Tournament.
    """

    def __init__(self, name, recipe, config):
        self.name = name
        self.cfg = config
        self.cx, self.cy = self.cfg.get("center_x", 800), self.cfg.get("center_y", 600)
        # Internal State (Models and Coefficients)
        self.params = {"x": None, "y": None}
        self.models = {"x": None, "y": None}

        self.prequential_errors = []
        self.unlock_moments = {}
        # self.raw_prequential_errors = []  # Hardware error (px)

        # Recipe Definition
        self.master_recipe = recipe
        self.is_identity = "identity" in self.master_recipe
        self.current_features = self.master_recipe if self.is_identity else ["bias"]
        # Start simple (Bias) unless it's the raw/identity model

        # Tracking for BIC/Tournament
        self.bic_history = []
        self.macro_rmse_history = []

        # Screen Constants
        self.feature_library = {
            "identity": lambda dx, dy, r, r2: [],
            "bias": lambda dx, dy, r, r2: [np.ones_like(dx)],
            "lin_x": lambda dx, dy, r, r2: [dx / self.cx],
            "lin_y": lambda dx, dy, r, r2: [dy / self.cy],
            "quad_x": lambda dx, dy, r, r2: [(dx**2 * np.sign(dx)) / self.cx**2],
            "quad_y": lambda dx, dy, r, r2: [(dy**2 * np.sign(dy)) / self.cy**2],
            "radial_2": lambda dx, dy, r, r2: [
                (dx * r2) / self.cx**3,
                (dy * r2) / self.cy**3,
            ],
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
        }

        # Calculate k (Number of features per axis)
        self.k = 0 if self.is_identity else self._get_k_count()

        if self.is_identity:
            self.k_total = 0
        else:
            A_temp = self._get_matrix(np.array([0]), np.array([0]), self.master_recipe)
            self.k_total = A_temp.shape[1] * 2

    def _get_k_count(self):
        # Temp build matrix to count columns
        A = self._get_matrix(np.array([0]), np.array([0]), self.master_recipe)
        return A.shape[1]

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
        if self.current_features == ["bias"] and n_bins >= self.cfg.get(
            "trigger_bins", 15
        ):
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

        # 1. Parameters
        self.declare_parameters(
            namespace="",
            parameters=[
                ("publish_data_quiver", True),
                ("publish_status_profile", True),
                ("publish_prediction_map", True),
                ("publish_tournament", True),
                ("selection_strategy", "RMSE"),  # "BIC" or "RMSE"
                ("trigger_bins", 12),
                ("solver", "huber"),
                ("bic_hysteresis", 15.0),  # Threshold to switch models
                ("rmse_hysteresis", 2.0),
            ],
        )

        # 2. Configuration
        self.cfg = {
            "center_x": 800,
            "center_y": 600,
            "screen_w": 1600,
            "screen_h": 1200,
            "bin_size": 100,
            "samples_per_bin": 20,
            "val_size": 3,
            "thinning_stride": 15,
            "trigger_bins": self.get_parameter("trigger_bins").value,
            "solver": self.get_parameter("solver").value,
        }

        # 3. State
        self.reservoir = SpatialReservoir(self.cfg)
        self.competitors = [
            GazeCorrectionFramework("Raw", ["identity"], self.cfg),
            GazeCorrectionFramework("Bias", ["bias"], self.cfg),
            # GazeCorrectionFramework("Radial", ["bias", "radial_2"], self.cfg),
            GazeCorrectionFramework("Conic", ["full_conic"], self.cfg),
            GazeCorrectionFramework("Sigmoid X+Y", ["sigmoid"], self.cfg),
        ]

        self.active_idx = 1
        self.event_count = 0
        self.bridge = CvBridge()
        self.start_time = None

        # 4. ROS Setup
        self.create_subscription(
            InteractionSegment, "calibration/interaction_segment", self.segment_cb, 10
        )
        self.model_pub = self.create_publisher(
            CalibrationModel, "calibration/model_update", 10
        )

        # Modular Publishers
        self.pubs = {
            "quiver": self.create_publisher(
                Image, "calibration/viz/data_reservoir", 10
            ),
            "profile": self.create_publisher(
                Image, "calibration/viz/adaptation_profile", 10
            ),
            "map": self.create_publisher(Image, "calibration/viz/prediction_map", 10),
            "tourney": self.create_publisher(Image, "calibration/viz/tournament", 10),
        }

        self.get_logger().info("Tournament Calibration Learner Initialized.")

        # --- Plotting ---
        # self.fig_main, self.ax_main = plt.subplots(figsize=(8, 6), dpi=100)
        # self.fig_tourney, self.ax_tourney = plt.subplots(figsize=(6, 4), dpi=100)
        # self.canvas_main = FigureCanvasAgg(self.fig_main)
        # self.canvas_tourney = FigureCanvasAgg(self.fig_tourney)

    def segment_cb(self, msg: InteractionSegment):
        # 0. Parse Segment
        if len(msg.gaze_samples) != len(msg.target_samples):
            self.get_logger().error("Mismatched sample counts in segment!")
            return

        # TODO: not append if sample error greater than 200

        gx = np.array([p.x for p in msg.gaze_samples])
        gy = np.array([p.y for p in msg.gaze_samples])
        tx = np.array([p.x for p in msg.target_samples])
        ty = np.array([p.y for p in msg.target_samples])
        # Error relative to target (Ground Truth)
        ex, ey = gx - tx, gy - ty

        ### Phase 1: Prequential Evaluation ###
        # Evaluate all models BEFORE they learn from this segment
        best_aulc = float("inf")
        for i, model in enumerate(self.competitors):
            if model.params["x"] is not None:
                px, py = model.predict(gx, gy)
                rmse = np.sqrt(np.mean((ex - px) ** 2 + (ey - py) ** 2))
            else:
                rmse = np.sqrt(np.mean(ex**2 + ey**2))

            model.prequential_errors.append(rmse)

            # TODO: not here. Should be based on cv scores within the training phase, not the prequential error of the single segment. This is too noisy and reactive.
            # Winner Selection (AULC)
            if i > 0:
                aulc = np.mean(model.prequential_errors)
                if aulc < best_aulc:
                    best_aulc = aulc
                    self.active_idx = i

        ### Phase 2: Update Shared Reservoir ###
        self.reservoir.add_segment(gx, gy, ex, ey)
        train_pool, val_pool = self.reservoir.get_train_val_split()

        # Phase 3: Shared Training ###
        for model in self.competitors:
            model.train(train_pool, len(self.reservoir), self.event_count)

        self.event_count += 1

        # Phase 4: Model selection
        self.run_bic_tournament()

        # Publish model update and visuals
        self.publish_model_update()
        self.generate_visuals(train_pool, val_pool)

    def run_bic_tournament(self):
        n_bins = len(self.reservoir.bins)
        if n_bins == 0:
            return

        strategy = self.get_parameter("selection_strategy").value
        scores = []

        for i, model in enumerate(self.competitors):
            # Calculate Macro-Average MSE across all bins
            bin_mses = []
            for samples in self.reservoir.bins.values():
                s = np.array(samples)
                px, py = model.predict(s[:, 0], s[:, 1])
                mse = np.mean((s[:, 2] - px) ** 2 + (s[:, 3] - py) ** 2)
                bin_mses.append(mse)

            macro_mse = np.mean(bin_mses)
            macro_rmse = np.sqrt(macro_mse)
            model.macro_rmse_history.append(macro_rmse)

            # BIC = ln(N_bins) * k + N_bins * ln(MSE_macro)
            k_total = model.k * 2
            bic = np.log(n_bins) * model.k_total + n_bins * np.log(macro_mse + 1e-6)

            # bic = k_total * np.log(n_bins) + n_bins * np.log(macro_mse + 1e-6)
            model.bic_history.append(bic)
            scores.append(bic if strategy == "BIC" else macro_rmse)

        # Hysteresis Logic
        challenger_idx = np.argmin(scores)
        hys_key = "bic_hysteresis" if strategy == "BIC" else "rmse_hysteresis"
        hysteresis = self.get_parameter(hys_key).value

        if scores[challenger_idx] < (scores[self.active_idx] - hysteresis):
            if self.active_idx != challenger_idx:
                self.get_logger().info(
                    f"SWITCH: {self.competitors[self.active_idx].name} -> {self.competitors[challenger_idx].name}"
                )
                self.active_idx = challenger_idx

    def publish_model_update(self):
        winner = self.competitors[self.active_idx]
        if winner.params["x"] is None:
            return

        msg = CalibrationModel()
        # Initialize 6-slot coefficients with zeros
        cx, cy = [0.0] * 6, [0.0] * 6
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
            # Recipe ["bias", "radial_2"]: index 0=bias, 1=radial_x, 2=radial_y
            cx[0], cx[5] = px[1] / (W**3), px[0]
            cy[1], cy[5] = py[2] / (H**3), py[0]

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

    # ==========================================
    # VISUALIZATION REFACTOR
    # ==========================================
    def generate_visuals(self, train_pool, val_pool):
        if self.get_parameter("publish_data_quiver").value:
            self._plot_reservoir(train_pool, val_pool)
        if self.get_parameter("publish_tournament").value:
            self._plot_tournament()
        if self.get_parameter("publish_status_profile").value:
            self._plot_profile()
        if self.get_parameter("publish_prediction_map").value:
            self._plot_prediction_field()

    def _plot_reservoir(self, train_pool, val_pool):
        fig, ax = plt.subplots(figsize=(6, 5))
        if len(train_pool) > 0:
            angles = np.arctan2(train_pool[:, 3], train_pool[:, 2])
            ax.quiver(
                train_pool[:, 0],
                train_pool[:, 1],
                train_pool[:, 2],
                train_pool[:, 3],
                color=plt.cm.hsv((angles + np.pi) / (2 * np.pi)),
                alpha=0.5,
                scale=1,
                scale_units="xy",
            )
        if len(val_pool) > 0:
            ax.quiver(
                val_pool[:, 0],
                val_pool[:, 1],
                val_pool[:, 2],
                val_pool[:, 3],
                color="black",
                scale=1,
                scale_units="xy",
                width=0.005,
            )
        ax.set_title(f"Reservoir ({len(self.reservoir.bins)} Bins)")
        ax.set_xlim(0, 1600)
        ax.set_ylim(1200, 0)
        self._pub_plt(fig, "quiver")

    def _plot_tournament(self):
        fig, ax = plt.subplots(figsize=(6, 4))
        strategy = self.get_parameter("selection_strategy").value
        for m in self.competitors:
            data = m.bic_history if strategy == "BIC" else m.macro_rmse_history
            if data:
                ax.plot(data, label=m.name)
        ax.set_title(f"Tournament Status ({strategy})")
        ax.legend(fontsize="x-small")
        ax.grid(alpha=0.2)
        self._pub_plt(fig, "tourney")

    def _plot_profile(self):
        fig, ax = plt.subplots(figsize=(6, 4))
        winner, raw = self.competitors[self.active_idx], self.competitors[0]
        if winner.macro_rmse_history:
            ax.plot(
                winner.macro_rmse_history,
                lw=2,
                color="blue",
                label=f"Active: {winner.name}",
            )
            ax.plot(raw.macro_rmse_history, "r--", label="Raw Hardware")
        ax.set_title("Global Macro RMSE Profile")
        ax.set_ylim(0, 150)
        ax.legend()
        ax.grid(alpha=0.2)
        self._pub_plt(fig, "profile")

    def _plot_prediction_field(self):
        winner = self.competitors[self.active_idx]
        fig, ax = plt.subplots(figsize=(6, 5))
        gw, gh = self.cfg["screen_w"], self.cfg["screen_h"]
        grid_x, grid_y = np.meshgrid(np.linspace(0, gw, 15), np.linspace(0, gh, 12))
        px, py = winner.predict(grid_x.ravel(), grid_y.ravel())
        mag = np.sqrt(px**2 + py**2)
        ax.quiver(
            grid_x,
            grid_y,
            px.reshape(grid_x.shape),
            py.reshape(grid_y.shape),
            mag.reshape(grid_x.shape),
            cmap="jet",
            scale=1,
            scale_units="xy",
        )
        ax.set_xlim(0, gw)
        ax.set_ylim(gh, 0)
        ax.set_title(f"Correction Field: {winner.name}")
        self._pub_plt(fig, "map")

    def _pub_plt(self, fig, key):
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        img = cv2.cvtColor(np.asarray(canvas.buffer_rgba()), cv2.COLOR_RGBA2BGR)
        self.pubs[key].publish(self.bridge.cv2_to_imgmsg(img, "bgr8"))
        plt.close(fig)


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
