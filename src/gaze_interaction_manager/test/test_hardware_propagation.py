import sys
import os
# Point to your 'src' folder so PyTest can import your nodes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

# Now you can import your classes! (Adjust the filename to match yours)
from gaze_controller import GazeController
from aruco_detector import ArucoDetectorNode
from button_finder import DiegeticButtonPublisher


import rclpy
import pytest
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from diegetic_transform_engine.msg import DiegeticButton2DArray
from rclpy.executors import SingleThreadedExecutor
import time

class PipelineAuditor(Node):
    def __init__(self):
        super().__init__('pipeline_auditor')
        self.image_pub = self.create_publisher(CompressedImage, 'pupil_glasses/front_image', 10)
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

def test_hardware_time_propagation():
    """Verifies that the CV pipeline does not overwrite the hardware timestamp"""
    executor = SingleThreadedExecutor()
    auditor = PipelineAuditor()
    # Assuming you have instantiated your Aruco and Button nodes here
    aruco_node = ArucoDetectorNode()
    button_node = DiegeticButtonPublisher()
    
    executor.add_node(auditor)
    executor.add_node(aruco_node)
    executor.add_node(button_node)

    # 1. Create a dummy image with a highly specific "Hardware" timestamp
    msg = CompressedImage()
    msg.header.stamp.sec = 9999    # Obvious fake hardware time
    msg.header.stamp.nanosec = 123456789
    
    # 2. Publish and process
    auditor.image_pub.publish(msg)
    
    # Spin to allow callbacks to process
    timeout = time.time() + 2.0
    while auditor.received_stamp is None and time.time() < timeout:
        executor.spin_once(timeout_sec=0.1)

    # 3. Assert the header made it through the whole CV pipeline untouched
    assert auditor.received_stamp is not None, "Pipeline dropped the message!"
    assert auditor.received_stamp.sec == 9999, "Hardware SECONDS were overwritten by host time!"
    assert auditor.received_stamp.nanosec == 123456789, "Hardware NANOSECONDS were overwritten!"