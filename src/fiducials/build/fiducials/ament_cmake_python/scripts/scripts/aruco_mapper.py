#!/usr/bin/env python3

# To run
"""
ros2 run fiducials aruco_mapper.py --ros-args --params-file config/params.yaml
"""

# Core ROS dependencies
import rclpy
from rclpy.node import Node

# Standard library imports
from math import sqrt
import numpy as np
import tf2_ros
import tf2_geometry_msgs

# Third-party imports
from cv2 import aruco, destroyAllWindows, drawFrameAxes, Rodrigues
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image
from tf_transformations import quaternion_from_matrix

# Local application imports
from fiducials.msg import (
    Fiducial,
    FiducialArray,
    FiducialTransform,
    FiducialTransformArray,
)
from geometry_msgs.msg import Transform
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
from tf2_ros.transform_broadcaster import TransformBroadcaster

from geometry_msgs.msg import TransformStamped

import csv


class MarkerTransformNode(Node):
    def __init__(self):
        super().__init__("marker_transform_node")

        # Initialize transform broadcasters
        self.static_broadcaster = StaticTransformBroadcaster(self)
        self.dynamic_broadcaster = TransformBroadcaster(self)

        # Load fixed relationship between a marker and another frame on self.transforms_relationships
        self.transforms_relationships = self.load_fixed_transforms()
        self.publish_static_transforms()

        self.subscription = self.create_subscription(
            FiducialTransformArray,
            "fiducial_transforms",
            self.update_dynamic_transforms,
            10,
        )

    def update_dynamic_transforms(self, msg):
        for transform in msg.transforms:
            dynamic_transform = TransformStamped()

            dynamic_transform.header.stamp = self.get_clock().now().to_msg()
            dynamic_transform.header.frame_id = "marker_" + str(transform.fiducial_id)
            dynamic_transform.child_frame_id = "camera"

            self.get_logger().info(
                "Publishing transform for marker " + str(transform.fiducial_id)
            )
            dynamic_transform.transform.translation.x = (
                -transform.transform.translation.x
            )
            dynamic_transform.transform.translation.y = (
                -transform.transform.translation.y
            )
            dynamic_transform.transform.translation.z = (
                -transform.transform.translation.z
            )
            dynamic_transform.transform.rotation.x = transform.transform.rotation.x
            dynamic_transform.transform.rotation.y = transform.transform.rotation.y
            dynamic_transform.transform.rotation.z = transform.transform.rotation.z
            dynamic_transform.transform.rotation.w = transform.transform.rotation.w
            self.dynamic_broadcaster.sendTransform(dynamic_transform)
            self.get_logger().info(
                "Published transform for marker " + str(transform.fiducial_id)
            )

    def publish_static_transforms(self):
        for marker_id in self.transforms_relationships:
            static_transform_stamped = TransformStamped()

            print("Publishing transform for marker " + str(marker_id))
            static_transform_stamped.header.stamp = self.get_clock().now().to_msg()
            static_transform_stamped.header.frame_id = self.transforms_relationships[
                marker_id
            ]["parent"]
            static_transform_stamped.child_frame_id = "marker_" + str(marker_id)
            static_transform_stamped.transform.translation.x = (
                self.transforms_relationships[marker_id]["translation"][0]
            )
            static_transform_stamped.transform.translation.y = (
                self.transforms_relationships[marker_id]["translation"][1]
            )
            static_transform_stamped.transform.translation.z = (
                self.transforms_relationships[marker_id]["translation"][2]
            )
            static_transform_stamped.transform.rotation.x = (
                self.transforms_relationships[marker_id]["rotation"][0]
            )
            static_transform_stamped.transform.rotation.y = (
                self.transforms_relationships[marker_id]["rotation"][1]
            )
            static_transform_stamped.transform.rotation.z = (
                self.transforms_relationships[marker_id]["rotation"][2]
            )
            static_transform_stamped.transform.rotation.w = (
                self.transforms_relationships[marker_id]["rotation"][3]
            )
            self.static_broadcaster.sendTransform(static_transform_stamped)
            self.get_logger().info("Published transform for marker " + str(marker_id))

    def load_fixed_transforms(self):
        print("Loading marker to button map...")
        transforms_relationships = {}
        with open("config/mapping.csv", "r") as csvfile:
            lines = csvfile.readlines()
            for line in lines[1:]:  # Skip header
                parts = line.split(",")

                parent_frame = str((parts[0]))
                marker_id = int(parts[1])
                marker_transform = [float(i) for i in parts[2:5]]  # mm
                marker_rotation = [float(i) for i in parts[5:9]]  # mm

                transforms_relationships[marker_id] = {
                    "parent": parent_frame,
                    "translation": marker_transform,
                    "rotation": marker_rotation,
                }
                self.get_logger().info("Loaded transform for marker " + str(marker_id))
                self.get_logger().info(
                    "Translation: "
                    + str(marker_transform)
                    + " Rotation: "
                    + str(marker_rotation)
                )
        return transforms_relationships


def main(args=None):
    rclpy.init(args=args)
    marker_transform_node = MarkerTransformNode()
    print("Aruco Detection Publisher Node is Running...")

    try:
        rclpy.spin(marker_transform_node)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        destroyAllWindows()
        marker_transform_node.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == "__main__":
    main()
