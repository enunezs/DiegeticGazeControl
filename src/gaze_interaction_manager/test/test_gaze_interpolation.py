import sys
import os
# Point to your 'src' folder so PyTest can import your nodes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Now you can import your classes! (Adjust the filename to match yours)
from gaze_controller import GazeController
from aruco_detector import ArucoDetectorNode
from button_finder import DiegeticButtonPublisher


import rclpy
from std_msgs.msg import Header
from geometry_msgs.msg import Point
from pupil_neon_ros.msg import GazeData, GazeEvent
from gaze_interaction_manager.msg import ButtonStatus, DiegeticButton2D
# Import your GazeController
# from gaze_controller_file import GazeController 

def test_temporal_interpolation_math():
    rclpy.init()
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
    assert segment.target_samples[0].x == 15.0, "Interpolation math failed X"
    assert segment.target_samples[0].y == 15.0, "Interpolation math failed Y"

    rclpy.shutdown()