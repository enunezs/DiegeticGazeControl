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
import random
from collections import deque
import os
import csv

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

import os
import csv
from sensor_msgs.msg import Joy

# from rcl_py.time import Time

# from sklearn.neighbors import KNeighborsRegressor
# from sklearn.model_selection import ShuffleSplit


# ==========================================
# 1. SHARED RESOURCE: SPATIAL RESERVOIR
# ==========================================
class SpatialReservoir:
    def __init__(self, cfg):
        self.cfg = cfg
        self.bins = {}  # (bx, by) -> deque
        self.bin_size = cfg.get("bin_size", 150)
        self.max_samples = cfg.get("samples_per_bin", 50)
        self.val_size = cfg.get("val_size", 10)
        self.stride = cfg.get("thinning_stride", 15)
        self.val_ratio = cfg.get("val_size", 10) / self.max_samples

    def add_segment(self, gx, gy, ex, ey):
        """Processes a new segment into the shared spatial bins."""
        stride = self.stride
        gx_t, gy_t, ex_t, ey_t = gx[::stride], gy[::stride], ex[::stride], ey[::stride]

        for i in range(len(gx_t)):
            # Basic outlier rejection
            if abs(ex_t[i]) > 150 or abs(ey_t[i]) > 150:
                continue

            # Binning
            bid = (int(gx_t[i] // self.bin_size), int(gy_t[i] // self.bin_size))
            if bid not in self.bins:
                self.bins[bid] = deque(maxlen=self.max_samples)

            self.bins[bid].append((gx_t[i], gy_t[i], ex_t[i], ey_t[i]))

    def get_split(self):
        """Routes to the requested CV strategy."""
        strategy = self.cfg.get("cv_strategy", "stratified")

        if strategy == "spatial_block":
            return self._get_spatial_block_split()
        elif strategy == "kfolds_spatial_block":
            return self._get_spatial_kfolds_iterator()
        else:
            return self._get_stratified_split()

    def _get_stratified_split(self):
        """Standard FIFO split: newest samples in bin are validation."""
        train_list, val_list = [], []

        # Every Nth sample goes to validation (e.g., if ratio is 0.2, every 5th)
        # Using a fixed step ensures consistent distribution
        # val_step = int(1.0 / self.val_ratio) if self.val_ratio > 0 else 100
        val_step = max(2, int(self.max_samples / self.val_size))

        for samples in self.bins.values():
            s_list = list(samples)
            for i, sample in enumerate(s_list):
                # Interleave: every val_step-th sample goes to validation
                if i % val_step == 0:
                    val_list.append(sample)
                else:
                    train_list.append(sample)

        # Fallback: if data is extremely sparse and val_list is empty,
        # swap one from train to val so solvers don't crash.
        if len(train_list) > 0 and len(val_list) == 0:
            val_list.append(train_list.pop())

        return np.array(train_list), np.array(val_list)

    def _get_spatial_block_split(self):
        """Selects entire bins for validation and buffers neighbors."""
        all_bin_ids = list(self.bins.keys())
        if len(all_bin_ids) < 5:
            return self._get_stratified_split()

        val_ratio = self.cfg.get("spatial_val_ratio", 0.2)
        n_val_bins = max(1, int(len(all_bin_ids) * val_ratio))
        test_bin_ids = set(random.sample(all_bin_ids, n_val_bins))

        buffer_bin_ids = set()
        include_diagonals = self.cfg.get("cv_include_diagonals", False)

        for bx, by in test_bin_ids:
            neighbors = [(bx + 1, by), (bx - 1, by), (bx, by + 1), (bx, by - 1)]
            if include_diagonals:
                neighbors += [
                    (bx + 1, by + 1),
                    (bx - 1, by - 1),
                    (bx + 1, by - 1),
                    (bx - 1, by + 1),
                ]
            for nb in neighbors:
                if nb in self.bins and nb not in test_bin_ids:
                    buffer_bin_ids.add(nb)

        train_list, val_list = [], []
        for bid, samples in self.bins.items():
            if bid in test_bin_ids:
                val_list.extend(list(samples))
            elif bid in buffer_bin_ids:
                continue
            else:
                train_list.extend(list(samples))

        if not train_list:
            return self._get_stratified_split()
        return np.array(train_list), np.array(val_list)

    def _get_spatial_kfolds_iterator(self):
        """Systematic spatial interleaving for K-Folds."""
        all_bin_ids = list(self.bins.keys())
        n_folds = self.cfg.get("n_folds", 5)
        include_diagonals = self.cfg.get("cv_include_diagonals", False)

        if len(all_bin_ids) < n_folds * 2:
            return [self._get_stratified_split()]

        folds_map = {i: [] for i in range(n_folds)}
        for bx, by in all_bin_ids:
            fold_idx = (bx + by) % n_folds
            folds_map[fold_idx].append((bx, by))

        kfolds_data = []
        for k in range(n_folds):
            test_bin_ids = set(folds_map[k])
            buffer_bin_ids = set()
            for bx, by in test_bin_ids:
                neighbors = [(bx + 1, by), (bx - 1, by), (bx, by + 1), (bx, by - 1)]
                if include_diagonals:
                    neighbors += [
                        (bx + 1, by + 1),
                        (bx - 1, by - 1),
                        (bx + 1, by - 1),
                        (bx - 1, by + 1),
                    ]
                for nb in neighbors:
                    if nb in self.bins and nb not in test_bin_ids:
                        buffer_bin_ids.add(nb)

            train_l, val_l = [], []
            for bid, samples in self.bins.items():
                if bid in test_bin_ids:
                    val_l.extend(list(samples))
                elif bid in buffer_bin_ids:
                    continue
                else:
                    train_l.extend(list(samples))

            if train_l and val_l:
                kfolds_data.append((np.array(train_l), np.array(val_l)))
        return kfolds_data

    def __len__(self):
        return len(self.bins)

    # def get_train_val_split(self):
    #     """Returns a flattened numpy array of training and validation samples."""
    #     train_list, val_list = [], []
    #     for samples in self.bins.values():
    #         s_list = list(samples)
    #         if len(s_list) > self.val_size:
    #             # FIFO: Use older data for training, keep newest for "Exam" (Validation)
    #             val_list.extend(s_list[-self.val_size :])  # Newest for BIC/Val
    #             train_list.extend(s_list[: -self.val_size])  # Older for Training
    #         else:
    #             val_list.extend(s_list)

    #     return np.array(train_list), np.array(val_list)


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

        # Tracking for BIC/Tournament
        self.bic_history = []
        self.aic_history = []

        self.macro_rmse_history = []

        # Screen Constants
        self.feature_library = {
            "identity": lambda dx, dy, r, r2: [],
            "bias": lambda dx, dy, r, r2: [np.ones_like(dx)],
            "lin_x": lambda dx, dy, r, r2: [dx / self.cx],
            "lin_y": lambda dx, dy, r, r2: [dy / self.cy],
            # "quad_x": lambda dx, dy, r, r2: [(dx**2 * np.sign(dx)) / self.cx**2], # TODO: Sign flipping problem!
            # "quad_y": lambda dx, dy, r, r2: [(dy**2 * np.sign(dy)) / self.cy**2],
            # Radial Linear: Correction scales with distance (Expansion/Contraction)
            # This creates a "stretching" or "shrinking" effect towards/away from center
            "radial_concentric": lambda dx, dy, r, r2: [dx / self.cx, dy / self.cy],
            "radial": lambda dx, dy, r, r2: [
                (dx * r) / self.cx**2,
                (dy * r) / self.cy**2,
            ],
            "radial_quad": lambda dx, dy, r, r2: [
                (dx * r2) / self.cx**3,
                (dy * r2) / self.cy**3,
            ],
            "radial_universal": lambda dx, dy, r, r2: [
                (dx * r) / self.cx**2,  # px[0] -> Maps to cx[8]
                (dy * r) / self.cy**2,  # px[1] -> Maps to cy[8]
                dx / self.cx,  # px[2] -> Maps to cx[3]
                dy / self.cy,  # px[3] -> Maps to cy[4]
                np.ones_like(dx),  # px[4] -> Maps to bias cx[5]
            ],
            # "radial_unit": lambda dx, dy, r, r2: [dx / (r + 1e-6), dy / (r + 1e-6)],
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

        s_type = self.cfg.get("solver", "ridge")
        alpha = self.cfg.get("solver_alpha", 1.0)
        A_temp = self._get_matrix(np.array([0]), np.array([0]), self.current_features)
        n_cols = A_temp.shape[1]

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
        if self.name == "Radial Concentric":

            if len(self.params["x"]) == 1:
                return np.full_like(gx, self.params["x"][0]), np.full_like(
                    gy, self.params["y"][0]
                )

            # Force decoupling: X correction uses dx, Y correction uses dy
            # params[0] is bias, params[1] is the radial component
            px = self.params["x"][0] + self.params["x"][1] * (dx / self.cx)
            py = self.params["y"][0] + self.params["y"][1] * (dy / self.cy)
            return px, py

        A = self._get_matrix(dx, dy, self.current_features)
        return A @ self.params["x"], A @ self.params["y"]

    def train(self, split_data, n_bins, event_idx):
        if self.is_identity:
            return

        # Step 1: Handle model graduation as per number of samples
        if self.current_features == ["bias"] and n_bins >= self.cfg.get(
            "trigger_bins", 15
        ):
            self.current_features = self.master_recipe
            self.unlock_moments["activation"] = event_idx
            self.models = {"x": None, "y": None}  # Reset solvers for shape change

        # Step 2: Solver Fit
        # Handle K-Folds vs Single Split

        # Handle K-Folds vs Single Split
        if isinstance(split_data, list):
            fold_mses, all_params_x, all_params_y = [], [], []
            for train_samples, val_samples in split_data:
                if len(train_samples) < 3:
                    continue

                t_dx, t_dy = (
                    train_samples[:, 0] - self.cx,
                    train_samples[:, 1] - self.cy,
                )
                A_train = self._get_matrix(t_dx, t_dy, self.current_features)
                mx, my = self._get_solver("x"), self._get_solver("y")
                mx.fit(A_train, train_samples[:, 2])
                my.fit(A_train, train_samples[:, 3])

                v_dx, v_dy = val_samples[:, 0] - self.cx, val_samples[:, 1] - self.cy
                A_val = self._get_matrix(v_dx, v_dy, self.current_features)
                pvx, pvy = A_val @ mx.coef_, A_val @ my.coef_
                fold_mses.append(
                    np.mean(
                        (val_samples[:, 2] - pvx) ** 2 + (val_samples[:, 3] - pvy) ** 2
                    )
                )
                all_params_x.append(mx.coef_)
                all_params_y.append(my.coef_)

            if fold_mses:
                self.params["x"] = np.mean(all_params_x, axis=0)
                self.params["y"] = np.mean(all_params_y, axis=0)
                self._last_cv_mse = np.mean(fold_mses)

            # Optional: Production retrain on all data
            if self.cfg.get("retrain_on_full_data", True):
                full_data = np.concatenate([ts for ts, _ in split_data], axis=0)
                self._simple_fit(full_data)
        else:
            train_samples, _ = split_data
            self._simple_fit(train_samples)

    def _simple_fit(self, data):
        if len(data) < 3:
            return

        train_gx, train_gy, train_ex, train_ey = (
            data[:, 0],
            data[:, 1],
            data[:, 2],
            data[:, 3],
        )
        train_dx, train_dy = train_gx - self.cx, train_gy - self.cy

        if self.name == "Radial Concentric" and self.current_features != ["bias"]:
            # Solve X and Y using ONLY their respective radial components
            Ax = np.column_stack([np.ones_like(train_dx), train_dx / self.cx])
            Ay = np.column_stack([np.ones_like(train_dy), train_dy / self.cy])

            mx, my = self._get_solver("x"), self._get_solver("y")
            self.models["x"] = mx.fit(Ax, train_ex)
            self.models["y"] = my.fit(Ay, train_ey)
            self.params["x"], self.params["y"] = (
                self.models["x"].coef_,
                self.models["y"].coef_,
            )
        else:

            A = self._get_matrix(train_dx, train_dy, self.current_features)
            mx, my = self._get_solver("x"), self._get_solver("y")
            # Fit models
            self.models["x"], self.models["y"] = mx.fit(A, train_ex), my.fit(
                A, train_ey
            )
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
                # Plotting Toggles
                ("publish_data_quiver", True),
                ("publish_status_profile", True),
                ("publish_prediction_map", True),
                ("publish_tournament", True),
                # Selection and switching logic
                ("selection_strategy", "RMSE"),  # "BIC" or "RMSE"
                (
                    "cv_strategy",
                    "kfolds_spatial_block",
                ),  # "stratified", "spatial_block", "kfolds_spatial_block"
                ("n_folds", 5),
                ("spatial_val_ratio", 0.2),
                ("cv_include_diagonals", True),
                ("retrain_on_full_data", False),
                # Regressor settings
                ("solver", "ridge"),  # "huber", "ridge", "linear"
                ("solver_alpha", 1.0),  # TODO: Regularization strength for Ridge
                # ("trigger_bins", 10),
                ("bic_hysteresis", 3.0),  # Threshold to switch models
                ("rmse_hysteresis", 2.0),
                ("joy_button_index", 10),  # For recording, default to 'A' or 'X' button
                ("error_log_filename", "gaze_error_log.csv"),
            ],
        )

        # 2. Configuration
        self.cfg = {
            "center_x": 800,
            "center_y": 600,
            "screen_w": 1600,
            "screen_h": 1200,
            "bin_size": 150,
            "samples_per_bin": 50,
            "val_size": 10,
            "thinning_stride": 5,
            # "trigger_bins": self.get_parameter("trigger_bins").value, # TODO: Formalize or remove later
            "solver": self.get_parameter("solver").value,
            "solver_alpha": self.get_parameter("solver_alpha").value,
            "cv_strategy": self.get_parameter("cv_strategy").value,
            "n_folds": self.get_parameter("n_folds").value,
            "spatial_val_ratio": self.get_parameter("spatial_val_ratio").value,
            "cv_include_diagonals": self.get_parameter("cv_include_diagonals").value,
            "retrain_on_full_data": self.get_parameter("retrain_on_full_data").value,
        }

        # 3. State
        self.reservoir = SpatialReservoir(self.cfg)
        self.competitors = [
            GazeCorrectionFramework(
                "Raw", ["identity"], self.cfg | {"trigger_bins": 0}
            ),
            GazeCorrectionFramework("Bias", ["bias"], self.cfg | {"trigger_bins": 0}),
            GazeCorrectionFramework(
                "Linear", ["bias", "lin_x", "lin_y"], self.cfg | {"trigger_bins": 0}
            ),
            GazeCorrectionFramework(
                "Radial Concentric",
                ["bias", "radial_concentric"],
                self.cfg | {"trigger_bins": 5},
            ),
            # GazeCorrectionFramework(
            #     "Simple Radial", ["bias", "radial"], self.cfg | {"trigger_bins": 5}
            # ),
            GazeCorrectionFramework(
                "Radial Complete",
                ["bias", "radial_universal"],
                self.cfg | {"trigger_bins": 20},
            ),
            GazeCorrectionFramework(
                "Conic", ["bias", "full_conic"], self.cfg | {"trigger_bins": 40}
            ),
            # GazeCorrectionFramework(
            #     "Sigmoid X+Y", ["bias", "sigmoid"], self.cfg | {"trigger_bins": 15}
            # ),
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

        # 5. Prepare error log
        self.joy_btn_idx = self.get_parameter("joy_button_index").value
        self.log_path = self.get_parameter("error_log_filename").value
        self.last_button_state = 0  # For debouncing (rising edge detection)
        self.create_subscription(Joy, "joy", self.joy_callback, 10)

        # Prepare CSV File
        self._init_error_log()
        self.get_logger().info(
            f"Tournament Initialized. CV Strategy: {self.cfg['cv_strategy']}"
        )
        self.get_logger().info(
            f"Model Selection Strategy: {self.get_parameter('selection_strategy').value}"
        )
        self.get_logger().info(
            f"Solvers: {self.cfg['solver']} with alpha={self.cfg['solver_alpha']}"
        )
        self.get_logger().info(
            f"Hysteresis Thresholds - BIC: {self.get_parameter('bic_hysteresis').value}, RMSE: {self.get_parameter('rmse_hysteresis').value}"
        )
        self.get_logger().info("--- Competitors: ---")
        for m in self.competitors:
            self.get_logger().info(
                f" - {m.name} (Features: {m.master_recipe}, Trigger Bins: {m.cfg['trigger_bins']})"
            )
        self.get_logger().info(
            f"Spatial Reservoir Config: Bin Size={self.cfg['bin_size']}, Max Samples/Bin={self.cfg['samples_per_bin']}, Validation Size/Bin={self.cfg['val_size']}, Thinning Stride={self.cfg['thinning_stride']}"
        )
        self.get_logger().info(f"--- Error Logging ---")
        self.get_logger().info(
            f"Joy Button Index for Error Logging: {self.joy_btn_idx}"
        )
        self.get_logger().info(f"Error Log Path: {self.log_path}")

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
        # ex, ey = gx - tx, gy - ty
        ex, ey = tx - gx, ty - gy  # Target - Gaze

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

            # # TODO: not here. Should be based on cv scores within the training phase, not the prequential error of the single segment. This is too noisy and reactive.
            # # Winner Selection (AULC)
            # if i > 0:
            #     aulc = np.mean(model.prequential_errors)
            #     if aulc < best_aulc:
            #         best_aulc = aulc
            #         self.active_idx = i

        ### Phase 2: Update Shared Reservoir ###
        self.reservoir.add_segment(gx, gy, ex, ey)
        split_data = self.reservoir.get_split()

        # train_pool, val_pool

        # Phase 3: Shared Training ###
        for model in self.competitors:
            model.train(split_data, len(self.reservoir), self.event_count)

        self.event_count += 1

        # Phase 4: Model selection
        self.run_selection_tournament()

        # Publish model update and visuals
        self.publish_model_update()
        train_flat, val_flat = self.reservoir._get_stratified_split()
        self.generate_visuals(train_flat, val_flat)

    def run_selection_tournament(self):
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
            # AIC = 2 * k - 2 * ln(Likelihood), where Likelihood ~ exp(-N_bins * MSE_macro)
            aic = 2 * model.k_total + n_bins * np.log(macro_mse + 1e-6)

            # bic = k_total * np.log(n_bins) + n_bins * np.log(macro_mse + 1e-6)
            model.bic_history.append(bic)
            model.aic_history.append(aic)
            scores.append(
                bic if strategy == "BIC" else aic if strategy == "AIC" else macro_rmse
            )
            # Pending to add AIC

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
        # Initialize 9-slot coefficients with zeros [x2, y2, xy, x, y, bias, sigmoid_amp, sigmoid_scale, radial_coeff]
        cx, cy = [0.0] * 9, [0.0] * 9

        px, py = winner.params["x"], winner.params["y"]

        W, H = 800.0, 600.0  # Normalization constants used in training

        if winner.name == "Bias":
            msg.model_type = CalibrationModel.TYPE_BIAS
            cx[5], cy[5] = float(px[0]), float(py[0])

        elif winner.name == "Linear":
            msg.model_type = CalibrationModel.TYPE_LINEAR
            # Recipe: ["bias", "lin_x", "lin_y"] -> [1, dx/W, dy/H]
            cx[5], cx[3], cx[4] = px[0], px[1] / W, px[2] / H
            cy[5], cy[3], cy[4] = py[0], py[1] / W, py[2] / H

        elif winner.name == "Radial Concentric":
            msg.model_type = CalibrationModel.TYPE_LINEAR
            # Special case: Decoupled solves

            if len(winner.params["x"]) > 1:
                # Recipe: Decoupled ["bias", "radial_concentric"]
                cx[3], cx[5] = float(px[1] / W), float(px[0])
                cy[4], cy[5] = float(py[1] / H), float(py[0])
            else:
                cx[5], cy[5] = float(px[0]), float(py[0])

        elif winner.name == "Radial Complete":
            msg.model_type = CalibrationModel.TYPE_RADIAL_UNIVERSAL
            # Recipe: ["bias", "radial_universal"]
            # We map the primary radial term (dx*r) to index 8
            # and the linear/bias terms to 3, 4, 5

            # [dx*r2/W3, dy*r2/H3, dx/W, dy/H, bias]
            cx[8], cx[3], cx[5] = px[0] / (W**2), px[2] / W, px[4]
            cy[8], cy[4], cy[5] = py[1] / (H**2), py[3] / H, py[4]

        elif winner.name == "Conic":
            msg.model_type = CalibrationModel.TYPE_QUADRATIC
            # Recipe: ["bias", "full_conic"]
            # Full conic order: [dx2/W2, dy2/H2, dxdy/WH, dx/W, dy/H, bias]
            cx[0], cx[1], cx[2], cx[3], cx[4], cx[5] = (
                px[0] / (W**2),
                px[1] / (H**2),
                px[2] / (W * H),
                px[3] / W,
                px[4] / H,
                px[5],
            )
            cy[0], cy[1], cy[2], cy[3], cy[4], cy[5] = (
                py[0] / (W**2),
                py[1] / (H**2),
                py[2] / (W * H),
                py[3] / W,
                py[4] / H,
                py[5],
            )

        elif winner.name == "Sigmoid X+Y":
            msg.model_type = CalibrationModel.TYPE_SIGMOIDAL
            # Recipe: [tanh(dx/400), tanh(dy/300), bias]
            cx[6] = float(px[0])  # Amplitude
            cx[7] = W / 2  # Fixed Scale from the recipe
            cx[5] = float(px[2])  # Bias

            cy[6] = float(py[1])  # Amplitude
            cy[7] = H / 2  # Fixed Scale from the recipe
            cy[5] = float(py[2])  # Bias

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

        # --- ADD BIN MARKS (GRID) ---
        bin_size = self.cfg["bin_size"]
        # Set ticks at every bin interval
        ax.set_xticks(np.arange(0, self.cfg["screen_w"] + bin_size, bin_size))
        ax.set_yticks(np.arange(0, self.cfg["screen_h"] + bin_size, bin_size))
        # Style the grid to look like "marks"
        ax.grid(True, which="both", color="gray", linestyle="--", alpha=0.4)
        # Optional: hide tick labels if it gets too crowded
        ax.tick_params(axis="both", which="major", labelsize=8)

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
                width=0.0015,
            )
        ax.set_title(
            f"Reservoir ({len(self.reservoir.bins)} Bins) - {self.cfg['cv_strategy']} Pointing from gaze to target"
        )
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

    def _init_error_log(self):
        """Creates the CSV file and writes headers if it doesn't exist."""
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", newline="") as f:
                writer = csv.writer(f)
                header = [
                    "timestamp_ros",
                    "event_count",
                    "active_model",
                    "num_bins",
                    "total_samples",
                ]
                # Add columns for every competitor's current score
                for m in self.competitors:
                    header.append(f"{m.name}_score")
                writer.writerow(header)

    def joy_callback(self, msg: Joy):
        """Listens for the 'calibration is wrong' button press."""
        current_state = msg.buttons[self.joy_btn_idx]

        # Detect Rising Edge (0 -> 1)
        if current_state == 1 and self.last_button_state == 0:
            self.get_logger().warn("USER REPORTED CALIBRATION FAILURE!")
            self.log_error_event()

        self.last_button_state = current_state

    def log_error_event(self):
        """Saves the current internal state of the calibration to a CSV."""
        now = self.get_clock().now().to_msg()
        timestamp = f"{now.sec}.{now.nanosec}"

        active_model = self.competitors[self.active_idx]
        strategy = self.get_parameter("selection_strategy").value

        # Gather data
        row = [
            timestamp,
            self.event_count,
            active_model.name,
            len(self.reservoir.bins),
            sum(len(b) for b in self.reservoir.bins.values()),
        ]

        # Append scores for all models to see if the 'correct' model was close
        for m in self.competitors:
            score = 0.0
            if strategy == "BIC":
                score = m.bic_history[-1] if m.bic_history else 0.0
            elif strategy == "AIC":
                score = m.aic_history[-1] if m.aic_history else 0.0
            else:
                score = m.macro_rmse_history[-1] if m.macro_rmse_history else 0.0
            row.append(score)

        # Write to file
        with open(self.log_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        self.get_logger().info(f"Event logged to {self.log_path}")


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
