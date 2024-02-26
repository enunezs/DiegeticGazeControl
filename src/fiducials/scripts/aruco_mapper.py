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

from scipy.spatial.transform import Rotation  # IMPORTANT, USES x,y,z,w
import numpy as np


class MarkerTransformNode(Node):
    def __init__(self):
        super().__init__("marker_transform_node")
        self.get_logger().info("Aruco Detection Publisher Node is Running...")

        # Initialize transform broadcasters
        self.static_broadcaster = StaticTransformBroadcaster(self)
        self.dynamic_broadcaster = TransformBroadcaster(self)

        # load parameter for root frame, set default to "camera"
        self.declare_parameter("root_frame", "camera")
        self.root_frame = self.get_parameter("root_frame").value

        # Publish static transforms
        # Load fixed relationship between a marker and another frame on self.transforms_relationships
        self.declare_parameter("config_file_path", "src/fiducials/config/mapping.csv")
        self.config_file_path = self.get_parameter("config_file_path").value
        self.transforms_relationships = self.load_fixed_transforms(
            self.config_file_path
        )
        self.publish_static_transforms()

        # Publish dynamic transforms
        # Initialize subscription to fiducial_transforms
        self.subscription = self.create_subscription(
            FiducialTransformArray,
            "fiducial_transforms",
            self.update_dynamic_transforms,
            10,
        )

    def publish_static_transforms(self):
        for marker_id in self.transforms_relationships:
            static_transform_stamped = TransformStamped()
            static_transform_stamped.header.stamp = self.get_clock().now().to_msg()

            parent_frame = self.transforms_relationships[marker_id]["parent"]

            # Markers are children to other components
            static_transform_stamped.header.frame_id = parent_frame
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
            self.get_logger().info(
                "Published fixed transform for marker " + str(marker_id)
            )

    def update_dynamic_transforms(self, msg):

        for transform in msg.transforms:
            # only run if marker is id == 4
            if transform.fiducial_id != 5:
                continue

            # Markers should be parent to the camera.
            # TODO: If multiple, pool multiple to estimate position
            # TODO ARUCO SLAM

            # Collect inputs
            translation_to_marker = np.array(
                [
                    [
                        transform.transform.translation.x,
                        transform.transform.translation.y,
                        transform.transform.translation.z,
                    ]
                ]
            )
            rotation_to_marker = Rotation.from_quat(
                [
                    transform.transform.rotation.x,
                    transform.transform.rotation.y,
                    transform.transform.rotation.z,
                    transform.transform.rotation.w,
                ]
            )

            # To matrix...
            camera_to_marker = np.concatenate(
                (rotation_to_marker.as_matrix(), translation_to_marker.T), axis=1
            )
            camera_to_marker = np.concatenate(
                (camera_to_marker, [[0, 0, 0, 1]]), axis=0
            )

            # Invert matrix
            marker_to_camera = np.linalg.inv(camera_to_marker)

            # Extract translation and rotation
            translation_to_camera = marker_to_camera[0:3, 3]
            rotation_to_camera = Rotation.from_matrix(marker_to_camera[0:3, 0:3])

            dynamic_transform = TransformStamped()
            dynamic_transform.header.stamp = self.get_clock().now().to_msg()
            dynamic_transform.header.frame_id = "marker_" + str(transform.fiducial_id)
            dynamic_transform.child_frame_id = self.root_frame

            # dynamic_transform.header.frame_id = 'j2n6s300_link_6_target'

            dynamic_transform.transform.translation.x = translation_to_camera[0]
            dynamic_transform.transform.translation.y = translation_to_camera[1]
            dynamic_transform.transform.translation.z = translation_to_camera[2]

            rotation_to_camera = rotation_to_camera.as_quat()
            dynamic_transform.transform.rotation.x = rotation_to_camera[0]
            dynamic_transform.transform.rotation.y = rotation_to_camera[1]
            dynamic_transform.transform.rotation.z = rotation_to_camera[2]
            dynamic_transform.transform.rotation.w = rotation_to_camera[3]

            self.dynamic_broadcaster.sendTransform(dynamic_transform)
            """self.get_logger().info(
                "Published dynamic transform for marker " + str(transform.fiducial_id)
            )"""

    def load_fixed_transforms(self, path):
        self.get_logger().info("Loading marker to button map...")
        transforms_relationships = {}
        with open(path, "r") as csvfile:
            lines = csvfile.readlines()
            for line in lines[1:]:  # Skip header
                parts = line.split(",")

                parent_frame = str((parts[0]))
                marker_id = int(parts[1])
                marker_transform = [float(i) for i in parts[2:5]]  # mm
                marker_rotation = [
                    float(i) for i in parts[5:8]
                ]  # mm # Change to roll pitch yaw

                # ! Works, but not in the right order, seems like xzy
                marker_rotation = Rotation.from_euler(
                    "xyz", marker_rotation, degrees=True
                ).as_quat()

                transforms_relationships[marker_id] = {
                    "parent": parent_frame,
                    "translation": marker_transform,
                    "rotation": marker_rotation,
                }
                self.get_logger().info(
                    "Loaded transform for marker "
                    + str(marker_id)
                    + " to "
                    + parent_frame
                )
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

    try:
        rclpy.spin(marker_transform_node)
    except KeyboardInterrupt:
        destroyAllWindows()
        marker_transform_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
