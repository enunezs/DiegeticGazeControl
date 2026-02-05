#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from pupil_neon_ros.msg import GazeData
from geometry_msgs.msg import PointStamped
from sensor_msgs.msg import CompressedImage

import cv2
import numpy as np
from cv_bridge import CvBridge
import threading

from gaze_interaction_manager.msg import ButtonStatusArray as ButtonStatusArray_msg
from diegetic_transform_engine.msg import MarkerArray as FiducialMarkerArray
from sensor_msgs.msg import CameraInfo


class Visualizer2D(Node):
    def __init__(self):
        super().__init__("visualizer_2d")

        # --- Parameters ---
        self.debug_fps = 10.0  # configurable frame rate (Hz)
        self.base_width = 1600
        self.base_height = 1200
        self.screen_width = 800
        self.screen_height = 600
        self.scale_x = self.screen_width / self.base_width
        self.scale_y = self.screen_height / self.base_height

        # -------- ARUCO --------
        self._aruco_lock = threading.Lock()
        self.aruco_markers = []
        self.aruco_colors = {}

        self.declare_parameter("use_camera_background", True)
        self.use_camera_background = (
            self.get_parameter("use_camera_background").get_parameter_value().bool_value
        )

        self._image_lock = threading.Lock()
        self.latest_camera_img = None

        ### Subscriptions
        # Gaze
        self.create_subscription(GazeData, "pupil_glasses/gaze_data", self._gaze_cb, 10)
        self.create_subscription(
            PointStamped, "/gaze_controller/corrected_gaze", self._corrected_gaze_cb, 10
        )
        # Buttons
        self.create_subscription(
            ButtonStatusArray_msg, "/dwell_time/input_status", self._button_cb, 10
        )

        # ArUco Markers
        self.create_subscription(
            FiducialMarkerArray,
            "/aruco_markers",
            self._aruco_cb,
            10,
        )

        if self.use_camera_background:
            self.create_subscription(
                CompressedImage, "/pupil_glasses/front_image", self._camera_image_cb, 5
            )
            self.get_logger().info(
                "Using camera background (/pupil_glasses/front_image)"
            )
        else:
            self.get_logger().info("Using blank background")

        # -------- CAMERA INFO --------
        self._cam_info_lock = threading.Lock()
        self.camera_matrix = None
        self.dist_coeffs = None
        self.cam_width = None
        self.cam_height = None

        sensor_qos = rclpy.qos.QoSProfile(
            depth=1,
            reliability=rclpy.qos.QoSReliabilityPolicy.BEST_EFFORT,
        )

        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            "pupil_glasses/front_camera/camera_info",
            self._camera_info_cb,
            sensor_qos,
        )

        # Publisher
        self.debug_image_pub = self.create_publisher(Image, "/visuals/debug_image", 1)

        # Internal state
        self._button_lock = threading.Lock()
        self.button_statuses = {}
        self.gaze_point = None
        self.corrected_gaze_point = None

        # Vision helpers
        self.cv_bridge = CvBridge()

        # Preallocate image buffer (reused every frame)
        self.img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)

        self.get_logger().info("Visualizer2D Node started")

        # Timer (runs at debug_fps)
        self.create_timer(1.0 / self.debug_fps, self._publish_debug_frame)

    # -------- BUTTONS --------
    def _button_cb(self, msg: ButtonStatusArray_msg):
        with self._button_lock:
            self.button_statuses = {btn.button_id: btn for btn in msg.inputs}

    # -------- GAZE --------
    def _gaze_cb(self, msg: GazeData):
        self.gaze_point = (msg.x, msg.y)

    def _corrected_gaze_cb(self, msg: PointStamped):
        self.corrected_gaze_point = (msg.point.x, msg.point.y)

    # -------- IMAGE GENERATION --------
    def _publish_debug_frame(self):
        """Assemble overlays and publish a debug image"""
        img = self.img

        if self.use_camera_background:
            with self._image_lock:
                if self.latest_camera_img is not None:
                    img[:] = self.latest_camera_img
                else:
                    img[:] = 0  # fallback while no image received
        else:
            img[:] = 0

        ### BUTTON DRAWING ###
        with self._button_lock:
            if self.button_statuses is None:
                # TODO: No button data yet, draw in grey
                pass

            for button_id, status in self.button_statuses.items():
                # Pick color
                color = (200, 200, 200)  # Default gray
                if status.button_status == status.BUTTON_ACTIVE:
                    color = (0, 255, 0)
                elif status.button_status == status.BUTTON_HOVER:
                    color = (0, 255, 255)

                # Draw polygon buttons (scaled)
                if (
                    len(status.button.x_points) == 4
                    and len(status.button.y_points) == 4
                ):
                    pts = np.array(
                        [
                            [
                                int(status.button.x_points[i] * self.scale_x),
                                int(status.button.y_points[i] * self.scale_y),
                            ]
                            for i in range(4)
                        ],
                        np.int32,
                    )
                    cv2.polylines(img, [pts], True, color, 2)

                    # Simplified fill (no alpha blending)
                    if status.percent > 0.5:
                        cv2.fillPoly(img, [pts], color)

                    # Draw text and small circle for hover/active
                    cx = int(status.button.center_x * self.scale_x)
                    cy = int(status.button.center_y * self.scale_y)
                    if status.button_status != status.BUTTON_INACTIVE:
                        cv2.putText(
                            img,
                            button_id,
                            (cx - 20, cy),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            (255, 255, 255),
                            1,
                        )
                        cv2.circle(img, (cx, cy), 5, color, 1)

                    # --- NEW: red circle at button center ---
                    cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)  # filled red

                else:
                    # Fallback rectangle (scaled)
                    x0, y0 = int(status.x0 * self.scale_x), int(
                        status.y0 * self.scale_y
                    )
                    x1, y1 = int(status.x1 * self.scale_x), int(
                        status.y1 * self.scale_y
                    )
                    cv2.rectangle(img, (x0, y0), (x1, y1), color, 2)

                    # Center
                    cx = (x0 + x1) // 2
                    cy = (y0 + y1) // 2

                    if status.button_status != status.BUTTON_IDLE:
                        cv2.putText(
                            img,
                            button_id,
                            (x0, y0 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            (255, 255, 255),
                            1,
                        )

                    # --- NEW: red circle at button center ---
                    cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)  # filled red

        # -------- ARUCO SIMPLE VISUALIZATION --------
        with self._aruco_lock, self._cam_info_lock:
            if self.camera_matrix is None:
                return  # cannot project yet

            for marker in self.aruco_markers:
                # Get marker center in camera frame
                t = marker.pose.position
                obj_pt = np.array([[t.x, t.y, t.z]], dtype=np.float32)

                # Project 3D point to 2D
                img_pt, _ = cv2.projectPoints(
                    obj_pt,
                    np.zeros((3, 1), dtype=np.float32),  # rvec = 0
                    np.zeros((3, 1), dtype=np.float32),  # tvec = 0
                    self.camera_matrix,
                    self.dist_coeffs,
                )

                # Pixel coordinates
                px, py = img_pt.ravel()

                # Scale to debug image
                px = int(px * self.screen_width / self.cam_width)
                py = int(py * self.screen_height / self.cam_height)

                color = self.aruco_colors.get(marker.id, (255, 0, 255))

                cv2.circle(self.img, (px, py), 6, color, -1)
                cv2.putText(
                    self.img,
                    f"ID {marker.id}",
                    (px + 5, py - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    color,
                    1,
                )

        ### DRAW GAZE POINTS (scaled) ###
        if self.gaze_point:
            gx = int(self.gaze_point[0] * self.scale_x)
            gy = int(self.gaze_point[1] * self.scale_y)
            cv2.circle(img, (gx, gy), 10, (0, 255, 0), 2)  # raw gaze

        if self.corrected_gaze_point:
            cx = int(self.corrected_gaze_point[0] * self.scale_x)
            cy = int(self.corrected_gaze_point[1] * self.scale_y)
            cv2.circle(img, (cx, cy), 8, (255, 255, 255), 2)
            cv2.circle(img, (cx, cy), 5, (0, 124, 255), 2)

        # Publish image
        try:
            img_msg = self.cv_bridge.cv2_to_imgmsg(img, "bgr8")
            img_msg.header.stamp = self.get_clock().now().to_msg()
            img_msg.header.frame_id = "debug_image"
            self.debug_image_pub.publish(img_msg)
        except Exception as e:
            self.get_logger().warn(f"Failed to publish debug image: {e}")

    def _camera_image_cb(self, msg: CompressedImage):
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is None:
                return

            # Resize to visualization resolution
            img = cv2.resize(img, (self.screen_width, self.screen_height))

            with self._image_lock:
                self.latest_camera_img = img

        except Exception as e:
            self.get_logger().warn(f"Failed to decode camera image: {e}")

    def _aruco_cb(self, msg):
        with self._aruco_lock:
            self.aruco_markers = msg.markers
            for marker in msg.markers:
                if marker.id not in self.aruco_colors:
                    # Pick bright random color
                    self.aruco_colors[marker.id] = (
                        int(100 + 155 * np.random.rand()),
                        int(100 + 155 * np.random.rand()),
                        255,
                    )

    def _camera_info_cb(self, msg: CameraInfo):
        with self._cam_info_lock:
            self.camera_matrix = np.array(msg.k, dtype=np.float32).reshape(3, 3)
            self.dist_coeffs = np.array(msg.d, dtype=np.float32)
            self.cam_width = msg.width
            self.cam_height = msg.height


def main(args=None):
    rclpy.init(args=args)
    node = Visualizer2D()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
