#!/usr/bin/env python3
"""
Run with:
python3 -m pytest src/gaze_interaction_manager/test/test_integration_controller_learner.py -v -s

"""

#!/usr/bin/env python3

import os
import sys
import pytest
import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import PointStamped

# Import Messages
from std_msgs.msg import Header
from geometry_msgs.msg import Point
from pupil_neon_ros.msg import GazeData, GazeEvent
from gaze_interaction_manager.msg import (
    ButtonStatus,
    InteractionSegment,
    CalibrationModel,
)
from diegetic_transform_engine.msg import DiegeticButton2D

# Import Nodes
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, "..", "scripts")
sys.path.insert(0, scripts_dir)
src_dir = os.path.join(current_dir, "..", "..", "diegetic_transform_engine", "scripts")
sys.path.insert(0, src_dir)

from gaze_controller import GazeController
from spatial_calibration_learner import CalibrationLearner

# ===========================================================================
# Helpers & Fixtures
# ===========================================================================


def make_button(button_id, cx, cy, t_sec, t_nanosec=0):
    msg = ButtonStatus(
        button_status=ButtonStatus.BUTTON_ACTIVE,
        button=DiegeticButton2D(
            button_id=button_id, center_x=float(cx), center_y=float(cy)
        ),
    )
    msg.header.stamp.sec = t_sec
    msg.header.stamp.nanosec = t_nanosec
    return msg


def make_gaze(x, y, t_sec, t_nanosec=0):
    msg = GazeData(x=float(x), y=float(y))
    msg.header.stamp.sec = t_sec
    msg.header.stamp.nanosec = t_nanosec
    return msg


def make_saccade(t_ns):
    return GazeEvent(start_time_ns=t_ns)


class IntegrationSystem:
    """Encapsulates both nodes and wires them together via mock queues."""

    def __init__(self):
        self.controller = GazeController()
        self.learner = CalibrationLearner()

        # Zero out controller timing trims for deterministic testing
        self.controller.set_parameters(
            [
                rclpy.parameter.Parameter("internal_pipeline_delay_ms", value=0.0),
                rclpy.parameter.Parameter("start_trim_ms", value=0.0),
                rclpy.parameter.Parameter("min_event_duration_ms", value=0.0),
                rclpy.parameter.Parameter("terminal_trim_ms", value=0.0),
                rclpy.parameter.Parameter("sticky_button_interaction", value=False),
            ]
        )

        # Force Learner to use RMSE for immediate switching & DISABLE PLOTTING for speed
        self.learner.set_parameters(
            [
                rclpy.parameter.Parameter("selection_strategy", value="RMSE"),
                rclpy.parameter.Parameter("rmse_hysteresis", value=0.0),
                rclpy.parameter.Parameter("publish_data_quiver", value=False),
                rclpy.parameter.Parameter("publish_status_profile", value=False),
                rclpy.parameter.Parameter("publish_prediction_map", value=False),
                rclpy.parameter.Parameter("publish_tournament", value=False),
            ]
        )

        # Directly override Learner CFG to use un-regularized Linear solver.
        # This prevents Ridge (L2 penalty) from slightly shrinking the bias from 50.0 to ~49.8
        self.learner.cfg["solver"] = "linear"

        # --- WIRE THE ROS GRAPH (Queue-based to prevent thread Deadlocks) ---
        self.segment_queue = []
        self.model_queue = []

        self.controller.segment_pub.publish = lambda msg: self.segment_queue.append(msg)
        self.learner.model_pub.publish = lambda msg: self.model_queue.append(msg)

        # Intercept corrected gaze to check the final output
        self.corrected_gaze_msgs = []
        self.controller.corrected_gaze_pub.publish = (
            lambda msg: self.corrected_gaze_msgs.append(msg)
        )

    def flush_network(self):
        """Simulates ROS middleware delivering messages."""
        while self.segment_queue or self.model_queue:
            if self.segment_queue:
                self.learner.segment_cb(self.segment_queue.pop(0))
            if self.model_queue:
                self.controller.model_cb(self.model_queue.pop(0))

    def trigger_interaction(self, btn_x, btn_y, gaze_x, gaze_y, t_sec):
        """Simulates a full closed interaction loop with enough samples."""
        # 1. Start bounding button (T = t_sec)
        self.controller.button_cb(make_button("btn1", btn_x, btn_y, t_sec, 0))

        # 2. Feed 30 gaze samples (200Hz = 0.005s per sample)
        # 30 samples ensures the Learner has enough data to clear validation thresholds
        for i in range(30):
            t = t_sec + 0.1 + (i * 0.005)
            sec = int(t)
            nanosec = int(round((t - sec) * 1e9))
            self.controller.gaze_cb(make_gaze(gaze_x, gaze_y, sec, nanosec))

        # 3. End bounding button (T = t_sec + 1)
        self.controller.button_cb(make_button("btn1", btn_x, btn_y, t_sec + 1, 0))

        # 4. End the segment with a saccade (T = t_sec + 1.5)
        self.controller.saccade_cb(make_saccade(int((t_sec + 1.5) * 1e9)))

        # 5. Deliver the messages across the mock network
        self.flush_network()


