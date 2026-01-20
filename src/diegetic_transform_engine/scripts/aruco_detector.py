#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
import cv2
import numpy as np
import traceback

from cv_bridge import CvBridge
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster
from geometry_msgs.msg import TransformStamped, PoseStamped
from sensor_msgs.msg import CompressedImage, CameraInfo
from diegetic_transform_engine.msg import MarkerArray, Marker
import tf_transformations

# ----------------------------------------------------------------------------
# 1€ Filter Implementation (Kept same as before)
# ----------------------------------------------------------------------------
class LowPassFilter:
    def __init__(self, alpha, init_val=None):
        self.y = init_val
        self.s = init_val
        self.alpha = alpha

    def set_alpha(self, alpha):
        self.alpha = alpha

    def filter(self, val):
        if self.y is None:
            self.s = val
        else:
            self.s = self.alpha * val + (1.0 - self.alpha) * self.s
        self.y = self.s
        return self.y

class OneEuroFilter:
    def __init__(self, t0, x0, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.frequency = 0.0
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_filt = LowPassFilter(self.alpha(min_cutoff), x0)
        self.dx_filt = LowPassFilter(self.alpha(d_cutoff), np.zeros_like(x0))
        self.t_prev = t0

    def alpha(self, cutoff):
        tau = 1.0 / (2 * np.pi * cutoff)
        return 1.0 / (1.0 + tau * self.frequency)

    def __call__(self, t, x):
        if self.t_prev != t:
            self.frequency = 1.0 / (t - self.t_prev)
        self.t_prev = t
        
        # Estimate derivative
        prev_x = self.x_filt.y
        dx = (x - prev_x) * self.frequency
        dx_hat = self.dx_filt.filter(dx)
        
        cutoff = self.min_cutoff + self.beta * np.abs(dx_hat)
        self.x_filt.set_alpha(self.alpha(cutoff))
        return self.x_filt.filter(x)

# ----------------------------------------------------------------------------
# ROS Node
# ----------------------------------------------------------------------------

class ArucoDetectorNode(Node):
    def __init__(self):
        super().__init__("aruco_detector")

        self.bridge = CvBridge()
        
        # 1. Dynamic Broadcaster (Updates Camera position every frame)
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # 2. Static Broadcaster (Connects Marker to Robot ONCE)
        self.static_broadcaster = StaticTransformBroadcaster(self)

        self.load_config()
        self.last_marker_poses = {} 
        self.filters = {} 

        # --- IMPORTANT: Publish the bridge between Robot and Marker ---
        self.publish_static_marker_link()
        # --------------------------------------------------------------

        self.setup_aruco_detector()

        self.camera_matrix = None
        self.dist_coeffs = None
        
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=1,
        )

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

        self.aruco_marker_array_pub = self.create_publisher(
            MarkerArray, "aruco_markers", 10
        )
        self.marker_pose_pub = self.create_publisher(PoseStamped, "aruco_poses", 10)

        self.get_logger().info(f"ArUco detector initialized. Anchor ID: {self.config['anchor_id']}")

    def load_config(self):
        self.declare_parameter("aruco_dict", "DICT_4X4_100")
        self.declare_parameter("marker_size", 0.044)
        self.declare_parameter("camera_frame", "camera_optical_frame") 
        self.declare_parameter("publish_tf", True)
        self.declare_parameter("publish_poses", True)
        self.declare_parameter("marker_persistence", 0.5)
        self.declare_parameter("filter_min_cutoff", 0.5) 
        self.declare_parameter("filter_beta", 0.05)      

        # --- ANCHOR CONFIGURATION ---
        self.declare_parameter("anchor_id", 91) # For calibration target
        # self.declare_parameter("anchor_id", 78) # For controls

        # The robot frame that the marker is attached to (e.g. base_link or end_effector)
        self.declare_parameter("robot_parent_frame", "j2n6s300_end_effector") 
        
        # Where is the marker relative to that robot frame? (x, y, z, r, p, y)
        # Example: Marker is 5cm above the base center
        self.declare_parameter("marker_offset_xyz", [0.0, 0.045, -0.09])
        self.declare_parameter("marker_offset_rpy", [-np.pi/2, 0.0, 0.0])

        self.config = {
            "aruco_dict": self.get_parameter("aruco_dict").value,
            "marker_size": self.get_parameter("marker_size").value,
            "camera_frame": self.get_parameter("camera_frame").value,
            "publish_tf": self.get_parameter("publish_tf").value,
            "publish_poses": self.get_parameter("publish_poses").value,
            "marker_persistence": self.get_parameter("marker_persistence").value,
            "min_cutoff": self.get_parameter("filter_min_cutoff").value,
            "beta": self.get_parameter("filter_beta").value,
            "anchor_id": self.get_parameter("anchor_id").value,
            "robot_parent_frame": self.get_parameter("robot_parent_frame").value,
            "marker_offset_xyz": self.get_parameter("marker_offset_xyz").value,
            "marker_offset_rpy": self.get_parameter("marker_offset_rpy").value,
        }
        self.marker_persistence = self.config.get("marker_persistence", 0.5)

    def publish_static_marker_link(self):
        """
        Publishes a static transform connecting the Robot to the Marker.
        Tree: [robot_parent_frame] -> [aruco_78]
        """
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = self.config["robot_parent_frame"]  # e.g., j2m6s300_link_base
        t.child_frame_id = f"aruco_{self.config['anchor_id']}"

        # Get offsets from config
        xyz = self.config["marker_offset_xyz"]
        rpy = self.config["marker_offset_rpy"]

        t.transform.translation.x = float(xyz[0])
        t.transform.translation.y = float(xyz[1])
        t.transform.translation.z = float(xyz[2])

        quat = tf_transformations.quaternion_from_euler(rpy[0], rpy[1], rpy[2])
        t.transform.rotation.x = quat[0]
        t.transform.rotation.y = quat[1]
        t.transform.rotation.z = quat[2]
        t.transform.rotation.w = quat[3]

        self.static_broadcaster.sendTransform(t)
        self.get_logger().info(f"Published Static TF: {t.header.frame_id} -> {t.child_frame_id}")

    def setup_aruco_detector(self):
        aruco_dict_name = self.config.get("aruco_dict", "DICT_4X4_100")
        if hasattr(cv2.aruco, aruco_dict_name):
            aruco_dict_id = getattr(cv2.aruco, aruco_dict_name)
            self.aruco_dict = cv2.aruco.Dictionary_get(aruco_dict_id)
        else:
            self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)
        self.detector_params = cv2.aruco.DetectorParameters_create()
        self.marker_size = self.config.get("marker_size", 0.05)

    def camera_info_callback(self, msg):
        self.get_logger().info("Camera calibration received", once=True)
        self.camera_matrix = np.array(msg.k).reshape(3, 3)
        self.dist_coeffs = np.array(msg.d)

    def image_callback(self, msg):
        if self.camera_matrix is None:
            return
        try:
            cv_image = self.bridge.compressed_imgmsg_to_cv2(msg, "bgr8")
            self.detect_markers(cv_image, msg.header)
        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")
            self.get_logger().error(traceback.format_exc())

    def get_filtered_pose(self, marker_id, t_curr, tvec, quat):
        """Applies OneEuroFilter to position and rotation."""
        min_cutoff = self.config.get("min_cutoff", 0.5)
        beta = self.config.get("beta", 0.05)
        
        tvec = np.array(tvec, dtype=float)
        quat = np.array(quat, dtype=float)

        if marker_id not in self.filters:
            self.filters[marker_id] = {
                'pos': OneEuroFilter(t_curr, tvec, min_cutoff=min_cutoff, beta=beta),
                'rot': OneEuroFilter(t_curr, quat, min_cutoff=min_cutoff, beta=beta)
            }
            return tvec, quat

        f_pos = self.filters[marker_id]['pos'](t_curr, tvec)

        prev_quat = self.filters[marker_id]['rot'].x_filt.y
        if prev_quat is not None:
            prev_quat = np.array(prev_quat)
            if np.dot(prev_quat, quat) < 0:
                quat = -quat

        f_quat = self.filters[marker_id]['rot'](t_curr, quat)
        f_quat = f_quat / np.linalg.norm(f_quat)

        return f_pos, f_quat

    def detect_markers(self, image, header):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.detector_params)

        current_header = header
        current_header.stamp = self.get_clock().now().to_msg()

        marker_array = MarkerArray()
        marker_array.header = current_header
        
        marker_array.header.frame_id = self.config["camera_frame"]
        marker_array.markers = []
        detected_ids = set()

        t_curr = header.stamp.sec + header.stamp.nanosec * 1e-9     


        if ids is not None and len(ids) > 0:
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners, self.marker_size, self.camera_matrix, self.dist_coeffs
            )

            for i, marker_id in enumerate(ids.flatten()):
                # Raw detection (Camera -> Marker)
                rvec_raw = rvecs[i][0]
                tvec_raw = tvecs[i][0]
                
                rot_mat = cv2.Rodrigues(rvec_raw)[0]
                T_raw = np.vstack([np.hstack([rot_mat, [[0],[0],[0]]]), [0, 0, 0, 1]])
                quat_raw = tf_transformations.quaternion_from_matrix(T_raw)

                # Filter
                tvec_filtered, quat_filtered = self.get_filtered_pose(
                    int(marker_id), t_curr, tvec_raw, quat_raw
                )

                # Reconstruct T_cam_marker from filtered data
                T_cam_marker = tf_transformations.quaternion_matrix(quat_filtered)
                T_cam_marker[0:3, 3] = tvec_filtered

                # 1. Populate Marker Msg
                marker = Marker()
                marker.id = int(marker_id)
                marker.pose.position.x = float(tvec_filtered[0])
                marker.pose.position.y = float(tvec_filtered[1])
                marker.pose.position.z = float(tvec_filtered[2])
                marker.pose.orientation.x = quat_filtered[0]
                marker.pose.orientation.y = quat_filtered[1]
                marker.pose.orientation.z = quat_filtered[2]
                marker.pose.orientation.w = quat_filtered[3]
                marker_array.markers.append(marker)
                detected_ids.add(marker_id)

                # 2. Dynamic Broadcasting
                if self.config.get("publish_tf", True):
                    anchor_id = self.config["anchor_id"]
                    
                    if int(marker_id) == anchor_id:
                        # ANCHOR FOUND: Update Camera Position based on Anchor
                        # Robot (Static) -> Aruco (Detection) -> Camera
                        self.broadcast_anchor_transform(T_cam_marker, header, marker_id)
                    else:
                        # STANDARD MARKER: Update Marker Position based on Camera
                        # Camera -> Aruco
                        self.broadcast_standard_transform(marker_id, tvec_filtered, quat_filtered, header)

                # Publish PoseStamped
                if self.config.get("publish_poses", True):
                    pose_msg = PoseStamped()
                    pose_msg.header = header
                    pose_msg.pose = marker.pose
                    self.marker_pose_pub.publish(pose_msg)
                    self.last_marker_poses[marker_id] = (pose_msg, self.get_clock().now())

        # Persistence for lost markers
        now = self.get_clock().now()
        for marker_id, (pose_msg, ts) in self.last_marker_poses.items():
            if marker_id not in detected_ids:
                elapsed = (now - ts).nanoseconds / 1e9
                if elapsed <= self.marker_persistence:
                    pose_msg.header.stamp = self.get_clock().now().to_msg()
                    self.marker_pose_pub.publish(pose_msg)
                    marker_array.markers.append(Marker(id=int(marker_id), pose=pose_msg.pose))

        self.aruco_marker_array_pub.publish(marker_array)

    def broadcast_anchor_transform(self, T_cam_marker, header, marker_id):
        """
        Calculates Camera position relative to the Marker (Robot).
        Publishes TF: aruco_78 -> camera_optical_frame
        """
        # self.get_logger().info(f"Broadcasting Anchor Transform for Marker ID: {marker_id}")
        # Invert: T_marker_cam = (T_cam_marker)^-1
        T_marker_cam = np.linalg.inv(T_cam_marker)
        
        trans = tf_transformations.translation_from_matrix(T_marker_cam)
        quat = tf_transformations.quaternion_from_matrix(T_marker_cam)

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = f"aruco_{marker_id}"  # Parent: The Marker (on the robot)
        # t.child_frame_id = header.frame_id        
        t.child_frame_id = self.config["camera_frame"] # Child: The Camera

        t.transform.translation.x = float(trans[0])
        t.transform.translation.y = float(trans[1])
        t.transform.translation.z = float(trans[2])
        t.transform.rotation.x = quat[0]
        t.transform.rotation.y = quat[1]
        t.transform.rotation.z = quat[2]
        t.transform.rotation.w = quat[3]

        self.tf_broadcaster.sendTransform(t)

    def broadcast_standard_transform(self, marker_id, tvec, quaternion, header):
        """Standard Marker: Camera -> Marker"""
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = self.config["camera_frame"] # Parent: The Camera
        t.child_frame_id = f"aruco_{marker_id}"

        t.transform.translation.x = float(tvec[0])
        t.transform.translation.y = float(tvec[1])
        t.transform.translation.z = float(tvec[2])
        t.transform.rotation.x = quaternion[0]
        t.transform.rotation.y = quaternion[1]
        t.transform.rotation.z = quaternion[2]
        t.transform.rotation.w = quaternion[3]

        self.tf_broadcaster.sendTransform(t)
        self.get_logger().info(f"Broadcasted TF: {t.header.frame_id} -> {t.child_frame_id}", once=True)

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