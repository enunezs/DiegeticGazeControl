#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
import cv2
import numpy as np
import yaml
import os
from cv_bridge import CvBridge
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped, PoseStamped
from sensor_msgs.msg import Image, CompressedImage, CameraInfo
from std_msgs.msg import Header
from diegetic_transform_engine.msg import (
    MarkerArray,
    Marker,
)  # You might need to create this custom message
import tf_transformations

import traceback


class ArucoDetectorNode(Node):
    def __init__(self):
        super().__init__("aruco_detector")

        # Initialize CV bridge
        self.bridge = CvBridge()

        # Initialize TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)

        # Load configuration
        self.load_config()

        # Last known marker poses for temporary caching
        self.last_marker_poses = {}  # {marker_id: (PoseStamped, rclpy.time.Time)}

        # Initialize ArUco detector
        self.setup_aruco_detector()

        # Camera calibration parameters (will be updated from camera_info)
        self.camera_matrix = None
        self.dist_coeffs = None
        self.camera_info = None

        # QoS profiles
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=1,
        )

        # Subscribers
        self.image_sub = self.create_subscription(
            CompressedImage,
            "pupil_glasses/front_image",
            self.image_callback,
            sensor_qos,
        )

        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            "pupil_glasses/front_camera/camera_info",
            self.camera_info_callback,
            sensor_qos,
        )

        # Publishers
        self.aruco_marker_array_pub = self.create_publisher(
            MarkerArray, "aruco_markers", 10
        )
        self.marker_pose_pub = self.create_publisher(PoseStamped, "aruco_poses", 10)
        # TODO: Debug image publisher (optional)
        self.debug_image_pub = self.create_publisher(Image, "aruco_debug_image", 1)

        self.get_logger().info("ArUco detector node initialized")

    def load_config(self):
        # Declare ROS 2 parameters with default values
        self.declare_parameter("aruco_dict", "DICT_4X4_100")
        self.declare_parameter("marker_size", 0.044)  # meters
        self.declare_parameter("camera_frame", "camera_optical_frame")
        self.declare_parameter("world_frame", "world")
        self.declare_parameter("publish_tf", True)
        self.declare_parameter("publish_poses", True)
        self.declare_parameter("debug_images", True)
        # self.declare_parameter(
        #     "markers", {}
        # )  # marker_id: {'frame_id': 'marker_X', 'relative_to': 'transient'}
        self.declare_parameter("marker_persistence", 0.5)  # seconds

        # Load parameters into self.config
        self.config = {
            "aruco_dict": self.get_parameter("aruco_dict").value,
            "marker_size": self.get_parameter("marker_size").value,
            "camera_frame": self.get_parameter("camera_frame").value,
            "world_frame": self.get_parameter("world_frame").value,
            "publish_tf": self.get_parameter("publish_tf").value,
            "publish_poses": self.get_parameter("publish_poses").value,
            "debug_images": self.get_parameter("debug_images").value,
            "marker_persistence": self.get_parameter("marker_persistence").value,
            # "markers": self.get_parameter("markers").value,
        }

        self.marker_persistence = self.config.get("marker_persistence", 0.5)

    def create_default_config(self, config_path):
        """Create a default configuration file"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as file:
                yaml.dump(self.config, file, default_flow_style=False)
            self.get_logger().info(f"Created default config file at {config_path}")
        except Exception as e:
            self.get_logger().warn(f"Could not create config file: {e}")

    def setup_aruco_detector(self):
        """Initialize ArUco detector"""
        aruco_dict_name = self.config.get("aruco_dict", "DICT_4X4_100")
        if hasattr(cv2.aruco, aruco_dict_name):
            aruco_dict_id = getattr(cv2.aruco, aruco_dict_name)
            self.aruco_dict = cv2.aruco.Dictionary_get(aruco_dict_id)
        else:
            self.get_logger().warn(
                f"Unknown ArUco dictionary {aruco_dict_name}, using DICT_4X4_100"
            )
            self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)

        self.detector_params = cv2.aruco.DetectorParameters_create()
        self.marker_size = self.config.get("marker_size", 0.05)

    def camera_info_callback(self, msg):
        """Handle camera info messages"""
        self.get_logger().info("Camera calibration received", once=True)

        self.camera_info = msg
        self.camera_matrix = np.array(msg.k).reshape(3, 3)
        self.dist_coeffs = np.array(msg.d)

    def image_callback(self, msg):
        """Handle compressed image messages"""
        if self.camera_matrix is None:
            self.get_logger().warn("No camera calibration received yet")
            return
        # self.get_logger().info("Image received", throttle_duration_sec=1)

        try:
            # Convert compressed image to OpenCV format
            cv_image = self.bridge.compressed_imgmsg_to_cv2(msg, "bgr8")

            # Detect ArUco markers
            self.detect_markers(cv_image, msg.header)

        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")
            self.get_logger().error(traceback.format_exc())

    def detect_markers(self, image, header):
        """Detect ArUco markers and publish results"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(
            gray, self.aruco_dict, parameters=self.detector_params
        )
        rvecs = None
        tvecs = None

        detected_ids = set()
        marker_array = MarkerArray()
        marker_array.header = header
        marker_array.markers = []

        if ids is not None and len(ids) > 0:
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners, self.marker_size, self.camera_matrix, self.dist_coeffs
            )

            for i, marker_id in enumerate(ids.flatten()):
                rvec = rvecs[i][0]
                tvec = tvecs[i][0]

                rotation_matrix = cv2.Rodrigues(rvec)[0]
                quaternion = tf_transformations.quaternion_from_matrix(
                    np.vstack(
                        [np.hstack([rotation_matrix, [[0], [0], [0]]]), [0, 0, 0, 1]]
                    )
                )

                marker = Marker()
                marker.id = int(marker_id)
                marker.pose.position.x = float(tvec[0])
                marker.pose.position.y = float(tvec[1])
                marker.pose.position.z = float(tvec[2])
                marker.pose.orientation.x = quaternion[0]
                marker.pose.orientation.y = quaternion[1]
                marker.pose.orientation.z = quaternion[2]
                marker.pose.orientation.w = quaternion[3]

                marker_array.markers.append(marker)

                # Publish individual pose
                if self.config.get("publish_poses", True):
                    pose_msg = PoseStamped()
                    pose_msg.header = header
                    pose_msg.pose = marker.pose
                    self.marker_pose_pub.publish(pose_msg)

                    # Cache last known pose
                    self.last_marker_poses[marker_id] = (
                        pose_msg,
                        self.get_clock().now(),
                    )

                # Broadcast TF if enabled
                if self.config.get("publish_tf", True):
                    self.broadcast_marker_transform(marker_id, tvec, quaternion, header)

                detected_ids.add(marker_id)

        # Add cached markers if within persistence time
        now = self.get_clock().now()
        for marker_id, (pose_msg, ts) in self.last_marker_poses.items():
            if marker_id not in detected_ids:
                elapsed = (now - ts).nanoseconds / 1e9
                if elapsed <= self.marker_persistence:
                    # Update header timestamp
                    pose_msg.header.stamp = self.get_clock().now().to_msg()
                    self.marker_pose_pub.publish(pose_msg)

                    # Also include in MarkerArray
                    # self.get_logger().info(f"Marker id {marker_id}")

                    marker_array.markers.append(
                        Marker(id=int(marker_id), pose=pose_msg.pose)
                    )

        # Publish marker array
        self.aruco_marker_array_pub.publish(marker_array)

        # Publish debug image if enabled
        # self.publish_debug_image(image, corners, ids, rvecs, tvecs, header)

    def broadcast_marker_transform(self, marker_id, tvec, quaternion, header):
        """Broadcast transform for detected marker"""
        # Get marker configuration
        marker_config = self.config.get("markers", {}).get(str(marker_id), {})
        frame_id = marker_config.get("frame_id", f"aruco_marker_{marker_id}")
        relative_to = marker_config.get("relative_to", "transient")

        # Create transform
        t = TransformStamped()
        t.header = header

        # Set parent frame based on configuration
        if relative_to == "transient":
            t.header.frame_id = self.config.get("camera_frame", "camera_optical_frame")
        elif relative_to == "world":
            t.header.frame_id = self.config.get("world_frame", "world")
        else:
            t.header.frame_id = relative_to

        t.child_frame_id = frame_id

        # Set translation
        t.transform.translation.x = float(tvec[0])
        t.transform.translation.y = float(tvec[1])
        t.transform.translation.z = float(tvec[2])

        # Set rotation
        t.transform.rotation.x = quaternion[0]
        t.transform.rotation.y = quaternion[1]
        t.transform.rotation.z = quaternion[2]
        t.transform.rotation.w = quaternion[3]

        # Broadcast transform
        self.tf_broadcaster.sendTransform(t)

    def publish_debug_image(self, image, corners, ids, rvecs, tvecs, header):
        """Publish debug image with detected markers"""
        debug_image = image.copy()
        self.get_logger().info("Sending debug image", throttle_duration_sec=5)

        # Draw detected markers
        cv2.aruco.drawDetectedMarkers(debug_image, corners, ids)

        # Draw axes for each marker
        if rvecs is not None and tvecs is not None:
            for i in range(len(ids)):
                cv2.aruco.drawAxis(
                    debug_image,
                    self.camera_matrix,
                    self.dist_coeffs,
                    rvecs[i],
                    tvecs[i],
                    self.marker_size * 0.5,
                )

        # Convert back to compressed image message
        try:
            debug_msg = self.bridge.cv2_to_imgmsg(debug_image)  # , dst_format="jpg"
            debug_msg.header = header
            self.debug_image_pub.publish(debug_msg)
        except Exception as e:
            self.get_logger().error(f"Error publishing debug image: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetectorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
