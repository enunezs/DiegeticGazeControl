
'''
python3 -m pytest src/gaze_interaction_manager/test/test_hardware_propagation.py -v -s
'''

import sys
import os
# Point to your 'src' folder so PyTest can import your nodes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'diegetic_transform_engine/scripts'))) 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))) # gaze_interaction_manager/scripts

# Now you can import your classes! (Adjust the filename to match yours)
# from gaze_interaction_manager import scripts.gaze_controller as GazeController
# from diegetic_transform_engine import aruco_detector as ArucoDetectorNode
# from diegetic_transform_engine import DiegeticButtonPublisher


import rclpy

import pytest
import time
import cv2
import numpy as np

from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor

from sensor_msgs.msg import CompressedImage, CameraInfo
from diegetic_transform_engine.msg import DiegeticButton2DArray

import time

# Add to top of file:
import tf2_ros

# Add to PipelineAuditor __init__:

class PipelineAuditor(Node):
    def __init__(self):
        super().__init__('pipeline_auditor')
        self.image_pub = self.create_publisher(CompressedImage, 'pupil_glasses/front_image', 5)

        self.camera_calib_pub = self.create_publisher(
            CameraInfo, "pupil_glasses/front_camera/camera_info", 10
        )
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.button_sub = self.create_subscription(
            DiegeticButton2DArray, '/diegetic_buttons_2d', self.button_cb, 10)
        self.received_stamp = None

    def button_cb(self, msg):
        self.received_stamp = msg.header.stamp

@pytest.fixture(autouse=True)
def ros_setup():
    rclpy.init()
    yield
    rclpy.shutdown()

# TEST: Is the hardware tiemstamp propagated properly from glasses image to the end of the button identification?
def test_hardware_time_propagation():
    """Verifies that the CV pipeline does not overwrite the hardware timestamp"""
    executor = SingleThreadedExecutor()
    auditor = PipelineAuditor()
    executor.add_node(auditor)

    # Wait a moment for ROS 2 to connect the publisher to the live nodes
    start_time = time.time()
    while time.time() - start_time < 1.0:
        executor.spin_once(timeout_sec=0.1)

    # 0. Prepatation: Publish a dummy camera calibration (some nodes won't process images without it)
    calib_msg = CameraInfo()
    calib_msg.width = 100
    calib_msg.height = 100
    auditor.camera_calib_pub.publish(calib_msg)

    # wait a moment for the calibration to propagate
    start_time = time.time()
    while time.time() - start_time < 1.0:
        executor.spin_once(timeout_sec=0.1)

    # 1. Create a dummy image with a highly specific "Hardware" timestamp
    msg = CompressedImage()
    msg.header.stamp.sec = 9876    # Obvious fake hardware time
    msg.header.stamp.nanosec = 123456789
    
    # Create a tiny blank image so cv_bridge doesn't crash the Aruco node
    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, compressed = cv2.imencode('.jpg', fake_img)
    msg.data = compressed.tobytes()
    msg.format = "jpeg"

    # 2. Publish and process
    auditor.image_pub.publish(msg)

    # Spin to allow the live nodes to process the image and send it back
    timeout = time.time() + 3.0
    while auditor.received_stamp is None and time.time() < timeout:
        executor.spin_once(timeout_sec=0.1)

    # 3. Assert the header made it through
    assert auditor.received_stamp is not None, "Pipeline dropped the message! (Are your nodes running?)"
    assert auditor.received_stamp.sec == 9876, f"Hardware SECONDS overwritten! Got {auditor.received_stamp.sec}"
    assert auditor.received_stamp.nanosec == 123456789, "Hardware NANOSECONDS overwritten!"

