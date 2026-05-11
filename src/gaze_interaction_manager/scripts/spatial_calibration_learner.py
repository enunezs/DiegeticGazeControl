#!/usr/bin/env python3

# ROS2 Imports
from datetime import datetime

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, Joy

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
        self.max_samples = cfg.get("samples_per_bin", 100)
        self.val_size = cfg.get("val_size", 10)
        self.stride = cfg.get("thinning_stride", 2)
        # ? self.val_ratio = cfg.get("val_size", 10) / self.max_samples
        self.val_ratio = (
            self.val_size / self.max_samples if self.max_samples > 0 else 0.2
        )

        # Tracking projection coverage for decoupled axis unlocking
        self.unique_bx = set()
        self.unique_by = set()

    def add_segment(self, gx, gy, ex, ey):
        """Processes a new segment into the shared spatial bins."""
        stride = self.stride
        gx_t, gy_t, ex_t, ey_t = gx[::stride], gy[::stride], ex[::stride], ey[::stride]
        max_error = self.cfg.get("max_error_cap", 150.0)

        # for i in range(len(gx_t)):
        #     # Basic outlier rejection
        #     if abs(ex_t[i]) > max_error or abs(ey_t[i]) > max_error:
        #         continue

        #     # Binning
        #     bx, by = int(gx_t[i] // self.bin_size), int(gy_t[i] // self.bin_size)
        #     bid = (bx, by)
        #     if bid not in self.bins:
        #         self.bins[bid] = deque(maxlen=self.max_samples)

        #     self.bins[bid].append((gx_t[i], gy_t[i], ex_t[i], ey_t[i]))
        #     # Update projection tracking
        #     self.unique_bx.add(bx)
        #     self.unique_by.add(by)

        # 1. Vectorized Outlier Rejection
        mask = (np.abs(ex_t) <= max_error) & (np.abs(ey_t) <= max_error)
        if not np.any(mask):
            return

        gx_f, gy_f, ex_f, ey_f = gx_t[mask], gy_t[mask], ex_t[mask], ey_t[mask]

        # 2. Vectorized Bin ID Calculation
        bxs = (gx_f // self.bin_size).astype(int)
        bys = (gy_f // self.bin_size).astype(int)

        # 3. Grouping into Deques
        # We still loop here, but only once per point in the segment, 
        # and the logic inside is stripped to the bare minimum.
        for i in range(len(gx_f)):
            bid = (bxs[i], bys[i])
            if bid not in self.bins:
                self.bins[bid] = deque(maxlen=self.max_samples)
            
            self.bins[bid].append((gx_f[i], gy_f[i], ex_f[i], ey_f[i]))
            self.unique_bx.add(bxs[i])
            self.unique_by.add(bys[i])

    @property
    def coverage(self):
        """Returns independent axis coverage and total 2D bin coverage."""
        return {
            "x": len(self.unique_bx),
            "y": len(self.unique_by),
            "2d": len(self.bins),
        }

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

        min_samples = self.cfg.get("min_samples_per_bin_threshold", 4)

        # Every Nth sample goes to validation (e.g., if ratio is 0.2, every 5th)
        # Using a fixed step ensures consistent distribution
        val_step = (
            max(2, int(self.max_samples / self.val_size)) if self.val_size > 0 else 100
        )

        for samples in self.bins.values():

            if len(samples) < min_samples:
                continue  # Ignore this bin for training/validation for now

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

        # 1. Get random sample of bins for testing
        val_ratio = self.cfg.get("spatial_val_ratio", 0.2)
        n_val_bins = max(1, int(len(all_bin_ids) * val_ratio))
        test_bin_ids = set(random.sample(all_bin_ids, n_val_bins))

        # 2. Mark buffer bins (not used in testing)
        buffer_bin_ids = set()
        include_diagonals = self.cfg.get("cv_include_diagonals", False)

        for bx, by in test_bin_ids:
            # Mark criteria
            neighbors = [(bx + 1, by), (bx - 1, by), (bx, by + 1), (bx, by - 1)]
            if include_diagonals:
                neighbors += [
                    (bx + 1, by + 1),
                    (bx - 1, by - 1),
                    (bx + 1, by - 1),
                    (bx - 1, by + 1),
                ]
            # Add bins to buffer
            for nb in neighbors:
                if nb in self.bins and nb not in test_bin_ids:
                    buffer_bin_ids.add(nb)

        # 3. Split samples based on bin membership.
        # Dont use buffer bins for anything
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

        # 1. If too few bins, fallback to single split to avoid empty folds
        if len(all_bin_ids) < n_folds * 2:
            return [self._get_stratified_split()]

        # 2. Assign bins to folds using checkerboard pattern: (bx + by) % n_folds
        folds_map = {i: [] for i in range(n_folds)}
        for bx, by in all_bin_ids:
            fold_idx = (bx + by) % n_folds
            folds_map[fold_idx].append((bx, by))

        # 3. For each fold, create train/val split with buffer zones around test bins
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
        self.aulc_history = []  # Cumulative Mean of Prequential Error
        self.macro_rmse_history = []

        # self.raw_prequential_errors = []  # Hardware error (px)

        ### ====== Recipe Definition ====== ###
        # Support for heterogeneous axis recipes:
        if isinstance(recipe, dict):
            # Can be a dict:     {'x': ['bias', 'radial'], 'y': ['bias', 'lin_y']}
            self.master_recipe_x = recipe["x"]
            self.master_recipe_y = recipe["y"]
        else:
            # Or a list: ['bias', 'lin_x', 'lin_y']
            self.master_recipe_x = list(recipe)
            self.master_recipe_y = list(recipe)

        self.master_recipe = recipe
        self.is_identity = "identity" in (
            self.master_recipe
            if isinstance(self.master_recipe, list)
            else self.master_recipe_x + self.master_recipe_y
        )

        # Independent axis feature tracking (replaces single current_features)
        self.current_features_x = self.master_recipe_x if self.is_identity else ["bias"]
        self.current_features_y = self.master_recipe_y if self.is_identity else ["bias"]
        # self.current_features = self.master_recipe if self.is_identity else ["bias"]

        # Feature categories used by decoupled unlocking logic
        self.feature_categories = {
            "x_only": ["lin_x", "quad_x", "cub_x", "sig_x"],
            "y_only": ["lin_y", "quad_y", "cub_y", "sig_y"],
            "interaction": [
                "cross_xy",
                "radial",
                "radial_quad",
                "radial_universal",
                "full_conic",
                "tangent_1",
                "tangent_2",
                "sigmoid",
            ],
        }

        # Tracking for BIC/Tournament
        self.bic_history = []
        self.aic_history = []

        # Screen Constants
        self.feature_library = {
            "identity": lambda dx, dy, r, r2: [],
            "bias": lambda dx, dy, r, r2: [np.ones_like(dx)],
            "lin_x": lambda dx, dy, r, r2: [dx / self.cx],
            "lin_y": lambda dx, dy, r, r2: [dy / self.cy],
            "quad_x": lambda dx, dy, r, r2: [(dx**2 * np.sign(dx)) / self.cx**2],
            "quad_y": lambda dx, dy, r, r2: [(dy**2 * np.sign(dy)) / self.cy**2],
            "cross_xy": lambda dx, dy, r, r2: [(dx * dy) / (self.cx * self.cy)],
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
            "sigmoid": lambda dx, dy, r, r2: [  # Correction = A x tanh(normalized_input) + bias
                np.tanh(dx / (self.cx / 2)),
                np.tanh(dy / (self.cy / 2)),
                np.ones_like(dx),
            ],
            "tangent_1": lambda dx, dy, r, r2: [
                (2 * dx * dy) / self.cx**2,
                (r2 + 2 * dx**2) / self.cx**2,
            ],
            "tangent_2": lambda dx, dy, r, r2: [
                (r2 + 2 * dy**2) / self.cy**2,
                (2 * dx * dy) / self.cy**2,
            ],
        }

        # Calculate k (Number of features per axis)
        # NOTE: k is the sum of both axis column counts, NOT doubled,
        # because master_recipe_x and master_recipe_y can differ.
        self.k = 0 if self.is_identity else self._get_k_count()

        # k_total kept for backward compatibility with tournament scoring
        self.k_total = self.k

    @property
    def current_features(self):
        """Compatibility property for plotting/logging that reads a single feature string."""
        if self.current_features_x == self.current_features_y:
            return self.current_features_x
        return f"X:{self.current_features_x} | Y:{self.current_features_y}"

    @current_features.setter
    def current_features(self, value):
        self.current_features_x = value
        self.current_features_y = value

    @property
    def aulc(self):
        """Area Under the Learning Curve: cumulative mean of prequential errors."""
        return np.mean(self.prequential_errors) if self.prequential_errors else 0.0

    def _get_k_count(self):
        # Total parameters = columns in X model + columns in Y model
        ax_temp = self._get_matrix(np.array([0]), np.array([0]), self.master_recipe_x)
        ay_temp = self._get_matrix(np.array([0]), np.array([0]), self.master_recipe_y)
        return ax_temp.shape[1] + ay_temp.shape[1]

    def _get_matrix(self, dx, dy, features):
        if not features or features == ["identity"]:
            return np.zeros((len(dx), 0))

        r2, r = dx**2 + dy**2, np.sqrt(dx**2 + dy**2)
        cols = []
        for f in features:
            if f in self.feature_library:
                cols.extend(self.feature_library[f](dx, dy, r, r2))
        return np.column_stack(cols)

    def _get_solver(self, axis, n_cols):
        """Solver factory. Handles shape changes for Huber warm_start."""
        if self.is_identity:
            return None

        s_type = self.cfg.get("solver", "ridge")
        alpha = self.cfg.get("solver_alpha", 1.0)
        m = self.models.get(axis)

        # A_temp = self._get_matrix(np.array([0]), np.array([0]), self.current_features)
        # n_cols = A_temp.shape[1]

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

        # Radial Concentric uses a special decoupled solve and cannot use the
        # general axis-split path — it is inherently a coupled radial model.
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

        # General path: predict using axis-specific active feature sets
        Ax = self._get_matrix(dx, dy, self.current_features_x)
        Ay = self._get_matrix(dx, dy, self.current_features_y)
        return Ax @ self.params["x"], Ay @ self.params["y"]

    def train(self, split_data, coverage_dict, event_idx):
        if self.is_identity:
            return

        # --- DECOUPLED UNLOCKING LOGIC ---
        policy = self.cfg.get("policy", "original_coupled")
        t_x = self.cfg.get("trigger_x", self.cfg.get("trigger_x", 5))
        t_y = self.cfg.get("trigger_y", self.cfg.get("trigger_y", 5))
        t2d = self.cfg.get("trigger_bins", 5)

        if policy == "original_coupled":
            # Traditional check: total 2D bin count unlocks both axes at once.
            # This preserves the original ROS2 behaviour exactly.
            if coverage_dict["2d"] >= t2d:
                if self.current_features_x == ["bias"]:  # Only act on first unlock
                    self.current_features_x = self.master_recipe_x
                    self.current_features_y = self.master_recipe_y
                    self.unlock_moments["activation"] = event_idx
                    self.models = {
                        "x": None,
                        "y": None,
                    }  # Reset solvers for shape change

        elif policy in ("decoupled_shared", "fully_decoupled"):
            # Asymmetric: X and Y unlock independently.
            # Note: Radial Concentric bypasses this path in predict() regardless,
            # but we still update current_features_x/y so the unlock log is honest.

            # Horizontal unlock
            if self.current_features_x == ["bias"] and coverage_dict["x"] >= t_x:
                x_features = [
                    f
                    for f in self.master_recipe_x
                    if f in self.feature_categories["x_only"] or f == "bias"
                ]
                # Guard: if recipe has no x_only terms (e.g. pure interaction),
                # skip the intermediate step and go straight to the full recipe.
                self.current_features_x = (
                    x_features if len(x_features) > 1 else self.master_recipe_x
                )
                self.unlock_moments["x_unlock"] = event_idx

            # Vertical unlock
            if self.current_features_y == ["bias"] and coverage_dict["y"] >= t_y:
                y_features = [
                    f
                    for f in self.master_recipe_y
                    if f in self.feature_categories["y_only"] or f == "bias"
                ]
                self.current_features_y = (
                    y_features if len(y_features) > 1 else self.master_recipe_y
                )
                self.unlock_moments["y_unlock"] = event_idx

            # Interaction rejoin (decoupled_shared only)
            # Once both axes are unlocked, promote both to the full recipe
            if policy == "decoupled_shared":
                both_unlocked = coverage_dict["x"] >= t_x and coverage_dict["y"] >= t_y
                if both_unlocked and self.current_features_x != self.master_recipe_x:
                    self.current_features_x = self.master_recipe_x
                    self.current_features_y = self.master_recipe_y
                    self.unlock_moments["interaction_unlock"] = event_idx

        # --- SOLVER FIT ---
        # Handle K-Folds vs Single Split
        if isinstance(split_data, list):
            all_params_x, all_params_y = [], []
            for train_samples, val_samples in split_data:
                if len(train_samples) < 5:
                    continue

                px, py = self._fit_step(train_samples)
                if px is not None:
                    all_params_x.append(px)
                    all_params_y.append(py)

            if all_params_x:
                self.params["x"] = np.mean(all_params_x, axis=0)
                self.params["y"] = np.mean(all_params_y, axis=0)

            # Production retrain: use the full reservoir (union of all folds)
            # NOTE: Flattening all fold train+val data rather than only fold[0]
            # to ensure we train on the complete dataset, not just one fold's worth.
            if self.cfg.get("retrain_on_full_data", True):
                all_data = np.vstack([np.vstack([ts, vs]) for ts, vs in split_data])
                px, py = self._fit_step(all_data)
                if px is not None:
                    self.params["x"], self.params["y"] = px, py
        else:
            train_samples, val_samples = split_data
            px, py = self._fit_step(train_samples)
            if px is not None:
                self.params["x"], self.params["y"] = px, py

            # Production retrain: include validation data in final fit
            if self.cfg.get("retrain_on_full_data", True):
                full_data = np.vstack([train_samples, val_samples])
                px, py = self._fit_step(full_data)
                if px is not None:
                    self.params["x"], self.params["y"] = px, py

    # def _simple_fit(self, data):
    def _fit_step(self, data):
        """Fits both axis models on the provided data slice. Returns (coef_x, coef_y)."""
        if len(data) < 3:
            return None, None

        dx, dy = data[:, 0] - self.cx, data[:, 1] - self.cy

        # Radial Concentric uses its own decoupled matrix construction
        if self.name == "Radial Concentric" and self.current_features_x != ["bias"]:
            # Solve X and Y using ONLY their respective radial components
            Ax = np.column_stack([np.ones_like(dx), dx / self.cx])
            Ay = np.column_stack([np.ones_like(dy), dy / self.cy])
        else:
            Ax = self._get_matrix(dx, dy, self.current_features_x)
            Ay = self._get_matrix(dx, dy, self.current_features_y)

        # Fit models separately for X and Y using their respective active feature sets
        mx = self._get_solver("x", Ax.shape[1]).fit(Ax, data[:, 2])
        my = self._get_solver("y", Ay.shape[1]).fit(Ay, data[:, 3])

        # Save coefficients
        self.models["x"], self.models["y"] = mx, my
        return mx.coef_, my.coef_


class CalibrationLearner(Node):
    def __init__(self):
        super().__init__("calibration_learner_reservoir")

        # 1. Parameters
        self.declare_parameters(
            namespace="",
            parameters=[
                # Plotting Toggles
                ("publish_data_quiver", True),
                ("publish_status_profile", False),
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
                ("retrain_on_full_data", True),
                # Regressor settings
                ("solver", "ridge"),  # "huber", "ridge", "linear"
                ("solver_alpha", 10.0),  # TODO: Regularization strength for Ridge
                ("bic_hysteresis", 3.0),  # Threshold to switch models
                ("rmse_hysteresis", 2.0),
                ("joy_userstop_button_index", 10),  # For recording, default to 'A' or 'X' button
                ("joy_resume_button_index", 0),  # Xbox 'A' button is typically index 0
                ("error_log_filename", "gaze_error_log.csv"),
                # Unlocking policy for feature graduation
                (
                    "policy",
                    "original_coupled",
                ),  # "original_coupled", "decoupled_shared", "fully_decoupled"
                ("trigger_x", 5),  # Bins along X axis before X-features unlock
                ("trigger_y", 5),  # Bins along Y axis before Y-features unlock
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
            "samples_per_bin": 100,
            "val_size": 10,
            "thinning_stride": 1,
            # "trigger_bins": self.get_parameter("trigger_bins").value, # TODO: Formalize or remove later
            "solver": self.get_parameter("solver").value,
            "solver_alpha": self.get_parameter("solver_alpha").value,
            "cv_strategy": self.get_parameter("cv_strategy").value,
            "n_folds": self.get_parameter("n_folds").value,
            "spatial_val_ratio": self.get_parameter("spatial_val_ratio").value,
            "cv_include_diagonals": self.get_parameter("cv_include_diagonals").value,
            "retrain_on_full_data": self.get_parameter("retrain_on_full_data").value,
            "policy": self.get_parameter("policy").value,
            # "trigger_x": self.get_parameter("trigger_x").value,
            # "trigger_y": self.get_parameter("trigger_y").value,
        }

        # 3. State
        self.reservoir = SpatialReservoir(self.cfg)
        self.competitors = [
            GazeCorrectionFramework(
                "Raw", ["identity"], self.cfg | {"trigger_bins": 0}
            ),
            GazeCorrectionFramework("Bias", ["bias"], self.cfg | {"trigger_bins": 1}),
            GazeCorrectionFramework(
                "Linear",
                ["bias", "lin_x", "lin_y"],
                self.cfg
                | {"trigger_x": 6, "trigger_y": 6, "policy": "decoupled_shared"},
            ),
            GazeCorrectionFramework(
                "Radial Concentric",
                ["bias", "radial_concentric"],

                self.cfg
                 | {"trigger_x": 3, "trigger_y": 3, "policy": "original_coupled"},
            ),
            GazeCorrectionFramework(
                "Simple Radial",
                ["bias", "radial"],
                self.cfg
                | {"trigger_x": 5, "trigger_y": 5, "policy": "decoupled_shared"},
            ),
            GazeCorrectionFramework(
                "Sigmoid X+Y",
                ["bias", "sigmoid"],
                self.cfg
                | {"trigger_x": 5, "trigger_y": 5, "policy": "decoupled_shared"},
            ),
            # GazeCorrectionFramework(
            #     "Raw 2", ["identity"], self.cfg | {"trigger_bins": 0}
            # ),
            GazeCorrectionFramework(
                "Radial Complete",
                ["bias", "radial_universal"],
                self.cfg
                | {"trigger_x": 8, "trigger_y": 8, "policy": "decoupled_shared"},
            ),
            # GazeCorrectionFramework(
            #     "Conic",
            #     ["bias", "full_conic"],
            #     self.cfg
            #     | {"trigger_x": 8, "trigger_y": 8, "policy": "decoupled_shared"},
            # ),
        ]

        self.active_idx = 1
        self.event_count = 0
        self.bridge = CvBridge()
        self.start_time = None

        # --- Evolution Tracking for plotting ---
        self.winner_idx_history = []
        self.system_prequential_errors = []

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

        # Extra. Filesystem Setup (New for Experiment)

        # 1. Session Folder Setup
        self.session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join(
            os.getcwd(), "user_recordings", f"session_{self.session_name}"
        )
        os.makedirs(self.log_dir, exist_ok=True)

        # 2. File Paths
        self.file_aulc = os.path.join(self.log_dir, "history_aulc.csv")
        self.file_preq = os.path.join(self.log_dir, "history_prequential.csv")
        self.file_rmse = os.path.join(self.log_dir, "history_rmse.csv")
        self.file_user = os.path.join(self.log_dir, "user_report_errors.csv")

        self._init_csv_headers()
        self.last_hardware_ts = "0.0"  # This will store the Pupil Clock time

        # 5. Prepare error log
        self.create_subscription(Joy, "joy", self.joy_cb, 10)

        self.joy_userstop_button_index = self.get_parameter("joy_userstop_button_index").value
        self.resume_btn_idx = self.get_parameter("joy_resume_button_index").value
        self.last_stop_button_state = 0  # For debouncing (rising edge detection)
        self.last_resume_button_state = 0
        
        self.log_path = self.get_parameter("error_log_filename").value

        # Prepare CSV File
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
            features = (
                m.cfg.get(
                    "trigger_bins",
                    m.cfg.get("trigger_x", m.cfg.get("trigger_y", "Unlocked")),
                )
                if m.is_identity
                else m.current_features
            )
            self.get_logger().info(
                f" - {m.name} (Features: {m.master_recipe}, Policy: {m.cfg.get('policy', 'Not Set')}, Trigger: {features})"
            )
        self.get_logger().info(
            f"Spatial Reservoir Config: Bin Size={self.cfg['bin_size']}, Max Samples/Bin={self.cfg['samples_per_bin']}, Validation Size/Bin={self.cfg['val_size']}, Thinning Stride={self.cfg['thinning_stride']}"
        )
        self.get_logger().info(f"--- Error Logging ---")
        self.get_logger().info(
            f"Joy Button Index for Error Logging: {self.joy_userstop_button_index}"
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

        # Save to CSVs
        now = self.get_clock().now().to_msg()
        system_ts = (
            f"{now.sec}.{now.nanosec:09d}"  # Ensure leading zeros for nanoseconds
        )
        last_sample = msg.gaze_samples[-1]
        self.last_hardware_ts = (
            f"{last_sample.header.stamp.sec}.{last_sample.header.stamp.nanosec:09d}"
        )

        gx = np.array([p.x for p in msg.gaze_samples])
        gy = np.array([p.y for p in msg.gaze_samples])
        tx = np.array([p.x for p in msg.target_samples])
        ty = np.array([p.y for p in msg.target_samples])
        # ts = np.array([p.timestamp_unix_seconds for p in msg.gaze_samples])

        # Error relative to target (Ground Truth)
        # ex, ey = gx - tx, gy - ty
        ex, ey = tx - gx, ty - gy  # Target - Gaze

        ### Phase 1: Prequential Evaluation ###
        # Evaluate all models BEFORE they learn from this segment
        preq_row = []
        aulc_row = []

        for i, model in enumerate(self.competitors):
            # if model.params["x"] is not None:
            px, py = model.predict(gx, gy)
            preq_rmse = np.sqrt(np.mean((ex - px) ** 2 + (ey - py) ** 2))
            # else:
            # rmse = np.sqrt(np.mean(ex**2 + ey**2))
            model.prequential_errors.append(preq_rmse)

            # AULC is the mean of errors seen SO FAR
            aulc = np.mean(model.prequential_errors)

            preq_row.append(preq_rmse)
            aulc_row.append(aulc)

        self.system_prequential_errors.append(self.competitors[self.active_idx].prequential_errors[-1])


        ### Phase 2: Update Shared Reservoir ###
        self.reservoir.add_segment(gx, gy, ex, ey)
        split_data = self.reservoir.get_split()
        coverage = self.reservoir.coverage

        # Phase 3: Shared Training ###
        rmse_row = []
        for model in self.competitors:
            if len(self.reservoir) == 0:
                return
            # model.train(split_data, len(self.reservoir), self.event_count)
            model.train(split_data, self.reservoir.coverage, self.event_count)

            # Update Macro-RMSE (error across all bins)
            bin_mses = []
            for samples in self.reservoir.bins.values():
                s = np.array(samples)
                px, py = model.predict(s[:, 0], s[:, 1])
                bin_mses.append(np.mean((s[:, 2] - px) ** 2 + (s[:, 3] - py) ** 2))

            macro_rmse = np.sqrt(np.mean(bin_mses))
            model.macro_rmse_history.append(macro_rmse)

            rmse_row.append(macro_rmse)

        # Phase 4: Model selection
        self.run_selection_tournament()

        meta = [
            system_ts,
            self.last_hardware_ts,
            self.event_count,
            self.reservoir.__len__(),
            msg.button_id,
            self.competitors[self.active_idx].name,
        ]
        self._append_to_csv(self.file_preq, meta + preq_row)
        self._append_to_csv(self.file_aulc, meta + aulc_row)
        self._append_to_csv(self.file_rmse, meta + rmse_row)

        self.event_count += 1

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
                # if model.params["x"] is None:
                #     px, py = np.zeros_like(px), np.zeros_like(py)
                mse = np.mean((s[:, 2] - px) ** 2 + (s[:, 3] - py) ** 2)
                bin_mses.append(mse)

            macro_mse = np.mean(bin_mses)
            macro_rmse = np.sqrt(macro_mse)

            # BIC = ln(N_bins) * k + N_bins * ln(MSE_macro)
            # k_total = model.k * 2
            bic = np.log(n_bins) * model.k_total + n_bins * np.log(macro_mse + 1e-6)
            # AIC = 2 * k - 2 * ln(Likelihood), where Likelihood ~ exp(-N_bins * MSE_macro)
            aic = 2 * model.k_total + n_bins * np.log(macro_mse + 1e-6)

            # bic = k_total * np.log(n_bins) + n_bins * np.log(macro_mse + 1e-6)
            model.bic_history.append(bic)
            model.aic_history.append(aic)
            scores.append(
                bic if strategy == "BIC" else aic if strategy == "AIC" else macro_rmse
            )

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
        self.winner_idx_history.append(self.active_idx)

    def reset_calibration(self):
        """Dumps current data, clears memory, and resets models for a fresh start."""
        self.get_logger().warn(
            "RESUME BUTTON PRESSED: Resetting calibration session..."
        )

        # 1. Dump current data with a unique label so it's not overwritten
        reset_label = f"reset_event_{self.event_count}"
        self.dump_reservoir(label=reset_label)

        # Clear tracking history
        self.winner_idx_history = []
        self.system_prequential_errors = []

        # 2. Clear the Reservoir
        self.reservoir = SpatialReservoir(self.cfg)

        # 3. Reset all competitors to their initial state
        for model in self.competitors:
            model.params = {"x": None, "y": None}
            model.models = {"x": None, "y": None}

            # UNCOMMENT THESE LINES TO FIX THE BUG:
            model.prequential_errors = []
            model.aulc_history =[]
            model.macro_rmse_history = []
            model.bic_history = []
            model.aic_history =[]
            model.unlock_moments = {}

            # This triggers the "Learning" phase again
            if not model.is_identity:
                model.current_features_x = ["bias"]
                model.current_features_y = ["bias"]
                
        # 4. Reset tournament state
        self.active_idx = 1  # Default back to 'Bias' model
        # Note: We keep self.event_count increasing to maintain a continuous timeline in logs
        self.log_reset_event()

        self.get_logger().info("Memory cleared. Models reset. Ready for new data.")
        self.publish_model_update()

    def log_reset_event(self):
        """Adds a special marker to the user report log to indicate a reset occurred."""
        now = self.get_clock().now().to_msg()
        system_ts = f"{now.sec}.{now.nanosec:09d}"

        row = [
            system_ts,
            self.last_hardware_ts,
            self.event_count,
            "ACTION_RESET_RESUME",  # Marker
            0,  # Bins are now 0
            0,  # Samples are now 0
            0.0,
        ]
        self._append_to_csv(self.file_user, row)

    def publish_model_update(self):
        winner = self.competitors[self.active_idx]

        msg = CalibrationModel()
        # Initialize 10-slot coefficients with zeros
        cx, cy = [0.0] * 10, [0.0] * 10

        px, py = winner.params["x"], winner.params["y"]
        W, H = 800.0, 600.0  # Normalization constants used in training

        # Guard against None (Not trained yet)
        if px is None or py is None:
            msg.model_type = getattr(CalibrationModel, 'TYPE_BIAS', 0)
            msg.coeffs_x =[float(c) for c in cx]
            msg.coeffs_y =[float(c) for c in cy]
            self.model_pub.publish(msg)
            return

        # Safe getter to avoid index out of bounds on partially unlocked models
        def get_p(arr, idx):
            return float(arr[idx]) if idx < len(arr) else 0.0

        # Determine if the advanced features have been unlocked
        is_locked_x = (len(px) == 1)
        is_locked_y = (len(py) == 1)

        # Default fallback for type in case custom constants aren't in the .msg file
        msg.model_type = getattr(CalibrationModel, 'TYPE_LINEAR', 1)

        if winner.name == "Bias":
            msg.model_type = getattr(CalibrationModel, 'TYPE_BIAS', 0)
            cx[5], cy[5] = get_p(px, 0), get_p(py, 0)

        elif winner.name == "Linear":
            msg.model_type = getattr(CalibrationModel, 'TYPE_LINEAR', 1)
            cx[5], cy[5] = get_p(px, 0), get_p(py, 0)
            
            # Dynamic mapping: decoupled_shared policy shifts indices!
            if "lin_x" in winner.current_features_x:
                idx = winner.current_features_x.index("lin_x")
                cx[3] = get_p(px, idx) / W
            if "lin_y" in winner.current_features_x:
                idx = winner.current_features_x.index("lin_y")
                cx[4] = get_p(px, idx) / H
                
            if "lin_x" in winner.current_features_y:
                idx = winner.current_features_y.index("lin_x")
                cy[3] = get_p(py, idx) / W
            if "lin_y" in winner.current_features_y:
                idx = winner.current_features_y.index("lin_y")
                cy[4] = get_p(py, idx) / H

        elif winner.name == "Radial Concentric":
            msg.model_type = getattr(CalibrationModel, 'TYPE_LINEAR', 1)
            cx[5], cy[5] = get_p(px, 0), get_p(py, 0)
            if not is_locked_x:
                cx[3] = get_p(px, 1) / W
            if not is_locked_y:
                cy[4] = get_p(py, 1) / H

        elif winner.name == "Radial Complete":
            msg.model_type = getattr(CalibrationModel, 'TYPE_RADIAL_UNIVERSAL', 2)
            cx[5], cy[5] = get_p(px, 0), get_p(py, 0)
            
            if not is_locked_x:
                # px[1] = dx*r, px[2] = dy*r, px[3] = dx, px[4] = dy, px[5] = bias offset
                cx[8] = get_p(px, 1) / (W**2)   # Main radial
                cx[9] = get_p(px, 2) / (H**2)   # Cross radial
                cx[3] = get_p(px, 3) / W        # Main linear
                cx[4] = get_p(px, 4) / H        # Cross linear
                cx[5] += get_p(px, 5)           # Add to bias
                
            if not is_locked_y:
                # py[1] = dx*r, py[2] = dy*r, py[3] = dx, py[4] = dy, py[5] = bias offset
                cy[9] = get_p(py, 1) / (W**2)   # Cross radial
                cy[8] = get_p(py, 2) / (H**2)   # Main radial
                cy[3] = get_p(py, 3) / W        # Cross linear
                cy[4] = get_p(py, 4) / H        # Main linear
                cy[5] += get_p(py, 5)

        elif winner.name == "Simple Radial":
            # Fallback to Quadratic if TYPE_RADIAL doesn't exist
            msg.model_type = getattr(CalibrationModel, 'TYPE_RADIAL', getattr(CalibrationModel, 'TYPE_QUADRATIC', 2))
            cx[5], cy[5] = get_p(px, 0), get_p(py, 0)
            if not is_locked_x:
                cx[8] = get_p(px, 1) / (W**2)
            if not is_locked_y:
                cy[8] = get_p(py, 2) / (H**2)

        # elif winner.name == "Radial Complete":
        #     msg.model_type = getattr(CalibrationModel, 'TYPE_RADIAL_UNIVERSAL', getattr(CalibrationModel, 'TYPE_QUADRATIC', 2))
        #     cx[5], cy[5] = get_p(px, 0), get_p(py, 0)
        #     if not is_locked_x:
        #         # px[1] is dx*r, px[3] is dx, px[5] is the extra ones offset
        #         cx[8], cx[3] = get_p(px, 1) / (W**2), get_p(px, 3) / W
        #         cx[5] += get_p(px, 5) 
        #     if not is_locked_y:
        #         # py[2] is dy*r, py[4] is dy
        #         cy[8], cy[4] = get_p(py, 2) / (H**2), get_p(py, 4) / H
        #         cy[5] += get_p(py, 5)

        elif winner.name == "Conic":
            msg.model_type = getattr(CalibrationModel, 'TYPE_QUADRATIC', 2)
            cx[5], cy[5] = get_p(px, 0), get_p(py, 0)
            if not is_locked_x:
                cx[0], cx[1], cx[2], cx[3], cx[4] = (
                    get_p(px, 1)/(W**2), get_p(px, 2)/(H**2), get_p(px, 3)/(W*H), get_p(px, 4)/W, get_p(px, 5)/H
                )
                cx[5] += get_p(px, 6)
            if not is_locked_y:
                cy[0], cy[1], cy[2], cy[3], cy[4] = (
                    get_p(py, 1)/(W**2), get_p(py, 2)/(H**2), get_p(py, 3)/(W*H), get_p(py, 4)/W, get_p(py, 5)/H
                )
                cy[5] += get_p(py, 6)

        elif winner.name == "Sigmoid X+Y":
            msg.model_type = getattr(CalibrationModel, 'TYPE_SIGMOIDAL', getattr(CalibrationModel, 'TYPE_QUADRATIC', 2))
            cx[5], cy[5] = get_p(px, 0), get_p(py, 0)
            if not is_locked_x:
                cx[6] = get_p(px, 1)   # px[1] maps exactly to tanh_x
                cx[7] = W / 2
                cx[5] += get_p(px, 3)  # Extra bias offset generated by sigmoid array
            if not is_locked_y:
                cy[6] = get_p(py, 2)   # py[2] maps exactly to tanh_y
                cy[7] = H / 2
                cy[5] += get_p(py, 3)

        msg.coeffs_x = [float(c) for c in cx]
        msg.coeffs_y =[float(c) for c in cy]
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

    def _plot_reservoir(self, train_pool, val_pool, save_name=None):
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
                -train_pool[:, 3],
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
                -val_pool[:, 3],
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
        self._pub_plt(fig, "quiver", save_name=save_name)

    def _plot_tournament(self, save_name=None):
        """Refactored Evolution Dashboard with Model Shading and Unlocks."""
        if not self.system_prequential_errors:
            return

        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        ev_range = np.arange(len(self.system_prequential_errors))
        sys_inst = np.array(self.system_prequential_errors)
        raw_inst = np.array(self.competitors[0].prequential_errors)
        
        # 1. Background Model Shading
        unique_models = [m.name for m in self.competitors]
        cmap = plt.get_cmap('Pastel1')
        
        if len(self.winner_idx_history) > 0:
            curr_start = 0
            curr_idx = self.winner_idx_history[0]
            for i, val in enumerate(self.winner_idx_history):
                # If model changed or we reached the end
                if val != curr_idx or i == len(self.winner_idx_history) - 1:
                    ax1.axvspan(curr_start, i, color=cmap(curr_idx % 9), alpha=0.3, zorder=0)
                    # Add label at the top of the shaded region
                    ax1.text((curr_start + i)/2, ax1.get_ylim()[1] * 0.9, 
                            unique_models[curr_idx], ha='center', fontsize=8, 
                            fontweight='bold', color='dimgrey', zorder=5)
                    curr_start, curr_idx = i, val

        # 2. Cumulative RMSE (AULC) Lines
        sys_cum = np.cumsum(sys_inst) / (ev_range + 1)
        raw_cum = np.cumsum(raw_inst) / (ev_range + 1)
        
        ax1.plot(raw_cum, color='firebrick', ls='--', lw=2, label='Baseline (Raw) AULC')
        ax1.plot(sys_cum, color='navy', lw=3, label='System (Winner) AULC')

        # 3. Feature Unlock Moments (Vertical Lines)
        # Check the active model for its graduation milestones
        winner = self.competitors[self.active_idx]
        for label, event_idx in winner.unlock_moments.items():
            ax1.axvline(x=event_idx, color='green', linestyle=':', alpha=0.6)
            ax1.text(event_idx, ax1.get_ylim()[1] * 0.1, label, 
                    rotation=90, verticalalignment='bottom', fontsize=7, color='green')

        ax1.set_title(f"Tournament Evolution: {winner.name} Active", loc='left', fontweight='bold')
        ax1.set_xlabel("Calibration Event Index")
        ax1.set_ylabel("Mean Error (AULC) [px]")
        ax1.legend(loc='upper right', fontsize='small')
        ax1.grid(True, alpha=0.15)

        self._pub_plt(fig, "tourney", save_name=save_name)

    def _plot_profile(self, save_name=None):
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
        self._pub_plt(fig, "profile", save_name=save_name)

    def _plot_prediction_field(self, save_name=None):
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
            -py.reshape(grid_y.shape),
            mag.reshape(grid_x.shape),
            cmap="jet",
            scale=1,
            scale_units="xy",
        )
        ax.set_xlim(0, gw)
        ax.set_ylim(gh,0)
        ax.set_title(f"Correction Field: {winner.name}")
        self._pub_plt(fig, "map", save_name=save_name)

    def _pub_plt(self, fig, key, save_name=None):
        # If a save_name is provided, write it to the log directory
        if save_name is not None:
            path = os.path.join(self.log_dir, save_name)
            fig.savefig(path, bbox_inches="tight")

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        img = cv2.cvtColor(np.asarray(canvas.buffer_rgba()), cv2.COLOR_RGBA2BGR)
        self.pubs[key].publish(self.bridge.cv2_to_imgmsg(img, "bgr8"))
        plt.close(fig)

    def joy_cb(self, msg: Joy):

        # 1. Report Error / User Stop (Xbox Button B or Menu)
        current_stop = msg.buttons[self.joy_userstop_button_index]
        if current_stop == 1 and self.last_stop_button_state == 0:
            self.get_logger().warn("USER REPORTED ERROR")
            self.log_user_error()

        self.last_stop_button_state = current_stop

        # 2. Reset and Resume (Xbox Button A)
        # Assuming index 0 for 'A' button. Add self.resume_btn_idx to __init__
        current_resume = msg.buttons[self.resume_btn_idx]
        if current_resume == 1 and self.last_resume_button_state == 0:
            self.dump_all_plots(label="experimenter_test_resumed")
            self.reset_calibration()

        self.last_resume_button_state = current_resume

    def _init_csv_headers(self):
        # For errors
        header = [
            "timestamp",
            "pupil_hardware_timestamp",
            "event_count",
            "bin_count",
            "button_id",
            "active_model",
        ] + [m.name for m in self.competitors]
        for f in [self.file_aulc, self.file_preq, self.file_rmse]:
            with open(f, "w", newline="") as csvfile:
                csv.writer(csvfile).writerow(header)

        # For user-reported errors, we log the state at the moment of the report
        with open(self.file_user, "w", newline="") as csvfile:
            csv.writer(csvfile).writerow(
                [
                    "timestamp",
                    "pupil_hardware_timestamp",
                    "event_count",
                    "bin_count",
                    "active_model",
                    "num_bins",
                    "total_samples",
                    "current_rmse",
                ]
            )

    def _append_to_csv(self, path, row):
        with open(path, "a", newline="") as f:
            csv.writer(f).writerow(row)

    def log_user_error(self):
        now = self.get_clock().now().to_msg()
        system_ts = f"{now.sec}.{now.nanosec:09d}"

        active = self.competitors[self.active_idx]

        # We add self.last_hardware_ts here
        row = [
            system_ts,
            self.last_hardware_ts,
            self.event_count,
            len(self.reservoir.bins),
            active.name,
            sum(len(b) for b in self.reservoir.bins.values()),
            active.macro_rmse_history[-1] if active.macro_rmse_history else 0.0,
        ]
        self._append_to_csv(self.file_user, row)

    # --- Reservoir Dump at Shutdown ---
    def dump_reservoir(self, label="training"):
        # Add a sub-timestamp to the file name to prevent accidental overwrites
        sub_ts = datetime.now().strftime("%H%M%S")
        filename = f"reservoir_dump_{label}_{sub_ts}.csv"
        path = os.path.join(self.log_dir, filename)

        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["bin_x", "bin_y", "gaze_x", "gaze_y", "err_x", "err_y"])
            for (bx, by), samples in self.reservoir.bins.items():
                for s in samples:
                    writer.writerow([bx, by, s[0], s[1], s[2], s[3]])
        self.get_logger().info(f"Reservoir saved to: {filename}")

    def on_shutdown(self):
        self.get_logger().info("Performing final data dump...")
        # Get plots of the final state
        self.dump_all_plots(label="shutdown")
        # Save the full CSV of all samples collected
        self.dump_reservoir(label="final_session")

    def dump_all_plots(self, label="manual"):
        """Generates and saves all current visualization plots to the session folder."""
        timestamp = datetime.now().strftime("%H%M%S")
        prefix = f"plot_{label}_ev{self.event_count}_{timestamp}"

        self.get_logger().info(f"Dumping plots with prefix: {prefix}")

        # Get current data split for the reservoir plot
        train_flat, val_flat = self.reservoir._get_stratified_split()

        # We call our existing plot functions but tell them to save to disk
        self._plot_reservoir(train_flat, val_flat, save_name=f"{prefix}_reservoir.png")
        self._plot_tournament(save_name=f"{prefix}_tournament.png")
        self._plot_profile(save_name=f"{prefix}_profile.png")
        self._plot_prediction_field(save_name=f"{prefix}_map.png")


def main():
    rclpy.init()
    node = CalibrationLearner()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info(
            "Shutting down: Saving final reservoir and flushing logs..."
        )
        node.on_shutdown()

        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
