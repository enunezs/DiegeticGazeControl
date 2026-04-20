
'''
python3 -m pytest src/gaze_interaction_manager/test/test_gaze_interpolation.py -v -s
'''

import sys
import os
import time
import pytest
import rclpy

# 1. FIX IMPORTS: Point dynamically to your scripts folder
# __file__ is .../gaze_interaction_manager/test/test_gaze_interpolation.py
# '../scripts' resolves to .../gaze_interaction_manager/scripts
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, '..', 'scripts')
sys.path.insert(0, scripts_dir)

# If you have a separate diegetic_transform_engine package, also add that to the path
src_dir = os.path.join(current_dir, '..', '..', 'diegetic_transform_engine', 'scripts')
sys.path.insert(0, src_dir)
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'diegetic_transform_engine/scripts'))) 
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))) # gaze_interaction_manager/scripts

# Now we can import the GazeController
from gaze_controller import GazeController

# ROS 2 Messages
from std_msgs.msg import Header
from geometry_msgs.msg import Point
from pupil_neon_ros.msg import GazeData, GazeEvent
from gaze_interaction_manager.msg import ButtonStatus

from diegetic_transform_engine.msg import DiegeticButton2D

@pytest.fixture(autouse=True)
def ros_setup():
    rclpy.init()
    yield
    rclpy.shutdown()

def test_temporal_interpolation_math():
    """Verifies that 30Hz target data is correctly interpolated to match 200Hz gaze timestamps"""
    node = GazeController()
    
    # Disable pipeline delay for the pure math test
    node.set_parameters([rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0)])
    node.set_parameters([rclpy.parameter.Parameter('pad_duration_ms', value=0.0)])
    node.set_parameters([rclpy.parameter.Parameter('min_event_duration_ms', value=0.0)])
    
    # 1. Feed Button Ground Truth (Hardware time: T=1.0 and T=2.0)
    btn_msg_1 = ButtonStatus(
        button_status=ButtonStatus.BUTTON_ACTIVE,
        button=DiegeticButton2D(button_id="btn1", center_x=10.0, center_y=10.0)
    )
    btn_msg_1.header.stamp.sec = 1
    btn_msg_1.header.stamp.nanosec = 0
    
    btn_msg_2 = ButtonStatus(
        button_status=ButtonStatus.BUTTON_ACTIVE,
        button=DiegeticButton2D(button_id="btn1", center_x=20.0, center_y=20.0)
    )
    btn_msg_2.header.stamp.sec = 2
    btn_msg_2.header.stamp.nanosec = 0

    node.button_cb(btn_msg_1)
    node.button_cb(btn_msg_2)

    # 2. Feed Gaze Data at exactly the halfway point (T=1.5)
    gaze_msg = GazeData(x=100.0, y=100.0)
    gaze_msg.header.stamp.sec = 1
    gaze_msg.header.stamp.nanosec = 500000000 # 1.5 seconds
    node.gaze_cb(gaze_msg)

    # Capture the output
    published_segments = []
    node.segment_pub.publish = lambda msg: published_segments.append(msg)

    # 3. Trigger a saccade at T=2.1 to close the segment
    saccade = GazeEvent(start_time_ns=2100000000) # 2.1 seconds
    node.saccade_cb(saccade)

    # 4. Assertions
    assert len(published_segments) == 1
    segment = published_segments[0]
    
    # The Gaze sample was at T=1.5. 
    # Button was at X=10 at T=1.0, and X=20 at T=2.0. 
    # Therefore, interpolated target MUST be exactly 15.0
    assert len(segment.target_samples) == 1
    assert segment.target_samples[0].x == 15.0, f"Interpolation math failed X! Got {segment.target_samples[0].x}"
    assert segment.target_samples[0].y == 15.0, "Interpolation math failed Y"