def test_burst_queue_saturation():
    """Verifies that a rapid burst of frames doesn't result in dropped data due to queue limits"""
    executor = SingleThreadedExecutor()
    auditor = PipelineAuditor()
    executor.add_node(auditor)

    # Setup calibration...
    calib_msg = CameraInfo(width=100, height=100)
    auditor.camera_calib_pub.publish(calib_msg)
    
    start_time = time.time()
    while time.time() - start_time < 0.5:
        executor.spin_once(timeout_sec=0.1)

    auditor.received_stamps_list = [] # Create a list to hold multiple stamps
    
    def collecting_cb(msg):
        auditor.received_stamps_list.append(msg.header.stamp.sec)
    
    # Temporarily override the callback for this test
    auditor.button_sub.callback = collecting_cb

    # Fire 5 frames as fast as possible!
    burst_size = 5
    for i in range(burst_size):
        msg = CompressedImage()
        msg.header.stamp.sec = 1000 + i # Timestamps 1000, 1001, 1002...
        
        fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, compressed = cv2.imencode('.jpg', fake_img)
        msg.data = compressed.tobytes()
        msg.format = "jpeg"
        auditor.image_pub.publish(msg)

    # Give the CV pipeline a few seconds to chew through the burst
    timeout = time.time() + 5.0
    while len(auditor.received_stamps_list) < burst_size and time.time() < timeout:
        executor.spin_once(timeout_sec=0.1)

    # Assertions
    assert len(auditor.received_stamps_list) == burst_size, \
        f"Pipeline dropped frames! Sent {burst_size}, but only {len(auditor.received_stamps_list)} made it through. Check your QoS queue sizes!"
    

def test_out_of_order_propagation():
    """Verifies the pipeline doesn't crash or reject stale data arriving late"""
    executor = SingleThreadedExecutor()
    auditor = PipelineAuditor()
    executor.add_node(auditor)

    # Setup calibration...
    auditor.camera_calib_pub.publish(CameraInfo(width=100, height=100))
    time.sleep(0.5)

    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, compressed = cv2.imencode('.jpg', fake_img)

    # Publish NEW frame first (T=2000)
    msg_new = CompressedImage(format="jpeg", data=compressed.tobytes())
    msg_new.header.stamp.sec = 2000
    auditor.image_pub.publish(msg_new)

    # Process it
    t_end = time.time() + 1.0
    while time.time() < t_end: executor.spin_once(timeout_sec=0.1)

    # Now publish OLD frame (T=1000)
    msg_old = CompressedImage(format="jpeg", data=compressed.tobytes())
    msg_old.header.stamp.sec = 1000
    auditor.image_pub.publish(msg_old)

    # Process it
    auditor.received_stamp = None # Reset
    t_end = time.time() + 2.0
    while auditor.received_stamp is None and time.time() < t_end: 
        executor.spin_once(timeout_sec=0.1)

    # Did the old frame make it through?
    assert auditor.received_stamp is not None, "Pipeline silently dropped the out-of-order frame!"
    assert auditor.received_stamp.sec == 1000, "Pipeline overwrote the old timestamp!"



def test_tf_hardware_time_expiration():
    """Verifies if deeply delayed hardware time causes TF lookup failures"""
    executor = SingleThreadedExecutor()
    auditor = PipelineAuditor()
    executor.add_node(auditor)

    # Publish calibration...
    auditor.camera_calib_pub.publish(CameraInfo(width=100, height=100))
    
    # 1. Get current Host PC time
    now_unix = time.time()
    
    # 2. Simulate a hardware clock that is exactly 20 seconds behind the PC
    hardware_time_sec = int(now_unix - 20.0)

    # Create image
    msg = CompressedImage()
    msg.header.stamp.sec = hardware_time_sec
    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, compressed = cv2.imencode('.jpg', fake_img)
    msg.data = compressed.tobytes()
    msg.format = "jpeg"

    auditor.image_pub.publish(msg)

    # Process for a moment
    t_end = time.time() + 2.0
    while time.time() < t_end: executor.spin_once(timeout_sec=0.1)

    # 3. Attempt to look up the TF transform at that exact hardware time!
    try:
        # Looking up standard camera frame to marker.
        # (This relies on your Aruco node publishing a TF. Since the image is black, 
        # it might not find a marker. You may need to inject a real marker image for this specific test!)
        
        ros_time = rclpy.time.Time(seconds=hardware_time_sec)
        
        # We expect this to fail if tf2 dropped it due to being >10 seconds old
        transform = auditor.tf_buffer.lookup_transform(
            'camera_optical_frame',
            'aruco_78', # Assuming this is a standard ID
            ros_time,
            timeout=rclpy.duration.Duration(seconds=1.0)
        )
        assert transform is not None
        
    except tf2_ros.ExtrapolationException as e:
        pytest.fail(f"TF Failed! The hardware time was too old and TF deleted it: {e}")
    except tf2_ros.LookupException as e:
        # If the image was black, Aruco didn't publish a TF, which throws this. 
        # TODO: To complete this test, load a real JPEG of an ArUco marker instead of np.zeros
        pass

