#!/usr/bin/env python3
"""
Run with:
python3 -m pytest src/gaze_interaction_manager/test/test_spatial_calibration_learner.py -v -s -k test_sigmoid_publication_mapping


STATUS:
* PASS  test_joy_reset_clears_decoupled_state - RuntimeError: Context must be initialized before it can be shutdown
* PASS test_tournament_hysteresis_prevents_flickering - AssertionError: Switched models despite hysteresis not...
* PASS test_kfolds_spatial_interleaving - assert 1 == 2

! FAILED test_tournament_bic_penalty - assert 0 == 1
? FAILED test_sigmoid_publication_mapping - KeyError: 'trigger_bins'


"""

import os
import sys
import pytest
import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Point
from std_msgs.msg import Header
from pupil_neon_ros.msg import GazeData
from gaze_interaction_manager.msg import InteractionSegment, CalibrationModel

from collections import deque

# Import your node and classes
# Adjust the sys.path insertion as needed for your specific directory structure
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, "..", "scripts")
sys.path.insert(0, scripts_dir)

from spatial_calibration_learner import (
    CalibrationLearner,
    SpatialReservoir,
    GazeCorrectionFramework,
)

# ===========================================================================
# Fixtures & Helpers
# ===========================================================================


@pytest.fixture(autouse=True)
def ros_setup(tmp_path, monkeypatch):
    """
    Initializes rclpy and redirects the node's file logging to a temporary
    pytest directory so we don't litter the real filesystem with test CSVs.
    """
    rclpy.init()
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    yield
    rclpy.shutdown()


def make_segment(gx_list, gy_list, tx_list, ty_list):
    """Creates a mock InteractionSegment message."""
    msg = InteractionSegment()
    for gx, gy, tx, ty in zip(gx_list, gy_list, tx_list, ty_list):
        g_pt = GazeData(x=float(gx), y=float(gy))
        # Add mock timestamps so CSV logger doesn't crash
        g_pt.header.stamp.sec = 1
        g_pt.timestamp_unix_seconds = 1.0

        t_pt = Point(x=float(tx), y=float(ty), z=0.0)

        msg.gaze_samples.append(g_pt)
        msg.target_samples.append(t_pt)
    msg.button_id = "test_btn"
    return msg


def capture_model_pubs(node):
    """Intercepts published CalibrationModel messages."""
    published = []
    node.model_pub.publish = lambda msg: published.append(msg)
    return published


# ===========================================================================
# 1. SPATIAL RESERVOIR TESTS
# ===========================================================================


def test_reservoir_thinning_and_fifo():
    cfg = {
        "bin_size": 100,
        "samples_per_bin": 5,  # Low capacity for testing
        "thinning_stride": 2,  # Keep every 2nd sample
    }
    res = SpatialReservoir(cfg)

    # Send 10 samples to one bin
    # Indices: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    # Thinned (stride 2): 0, 2, 4, 6, 8 (5 samples)
    gx = np.full(10, 150.0)
    gy = np.full(10, 150.0)
    ex = np.arange(10, dtype=float)  # 0 to 9
    ey = np.arange(10, dtype=float)

    res.add_segment(gx, gy, ex, ey)
    bin_samples = res.bins[(1, 1)]

    assert len(bin_samples) == 5
    assert bin_samples[0][2] == 0.0  # First sample kept
    assert bin_samples[-1][2] == 8.0  # Last sample before capacity reached

    # Add 2 more thinned samples (from a segment of 4)
    # Thinned indices 10, 12. These should push out indices 0, 2.
    res.add_segment(
        np.full(4, 150.0),
        np.full(4, 150.0),
        np.array([10.0, 11.0, 12.0, 13.0]),
        np.array([10.0, 11.0, 12.0, 13.0]),
    )

    assert len(bin_samples) == 5
    # FIFO check: Oldest thinned sample (0.0) should be gone
    remaining_errors = [s[2] for s in bin_samples]
    assert 0.0 not in remaining_errors
    assert 12.0 in remaining_errors


