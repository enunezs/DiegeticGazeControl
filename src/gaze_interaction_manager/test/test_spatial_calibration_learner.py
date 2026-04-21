#!/usr/bin/env python3

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

# Import your node and classes
# Adjust the sys.path insertion as needed for your specific directory structure
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, '..', 'scripts')
sys.path.insert(0, scripts_dir)

from calibration_learner import CalibrationLearner, SpatialReservoir, GazeCorrectionFramework

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
    monkeypatch.setattr(os, 'getcwd', lambda: str(tmp_path))
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

def test_reservoir_outlier_rejection():
    """
    Samples with an error > 150px should be silently dropped by the reservoir.
    """
    cfg = {"bin_size": 150, "samples_per_bin": 50, "val_size": 10, "thinning_stride": 1}
    res = SpatialReservoir(cfg)
    
    # Gaze at (500, 500)
    gx = np.array([500.0, 500.0])
    gy = np.array([500.0, 500.0])
    
    # Target 1 is close (error = 10px) -> ACCEPT
    # Target 2 is far (error = 160px) -> REJECT
    ex = np.array([10.0, 160.0])
    ey = np.array([10.0, 160.0])
    
    res.add_segment(gx, gy, ex, ey)
    
    bin_key = (500 // 150, 500 // 150)
    samples = res.bins[bin_key]
    
    assert len(samples) == 1, "Outlier was not rejected!"
    assert samples[0][2] == 10.0, "The wrong sample was kept."


def test_reservoir_stratified_split_logic():
    """
    Verifies that the FIFO/interleaved validation split properly separates
    training and validation data without overlap.
    """
    cfg = {"bin_size": 150, "samples_per_bin": 50, "val_size": 10, "thinning_stride": 1, "min_samples_per_bin_threshold": 4}
    res = SpatialReservoir(cfg)
    
    # Feed 20 samples to exactly one bin
    gx = np.full(20, 100.0)
    gy = np.full(20, 100.0)
    ex = np.arange(20, dtype=float)  # unique values to trace them
    ey = np.arange(20, dtype=float)
    
    res.add_segment(gx, gy, ex, ey)
    
    train_pool, val_pool = res._get_stratified_split()
    
    assert len(train_pool) > 0 and len(val_pool) > 0, "Split failed to populate both pools."
    
    # Ensure mutually exclusive
    train_errors = set(train_pool[:, 2])
    val_errors = set(val_pool[:, 2])
    intersection = train_errors.intersection(val_errors)
    
    assert len(intersection) == 0, f"Data leakage! Train and Val sets overlap: {intersection}"

# ===========================================================================
# 2. FEATURE GRADUATION & MODEL TRAINING
# ===========================================================================

def test_feature_graduation_trigger_bins():
    """
    Models start as simple "Bias" models to avoid overfitting. 
    They should only unlock their full features when n_bins >= trigger_bins.
    """
    cfg = {"center_x": 800, "center_y": 600, "solver": "ridge"}
    model = GazeCorrectionFramework("TestLinear", ["bias", "lin_x"], cfg | {"trigger_bins": 3})
    
    # Mock data arrays
    train_data = np.array([
        [100, 100, 5, 5],
        [200, 200, -5, -5],
        [300, 300, 2, 2]
    ])
    
    # 1. Train with only 1 bin -> Should remain "bias" only
    model.train((train_data, train_data), n_bins=1, event_idx=1)
    assert model.current_features == ["bias"], "Model unlocked prematurely!"
    assert len(model.params["x"]) == 1, "Bias model should only have 1 coefficient."
    
    # 2. Train with 3 bins -> Should unlock full recipe
    model.train((train_data, train_data), n_bins=3, event_idx=2)
    assert model.current_features == ["bias", "lin_x"], "Model failed to unlock features!"
    assert len(model.params["x"]) == 2, "Linear model should have 2 coefficients."

# ===========================================================================
# 3. TOURNAMENT & HYSTERESIS LOGIC
# ===========================================================================

def test_tournament_hysteresis_prevents_flickering():
    """
    Validates that a challenger model only becomes active if its score beats 
    the active model by at least the hysteresis threshold.
    """
    node = CalibrationLearner()
    node.set_parameters([
        rclpy.parameter.Parameter('selection_strategy', value='RMSE'),
        rclpy.parameter.Parameter('rmse_hysteresis', value=2.0)
    ])
    
    # Active model is Bias (idx=1)
    node.active_idx = 1
    
    # Mock some bins so the tournament runs
    node.reservoir.bins[(0,0)] = deque([(100, 100, 0, 0)])
    
    # Mock prediction returns so we control the RMSE
    # Active Model (Bias) gets RMSE ~ 10.0
    node.competitors[1].predict = lambda gx, gy: (gx + 10, gy) 
    
    # Challenger (Linear, idx=2) gets RMSE ~ 9.0 (better, but diff < 2.0)
    node.competitors[2].predict = lambda gx, gy: (gx + 9, gy)
    
    node.run_selection_tournament()
    
    assert node.active_idx == 1, "Switched models despite hysteresis not being met!"
    
    # Now Challenger gets RMSE ~ 7.0 (diff = 3.0, which is > hysteresis 2.0)
    node.competitors[2].predict = lambda gx, gy: (gx + 7, gy)
    node.run_selection_tournament()
    
    assert node.active_idx == 2, "Failed to switch models when hysteresis threshold was exceeded."

# ===========================================================================
# 4. ROS COEFFICIENT MAPPING (CRITICAL MATH VERIFICATION)
# ===========================================================================

def test_model_publication_coefficient_mapping():
    """
    Ensures that the complex internal state of the Scikit-Learn models is 
    mapped to the exact, correct slots in the CalibrationModel ROS message.
    """
    node = CalibrationLearner()
    published = capture_model_pubs(node)
    
    W, H = 800.0, 600.0 # Node normalization constants
    
    # --- TEST A: RADIAL COMPLETE ---
    node.active_idx = 6 # "Radial Complete"
    winner = node.competitors[6]
    winner.current_features = winner.master_recipe # Unlock
    
    # Internal Recipe: ["bias", "radial_universal"] -> [dx*r, dy*r, dx, dy, bias]
    # We mock the learned weights. 
    # Let's say: radial_x=2.0, radial_y=3.0, lin_x=4.0, lin_y=5.0, bias=6.0
    winner.params = {
        "x": np.array([2.0, 0.0, 4.0, 0.0, 6.0]),
        "y": np.array([0.0, 3.0, 0.0, 5.0, 6.0])
    }
    
    node.publish_model_update()
    msg = published[-1]
    
    assert msg.model_type == CalibrationModel.TYPE_RADIAL_UNIVERSAL
    
    # Check X Coefficients Mapping
    assert msg.coeffs_x[8] == 2.0 / (W**2), "Radial X term mapped to wrong index or scaled incorrectly!"
    assert msg.coeffs_x[3] == 4.0 / W, "Linear X term mapped incorrectly!"
    assert msg.coeffs_x[5] == 6.0, "Bias X term mapped incorrectly!"
    
    # --- TEST B: CONIC ---
    node.active_idx = 7 # "Conic"
    winner = node.competitors[7]
    winner.current_features = winner.master_recipe # Unlock
    
    # Internal Recipe: [dx2, dy2, dxdy, dx, dy, bias]
    winner.params = {
        "x": np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]),
        "y": np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    }
    
    node.publish_model_update()
    msg_conic = published[-1]
    
    assert msg_conic.model_type == CalibrationModel.TYPE_QUADRATIC
    assert msg_conic.coeffs_x[0] == 1.0 / (W**2), "Quadratic dx^2 mapped incorrectly!"
    assert msg_conic.coeffs_x[2] == 3.0 / (W*H), "Cross term dxdy mapped incorrectly!"

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
    tx = [105, 305, 505, 705, 905] # 5px error in X
    ty = [105, 305, 505, 705, 905] # 5px error in Y
    
    msg = make_segment(gx, gy, tx, ty)
    
    try:
        node.segment_cb(msg)
    except Exception as e:
        pytest.fail(f"segment_cb crashed: {e}")
        
    assert len(published) == 1, "Failed to publish CalibrationModel after processing segment."
    assert len(node.reservoir.bins) > 0, "Reservoir did not store the incoming data."

def test_joy_reset_clears_state_and_models():
    """
    Pressing the Reset/Resume button on the Joy controller must wipe the 
    Reservoir, reset the active tournament model to Bias, and lock all 
    feature graduation back to base state.
    """
    node = CalibrationLearner()
    
    # 1. Dirty the state
    node.reservoir.bins[(0,0)] = deque([(1,1,1,1)])
    node.active_idx = 5
    node.competitors[5].current_features = ["unlocked_feature"]
    
    # 2. Trigger Reset via Joy
    joy_msg = Joy()
    joy_msg.buttons = [0] * 15
    joy_msg.buttons[node.resume_btn_idx] = 1 # Press reset button
    
    node.joy_cb(joy_msg)
    
    # 3. Verify Clean Slate
    assert len(node.reservoir.bins) == 0, "Reservoir was not cleared!"
    assert node.active_idx == 1, "Active model did not reset to Bias (idx=1)!"
    assert node.competitors[5].current_features == ["bias"], "Model features did not lock back to 'bias'!"
    assert node.last_resume_button_state == 1