@pytest.fixture(autouse=True)
def ros_setup(tmp_path, monkeypatch):
    """Initializes ROS and redirects Learner CSVs to temp dir."""
    rclpy.init()
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    yield
    rclpy.shutdown()


# ===========================================================================
# INTEGRATION TESTS
# ===========================================================================


def test_closed_loop_bias_correction():
    """
    Test the full end-to-end loop:
    1. Gaze is consistently off by +50x, +50y.
    2. Nodes process interaction (feeding 30 samples).
    3. Learner fits a Bias model and sends it back.
    4. Next raw gaze should be corrected by +50x, +50y by the Controller.
    """
    sys = IntegrationSystem()

    # Target is 100,100. Gaze is 50,50 (Error = +50, +50)
    sys.trigger_interaction(btn_x=100, btn_y=100, gaze_x=50, gaze_y=50, t_sec=1)

    assert sys.controller.model_type == CalibrationModel.TYPE_BIAS
    # Using pytest.approx just in case floating point arithmetic causes 49.9999999
    assert sys.controller.coeffs_x[5] == pytest.approx(50.0)
    assert sys.controller.coeffs_y[5] == pytest.approx(50.0)

    # Test the correction application
    sys.corrected_gaze_msgs.clear()

    # Send a new raw gaze at (200, 200).
    # Because of the +50 bias, the corrected output should be (250, 250)
    sys.controller.gaze_cb(make_gaze(200.0, 200.0, 5, 0))

    corrected = sys.corrected_gaze_msgs[-1]
    assert corrected.point.x == pytest.approx(250.0)
    assert corrected.point.y == pytest.approx(250.0)


def test_model_graduation_linear_integration():
    """
    Simulates filling up spatial bins to force the Learner to graduate from
    Bias to Linear. Verifies the Controller correctly interprets the Linear
    coefficients.
    """
    sys = IntegrationSystem()

    # Lower trigger for Linear model so we hit it quickly
    sys.learner.competitors[2].cfg["trigger_bins"] = 2

    # 1st Bin (Top Left)
    sys.trigger_interaction(btn_x=100, btn_y=100, gaze_x=90, gaze_y=90, t_sec=1)
    assert sys.learner.active_idx == 1  # Still on Bias

    # 2nd Bin (Bottom Right)
    sys.trigger_interaction(btn_x=1000, btn_y=800, gaze_x=950, gaze_y=750, t_sec=5)

    # 3rd Bin (Middle) - Triggers graduation
    sys.trigger_interaction(btn_x=500, btn_y=400, gaze_x=480, gaze_y=380, t_sec=10)

    # Learner should have switched to Linear (idx=2)
    assert sys.learner.active_idx == 2, "Learner did not graduate to Linear model."
    assert (
        sys.controller.model_type == CalibrationModel.TYPE_LINEAR
    ), "Controller did not receive Linear state."

    # Ensure coeffs_x[3] (linear X scale) and coeffs_x[5] (bias) are populated
    # (Checking non-zero proves the controller parsed the ROS msg correctly)
    assert sys.controller.coeffs_x[3] != 0.0
    assert sys.controller.coeffs_x[5] != 0.0


def test_joy_reset_propagation():
    """
    Ensures that a user pressing Reset on the Joy controller resets the Learner,
    which immediately publishes a blank model, resetting the Controller.
    """
    sys = IntegrationSystem()

    # Create an initial offset (Bias +100)
    sys.trigger_interaction(btn_x=200, btn_y=200, gaze_x=100, gaze_y=100, t_sec=1)
    assert sys.controller.coeffs_x[5] == pytest.approx(100.0)

    # Simulate Joy Reset (Button 'A' / Index 0)
    joy_msg = Joy()
    joy_msg.buttons = [0] * 15
    joy_msg.buttons[sys.learner.resume_btn_idx] = 1

    sys.learner.joy_cb(joy_msg)

    # Process the model update through the mock network
    sys.flush_network()

    # The controller should have received an immediate blank model
    assert (
        sys.controller.coeffs_x[5] == 0.0
    ), "Controller bias was not reset after Joy command."
    assert (
        sys.controller.coeffs_y[5] == 0.0
    ), "Controller bias was not reset after Joy command."

    # Ensure next gaze is uncorrected
    sys.corrected_gaze_msgs.clear()
    sys.controller.gaze_cb(make_gaze(500.0, 500.0, 5, 0))
    assert sys.corrected_gaze_msgs[-1].point.x == 500.0


def test_compensation_toggle():
    """
    Tests the `compensation_active` parameter in the Controller.
    Even if the Learner sends a model, the Controller should bypass it if disabled.
    """
    sys = IntegrationSystem()

    # Generate +100 bias model
    sys.trigger_interaction(btn_x=200, btn_y=200, gaze_x=100, gaze_y=100, t_sec=1)

    # Turn OFF compensation
    sys.controller.set_parameters(
        [rclpy.parameter.Parameter("compensation_active", value=False)]
    )

    sys.corrected_gaze_msgs.clear()
    sys.controller.gaze_cb(make_gaze(100.0, 100.0, 5, 0))

    # Gaze should remain 100.0 (no +100 correction applied)
    assert sys.corrected_gaze_msgs[-1].point.x == 100.0
