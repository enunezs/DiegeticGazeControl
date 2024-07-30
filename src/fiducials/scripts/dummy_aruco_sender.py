#!/usr/bin/env python3

# To run
"""
ros2 run fiducials aruco_detect.py --ros-args --params-file config/params.yaml
"""

# Core ROS dependencies
import rclpy
from rclpy.node import Node

# Standard library imports
from math import sqrt
import numpy as np

# Third-party imports
from cv2 import (
    aruco,
    destroyAllWindows,
    drawFrameAxes,
    Rodrigues,
)
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image

# Local application imports
from fiducials.msg import (
    Fiducial,
    FiducialArray,
    FiducialTransform,
    FiducialTransformArray,
)


## Make a node to send a single fixed aruco marker fixed in front of the user.
class DummyArucoSender(Node):
    def __init__(self):
        super().__init__("dummy_aruco_sender")
        self.fiducial_transform_pub = self.create_publisher(
            FiducialTransformArray, "/fiducial_transforms", 10
        )
        self.create_timer(1 / 30, self.send_dummy_transform)

    def send_dummy_transform(self):

        fiducial_transform = FiducialTransform()
        fiducial_transform.fiducial_id = 5
        fiducial_transform.transform.translation.x = -0.0
        fiducial_transform.transform.translation.y = -0.0
        fiducial_transform.transform.translation.z = 0.060
        fiducial_transform.transform.rotation.x = 1.0
        fiducial_transform.transform.rotation.y = 0.0
        fiducial_transform.transform.rotation.z = 0.0
        fiducial_transform.transform.rotation.w = 0.0

        new_msg = FiducialTransformArray()
        new_msg.header.frame_id = "/fixed_front"
        new_msg.header.stamp = self.get_clock().now().to_msg()
        new_msg.transforms.append(fiducial_transform)
        self.fiducial_transform_pub.publish(new_msg)
        # self.get_logger().info("Published Dummy Aruco Transform")


def main():
    rclpy.init()  # Initialize ROS DDS
    aruco_publisher = DummyArucoSender()
    print("Aruco Detection Publisher Node is Running...")

    try:
        rclpy.spin(aruco_publisher)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        aruco_publisher.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == "__main__":
    main()