def test_reservoir_outlier_rejection():
    cfg = {"bin_size": 150, "samples_per_bin": 50, "max_error_cap": 150.0}
    res = SpatialReservoir(cfg)
    gx, gy = np.array([500.0, 500.0]), np.array([500.0, 500.0])
    ex, ey = np.array([10.0, 160.0]), np.array([10.0, 160.0])  # 160 > 150 cap

    res.add_segment(gx, gy, ex, ey)
    bin_key = (500 // 150, 500 // 150)
    assert len(res.bins[bin_key]) == 1


def test_reservoir_spatial_block_split():
    """Verifies that spatial_block strategy actually separates bins.
    Requires at least 5 bins to trigger the logic in the new code."""
    cfg = {
        "bin_size": 100,
        "cv_strategy": "spatial_block",
        "spatial_val_ratio": 0.2,
        "max_error_cap": 200.0,
        "thinning_stride": 1,
    }
    res = SpatialReservoir(cfg)

    # Add data to 6 distinct bins to satisfy 'len(all_bin_ids) < 5' check
    for i in range(6):
        pos = float(i * 110)
        res.add_segment(
            np.array([pos]), np.array([pos]), np.array([1.0]), np.array([1.0])
        )

    train, val = res.get_split()
    assert len(train) > 0
    assert len(val) > 0
    # Ensure a bin was moved entirely to validation
    train_bins = set([(int(x // 100), int(y // 100)) for x, y, ex, ey in train])
    val_bins = set([(int(x // 100), int(y // 100)) for x, y, ex, ey in val])
    assert train_bins.isdisjoint(val_bins)


def test_reservoir_stratified_split_logic():
    """
    Verifies that the FIFO/interleaved validation split properly separates
    training and validation data without overlap.
    """
    cfg = {
        "bin_size": 150,
        "samples_per_bin": 50,
        "val_size": 10,
        "thinning_stride": 1,
        "min_samples_per_bin_threshold": 4,
    }
    res = SpatialReservoir(cfg)

    # Feed 20 samples to exactly one bin
    gx = np.full(20, 100.0)
    gy = np.full(20, 100.0)
    ex = np.arange(20, dtype=float)  # unique values to trace them
    ey = np.arange(20, dtype=float)

    res.add_segment(gx, gy, ex, ey)

    train_pool, val_pool = res._get_stratified_split()

    assert (
        len(train_pool) > 0 and len(val_pool) > 0
    ), "Split failed to populate both pools."

    # Ensure mutually exclusive
    train_errors = set(train_pool[:, 2])
    val_errors = set(val_pool[:, 2])
    intersection = train_errors.intersection(val_errors)

    assert (
        len(intersection) == 0
    ), f"Data leakage! Train and Val sets overlap: {intersection}"


def test_kfolds_spatial_interleaving():
    cfg = {
        "bin_size": 100,
        "cv_strategy": "kfolds_spatial_block",
        "cv_include_diagonals": False,
        "n_folds": 2,
        "thinning_stride": 1,
        "max_error_cap": 100.0,
    }
    res = SpatialReservoir(cfg)

    ### A. Add segment check ###
    # Add data to 4 bins in a square
    # (0,0), (1,0)
    # (0,1), (1,1)
    # gx, gy, ex, ey
    res.add_segment(
        np.array([50, 50, 350, 350]),  # gx
        np.array([50, 350, 50, 350]),  # gy
        np.array([1, 2, 3, 4]),  # ex
        np.array([-1, -2, -3, -4]),  # ey
    )
    print(res.bins)
    assert res.bins.keys() == {(0, 0), (3, 0), (0, 3), (3, 3)}

    ### B. Get spatial kfolds check ###
    folds = res._get_spatial_kfolds_iterator()
    print(folds)
    # Triggering right function?
    assert not (len(list(res.bins.keys())) < cfg["n_folds"] * 2)

    assert len(folds) == 2

    # Fold 0 should contain bins where (bx + by) % 2 == 0: (0,0) and (3,3)
    # Fold 1 should contain (3,0) and (0,3)
    # Check that val set of fold 0 has different gx/gy than fold 1
    val_fold_0 = folds[0][1]
    val_fold_1 = folds[1][1]

    assert not np.array_equal(val_fold_0, val_fold_1)


def test_sigmoid_publication_mapping():
    node = CalibrationLearner()
    # Sigmoid is index 5 in your competitor list
    node.active_idx = 5
    winner = node.competitors[5]

    # Params for [tanh(dx/400), tanh(dy/300), bias]
    winner.params = {"x": np.array([50.0, 0.0, 10.0]), "y": np.array([0.0, 30.0, 5.0])}

    published = []
    node.model_pub.publish = lambda m: published.append(m)
    node.publish_model_update()

    msg = published[0]
    assert msg.model_type == CalibrationModel.TYPE_SIGMOIDAL
    assert msg.coeffs_x[6] == 50.0  # Amplitude
    assert msg.coeffs_x[7] == 400.0  # Scale (W/2)
    assert msg.coeffs_x[5] == 10.0  # Bias


# ===========================================================================
# 2. FEATURE GRADUATION & DECOUPLED UNLOCKING
# ===========================================================================


def test_feature_graduation_trigger_bins():
    """Updated to use coverage_dict and specific policy."""
    cfg = {
        "center_x": 800,
        "center_y": 600,
        "solver": "ridge",
        "policy": "original_coupled",
        "trigger_bins": 3,
    }
    model = GazeCorrectionFramework("TestLinear", ["bias", "lin_x"], cfg)
    train_data = np.array([[100, 100, 5, 5], [200, 200, -5, -5]])

    # 1. 2D coverage < 3
    model.train((train_data, train_data), {"x": 2, "y": 2, "2d": 2}, event_idx=1)
    assert model.current_features_x == ["bias"]

    # 2. 2D coverage >= 3
    model.train((train_data, train_data), {"x": 3, "y": 3, "2d": 3}, event_idx=2)
    assert "lin_x" in model.current_features_x


def test_decoupled_unlocking_policy():
    """Tests the new asymmetric unlocking logic."""
    cfg = {
        "center_x": 800,
        "center_y": 600,
        "solver": "ridge",
        "policy": "decoupled_shared",
        "trigger_x": 5,
        "trigger_y": 10,
    }
    recipe = {"x": ["bias", "lin_x"], "y": ["bias", "lin_y"]}
    model = GazeCorrectionFramework("DecoupledTest", recipe, cfg)
    data = (np.array([[100, 100, 1, 1]]), np.array([[100, 100, 1, 1]]))

    # X meets trigger, Y does not
    model.train(data, {"x": 6, "y": 2, "2d": 2}, event_idx=1)
    assert "lin_x" in model.current_features_x
    assert model.current_features_y == ["bias"]
    assert "x_unlock" in model.unlock_moments


def test_decoupled_shared_rejoin():
    recipe = {"x": ["bias", "lin_x", "cross_xy"], "y": ["bias", "lin_y", "cross_xy"]}
    cfg = {
        "policy": "decoupled_shared",
        "trigger_x": 3,
        "trigger_y": 3,
        "center_x": 800,
        "center_y": 600,
    }
    model = GazeCorrectionFramework("Test", recipe, cfg)
    dummy_data = (np.array([[100, 100, 1, 1]]), np.array([[100, 100, 1, 1]]))

    # 1. Only X triggered
    model.train(dummy_data, {"x": 4, "y": 1, "2d": 1}, 1)
    assert "lin_x" in model.current_features_x
    assert "cross_xy" not in model.current_features_x  # Not yet!

    # 2. Both triggered -> Full Graduation
    model.train(dummy_data, {"x": 4, "y": 4, "2d": 1}, 2)
    assert "cross_xy" in model.current_features_x
    assert "cross_xy" in model.current_features_y
    assert "interaction_unlock" in model.unlock_moments


# ===========================================================================
# 3. MATH & MAPPING
# ===========================================================================


def test_model_publication_coefficient_mapping():
    node = CalibrationLearner()
    # Mocking the winner as "Radial Complete" (must match Learner's internal string name)
    node.active_idx = 6
    winner = node.competitors[6]
    winner.current_features_x = winner.master_recipe_x
    winner.current_features_y = winner.master_recipe_y

    # [dx*r/W2, dy*r/H2, dx/W, dy/H, bias]
    winner.params = {
        "x": np.array([2.0, 0.0, 4.0, 0.0, 6.0]),
        "y": np.array([0.0, 3.0, 0.0, 5.0, 6.0]),
    }

    # Intercept publication
    published = []
    node.model_pub.publish = lambda msg: published.append(msg)
    node.publish_model_update()

    msg = published[0]
    W = 800.0
    assert msg.model_type == CalibrationModel.TYPE_RADIAL_UNIVERSAL
    assert msg.coeffs_x[8] == pytest.approx(2.0 / (W**2))
    assert msg.coeffs_x[3] == pytest.approx(4.0 / W)
    assert msg.coeffs_x[5] == pytest.approx(6.0)


def test_radial_concentric_special_mapping():
    cfg = {"center_x": 800, "center_y": 600}
    model = GazeCorrectionFramework(
        "Radial Concentric", ["bias", "radial_concentric"], cfg
    )
    model.params["x"] = np.array([10.0, 1.0])  # bias, radial_scale
    model.params["y"] = np.array([5.0, 0.5])

    # Gaze at 1600 (dx=800). Correction = 10 + 1.0*(800/800) = 11.0
    px, py = model.predict(np.array([1600.0]), np.array([600.0]))
    assert px[0] == 11.0
    assert py[0] == 5.0


# ===========================================================================
# 3. TOURNAMENT & HYSTERESIS LOGIC
# ===========================================================================


def test_tournament_bic_penalty():
    node = CalibrationLearner()
    node.set_parameters([rclpy.parameter.Parameter("selection_strategy", value="BIC")])

    # 1. Setup Bias Model (Idx 1) - Error is 10.0
    # 2. Setup Conic Model (Idx 7) - Error is 9.9 (Slightly better)

    # We need to mock n_bins for the log(n) term in BIC
    node.reservoir.bins = {(i, 0): deque([(0, 0, 0, 0)]) for i in range(10)}
    n_bins = 10

    # Mock scores
    def mock_score(model_idx, rmse):
        m = node.competitors[model_idx]
        mse = rmse**2
        # BIC = ln(n)*k + n*ln(mse)
        return np.log(n_bins) * m.k_total + n_bins * np.log(mse)

    # Bias k=2 (1 per axis), Conic k=12 (6 per axis)
    bias_score = mock_score(1, 10.0)
    conic_score = mock_score(7, 9.9)

    # In this scenario, Conic has 10 more parameters.
    # BIC penalty: ln(10) * 10 approx 23.0.
    # Unless ln(mse) drops significantly, Bias should win.
    assert bias_score < conic_score

    # Manually run tournament with these mocked conditions
    node.competitors[1].predict = lambda x, y: (np.zeros_like(x) + 10, np.zeros_like(y))
    node.competitors[7].predict = lambda x, y: (
        np.zeros_like(x) + 9.9,
        np.zeros_like(y),
    )

    node.active_idx = 1
    node.run_selection_tournament()
    assert node.active_idx == 1  # Stays bias because Conic was penalized for complexity


def test_joy_reset_clears_decoupled_state(monkeypatch, tmp_path):
    """Checks that reset clears the new axis-specific feature lists."""

    monkeypatch.setattr("os.getcwd", lambda: str(tmp_path))
    if not rclpy.ok():
        rclpy.init()

    node = CalibrationLearner()
    # Dirty the state
    lin_model = node.competitors[2]  # Linear
    lin_model.current_features_x = ["bias", "lin_x"]
    lin_model.unlock_moments["x_unlock"] = 5

    # Trigger Reset
    msg = Joy()
    msg.buttons = [0] * 20
    msg.buttons[node.resume_btn_idx] = 1
    node.joy_cb(msg)

    assert lin_model.current_features_x == ["bias"]
    assert lin_model.unlock_moments == {}
    assert node.active_idx == 1  # Back to Bias


def test_tournament_hysteresis_prevents_flickering():
    """
    Validates that a challenger model only becomes active if its score beats
    the active model by at least the hysteresis threshold.
    """
    node = CalibrationLearner()
    node.set_parameters(
        [
            rclpy.parameter.Parameter("selection_strategy", value="RMSE"),
            rclpy.parameter.Parameter("rmse_hysteresis", value=2.0),
        ]
    )

    # Active model is Bias (idx=1)
    node.active_idx = 1

    # Mock some bins so the tournament runs
    node.reservoir.bins[(0, 0)] = deque([(100, 100, 0, 0)])

    # Mock prediction returns so we control the RMSE
    node.competitors[0].predict = lambda gx, gy: (gx + 20, gy)
    node.competitors[3].predict = lambda gx, gy: (gx + 20, gy)
    node.competitors[4].predict = lambda gx, gy: (gx + 20, gy)
    node.competitors[5].predict = lambda gx, gy: (gx + 20, gy)
    node.competitors[6].predict = lambda gx, gy: (gx + 20, gy)
    node.competitors[7].predict = lambda gx, gy: (gx + 20, gy)

    # Active Model (Bias) gets RMSE ~ 10.0
    node.competitors[1].predict = lambda gx, gy: (gx + 10, gy)

    # Challenger (Linear, idx=2) gets RMSE ~ 9.0 (better, but diff < 2.0)
    node.competitors[2].predict = lambda gx, gy: (gx + 9, gy)

    node.run_selection_tournament()

    assert node.competitors[1].predict(np.array([100]), np.array([100])) == (110, 100)
    assert node.competitors[2].predict(np.array([100]), np.array([100])) == (109, 100)

    # assert node.competitors[1].macro_rmse_history[-1] == 10.0
    # assert node.competitors[2].macro_rmse_history[-1] == 9.0

    assert node.active_idx == 1, "Switched models despite hysteresis not being met!"

    # Now Challenger gets RMSE ~ 7.0 (diff = 3.0, which is > hysteresis 2.0)
    node.competitors[2].predict = lambda gx, gy: (gx + 7, gy)
    node.run_selection_tournament()

    assert (
        node.active_idx == 2
    ), "Failed to switch models when hysteresis threshold was exceeded."


# ===========================================================================
# 4. SYSTEM RESET
# ===========================================================================


def test_joy_reset_clears_state(monkeypatch, tmp_path):
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    node = CalibrationLearner()

    # Dirty the state
    node.reservoir.add_segment(
        np.array([100.0]), np.array([100.0]), np.array([1.0]), np.array([1.0])
    )
    node.active_idx = 3
    node.competitors[2].current_features_x = ["bias", "lin_x"]

    joy_msg = Joy()
    joy_msg.buttons = [0] * 20
    joy_msg.buttons[node.resume_btn_idx] = 1
    node.joy_cb(joy_msg)

    assert len(node.reservoir.bins) == 0
    assert node.active_idx == 1
    assert node.competitors[2].current_features_x == ["bias"]


# ===========================================================================
# 5. NODE INTEGRATION & RESET
# ===========================================================================


def test_end_to_end_segment_processing_no_crash():
    """
    Feeds an interaction segment directly into the node callback to ensure
    the entire pipeline (eval -> split -> train -> tourney -> pub) runs.
    """
    node = CalibrationLearner()
    published = capture_model_pubs(node)

    # Provide enough unique locations to trigger training splits
    gx = [100, 300, 500, 700, 900]
    gy = [100, 300, 500, 700, 900]
    tx = [105, 305, 505, 705, 905]  # 5px error in X
    ty = [105, 305, 505, 705, 905]  # 5px error in Y

    msg = make_segment(gx, gy, tx, ty)

    try:
        node.segment_cb(msg)
    except Exception as e:
        pytest.fail(f"segment_cb crashed: {e}")

    assert (
        len(published) == 1
    ), "Failed to publish CalibrationModel after processing segment."
    assert len(node.reservoir.bins) > 0, "Reservoir did not store the incoming data."


def test_joy_reset_clears_state_and_models():
    """
    Pressing the Reset/Resume button on the Joy controller must wipe the
    Reservoir, reset the active tournament model to Bias, and lock all
    feature graduation back to base state.
    """
    node = CalibrationLearner()

    # 1. Dirty the state
    node.reservoir.bins[(0, 0)] = deque([(1, 1, 1, 1)])
    node.active_idx = 5
    node.competitors[5].current_features = ["unlocked_feature"]

    # 2. Trigger Reset via Joy
    joy_msg = Joy()
    joy_msg.buttons = [0] * 15
    joy_msg.buttons[node.resume_btn_idx] = 1  # Press reset button

    node.joy_cb(joy_msg)

    # 3. Verify Clean Slate
    assert len(node.reservoir.bins) == 0, "Reservoir was not cleared!"
    assert node.active_idx == 1, "Active model did not reset to Bias (idx=1)!"
    assert node.competitors[5].current_features == [
        "bias"
    ], "Model features did not lock back to 'bias'!"
    assert node.last_resume_button_state == 1