def test_blinking_marker_timeout():
    """Verifies that buttons survive short frame drops but are deleted after the timeout"""
    executor = SingleThreadedExecutor()
    auditor = PipelineAuditor()
    executor.add_node(auditor)

    auditor.camera_calib_pub.publish(CameraInfo(width=100, height=100))
    
    # Send Frame 1 (T=1000)
    msg = CompressedImage(format="jpeg")
    msg.header.stamp.sec = 1000
    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, compressed = cv2.imencode('.jpg', fake_img)
    msg.data = compressed.tobytes()
    auditor.image_pub.publish(msg)

    # Spin to process
    t_end = time.time() + 1.0
    while time.time() < t_end: executor.spin_once(timeout_sec=0.1)

    assert auditor.received_stamp is not None, "Failed to receive first frame"
    
    # Now simulate a frame drop! We send the NEXT frame with a timestamp 0.4 seconds later.
    # Because your button_timeout is 0.5s, the button SHOULD SURVIVE.
    auditor.received_stamp = None
    msg.header.stamp.sec = 1000
    msg.header.stamp.nanosec = 400000000 # +0.4 seconds
    auditor.image_pub.publish(msg)

    t_end = time.time() + 1.0
    while auditor.received_stamp is None and time.time() < t_end: 
        executor.spin_once(timeout_sec=0.1)

    assert auditor.received_stamp is not None, "Button was incorrectly deleted after only 0.4s!"

    # Now simulate a LONG drop (0.6 seconds). 
    # T = 1000.4 + 0.6 = 1001.0
    auditor.received_stamp = None
    msg.header.stamp.sec = 1001
    msg.header.stamp.nanosec = 0
    auditor.image_pub.publish(msg)

    # Note: To fully test this, you'd check the internal state of `button_statuses` 
    # TODO in the GazeInteractionNode to ensure the old button was purged and a "new" one was created.
    # TODO: Add the top of interpolationt test to explore
    


   

def test_filter_identical_timestamps():
    """Verifies the 1Euro filter doesn't crash if two frames have the exact same hardware time"""
    executor = SingleThreadedExecutor()
    auditor = PipelineAuditor()
    executor.add_node(auditor)

    auditor.camera_calib_pub.publish(CameraInfo(width=100, height=100))
    time.sleep(0.5)

    # 1. First frame (T=5000)
    msg = CompressedImage()
    msg.header.stamp.sec = 5000
    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, compressed = cv2.imencode('.jpg', fake_img)
    msg.data = compressed.tobytes()
    msg.format = "jpeg"
    auditor.image_pub.publish(msg)

    # 2. Second frame (EXACT SAME TIMESTAMP, T=5000)
    # This often causes a DivideByZero error in custom temporal filters
    auditor.image_pub.publish(msg)

    # Spin to see if the node survives and processes it
    t_end = time.time() + 2.0
    while auditor.received_stamp is None and time.time() < t_end:
        executor.spin_once(timeout_sec=0.1)

    assert auditor.received_stamp is not None, "Pipeline crashed when given identical timestamps!"