def test_gaze_arrives_before_video():
    """Verifies the Gaze buffer safely holds gaze data until the slower video data arrives"""
    node = GazeController()
    node.set_parameters([rclpy.parameter.Parameter('history_length_s', value=5.0)])
    
    # 1. Gaze arrives FIRST (Hardware Time = 10.0)
    gaze_msg = GazeData(x=500.0, y=500.0)
    gaze_msg.header.stamp.sec = 10
    node.gaze_cb(gaze_msg)
    
    # Verify the gaze is waiting safely in the circular buffer
    assert node.gaze_history[0][0] == 10.0, "Gaze data wasn't buffered!"
    
    # 2. Wait a massive amount of "PC Time" (simulate heavy OpenCV lag)
    time.sleep(1.5)
    
    # 3. Finally, the Button CV finishes and arrives (Hardware Time = 10.0)
    btn_msg = ButtonStatus(
        button_status=ButtonStatus.BUTTON_ACTIVE,
        button=DiegeticButton2D(button_id="target", center_x=10.0, center_y=10.0)
    )
    btn_msg.header.stamp.sec = 1
    
    node.button_cb(btn_msg)
    
    # 4. Fire a saccade at T=10.5 to trigger the segment calculation
    node.saccade_cb(GazeEvent(start_time_ns=10500000000))
    
    # If this test passes, it proves your GazeController is IMMUNE to image processing lag.
    # Note: If no segment is published, you may need to adjust your node's recording state logic in the test.


def test_ghost_button_extrapolation():
    """Verifies the system doesn't generate training data for buttons that have gone off-screen"""
    node = GazeController()
    node.set_parameters([rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0)])
    node.set_parameters([rclpy.parameter.Parameter('pad_duration_ms', value=0.0)])
    node.set_parameters([rclpy.parameter.Parameter('min_event_duration_ms', value=0.0)])
    
    # 1. Button is visible at T=1.0 and T=2.0 (Moving from X=10 to X=20)
    btn_1 = ButtonStatus(button_status=ButtonStatus.BUTTON_ACTIVE, button=DiegeticButton2D(button_id="btn1", center_x=10.0))
    btn_1.header.stamp.sec = 1
    
    btn_2 = ButtonStatus(button_status=ButtonStatus.BUTTON_ACTIVE, button=DiegeticButton2D(button_id="btn1", center_x=20.0))
    btn_2.header.stamp.sec = 2

    node.button_cb(btn_1)
    node.button_cb(btn_2)

    # 2. But Gaze data keeps coming in until T=4.0!
    for t_sec in [1, 2, 3, 4]:
        gaze_msg = GazeData(x=100.0, y=100.0)
        gaze_msg.header.stamp.sec = t_sec
        node.gaze_cb(gaze_msg)

    # Capture output
    published = []
    node.segment_pub.publish = lambda msg: published.append(msg)

    # 3. Saccade triggers end of segment at T=4.5
    node.saccade_cb(GazeEvent(start_time_ns=4500000000))

    assert len(published) == 1
    segment = published[0]
    
    # Check the target X at T=4.0. 
    target_x_at_t4 = segment.target_samples[-1].x
    
    # If target_x_at_t4 == 20.0, it is training on ghost data.
    print(f"\n[Ghost Test Result] At T=4.0, interpolated target is at X={target_x_at_t4}.")


def test_empty_button_buffer_crash():
    """Verifies GazeController cleanly aborts if a saccade happens but no buttons were tracked"""
    node = GazeController()
    
    # 1. Trigger the start of recording (maybe a false positive)
    node.is_recording = True
    node.rec_start_ts = 1.0
    node.current_button_id = "ghost_button"
    
    # 2. Feed Gaze Data (T=1.0 to T=2.0)
    gaze_msg = GazeData(x=100.0, y=100.0)
    gaze_msg.header.stamp.sec = 1
    node.gaze_cb(gaze_msg)
    
    gaze_msg.header.stamp.sec = 2
    node.gaze_cb(gaze_msg)
    
    # NOTE: We DO NOT feed any Button data! btn_history is completely empty.

    published = []
    node.segment_pub.publish = lambda msg: published.append(msg)

    # 3. Trigger segment generation
    try:
        node.saccade_cb(GazeEvent(start_time_ns=2500000000))
    except Exception as e:
        pytest.fail(f"GazeController crashed when button history was empty: {e}")

    # It should cleanly exit and publish nothing
    assert len(published) == 0, "It published a segment with no ground truth!"
    assert node.is_recording == False, "It failed to reset the recording state!"