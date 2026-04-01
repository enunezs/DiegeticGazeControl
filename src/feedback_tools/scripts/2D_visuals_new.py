#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from cv_bridge import CvBridge
from collections import deque

# Messages
from sensor_msgs.msg import Image, CompressedImage, CameraInfo
from pupil_neon_ros.msg import GazeData
from geometry_msgs.msg import PointStamped
from gaze_interaction_manager.msg import ButtonStatusArray as ButtonStatusArray_msg
from diegetic_transform_engine.msg import MarkerArray as FiducialMarkerArray


class Visualizer2D(Node):
    def __init__(self):
        super().__init__("visualizer_2d")
        self.cv_bridge = CvBridge()

        # --- Parameters ---
        self.screen_width = 800
        self.screen_height = 600
        self.base_width = 1600.0
        self.base_height = 1200.0

        # --- Buffers (Store ~1 second of data) ---
        self.gaze_buffer = deque(maxlen=200)  # (ts, x, y)
        self.corr_gaze_buffer = deque(maxlen=200)  # (ts, x, y)
        self.button_buffer = deque(maxlen=60)  # (ts, dict_of_buttons)
        self.marker_buffer = deque(maxlen=60)  # (ts, markers_list)

        # --- Subscriptions ---
        self.create_subscription(GazeData, "pupil_glasses/gaze_data", self._gaze_cb, 10)
        self.create_subscription(
            PointStamped, "/gaze_controller/corrected_gaze", self._corr_gaze_cb, 10
        )
        self.create_subscription(
            ButtonStatusArray_msg, "/dwell_time/input_status", self._button_cb, 10
        )
        self.create_subscription(
            FiducialMarkerArray, "/aruco_markers", self._aruco_cb, 10
        )
        self.create_subscription(
            CompressedImage, "/pupil_glasses/front_image", self._camera_image_cb, 5
        )
        self.create_subscription(
            CameraInfo,
            "pupil_glasses/front_camera/camera_info",
            self._camera_info_cb,
            10,
        )

        # --- Publishers ---
        self.debug_image_pub = self.create_publisher(Image, "/visuals/debug_image", 5)

        # Camera Intrinsic State
        self.camera_matrix = None
        self.dist_coeffs = None
        self.cam_res = (1, 1)  # Width, Height

        self.get_logger().info("Synchronized Visualizer2D Initialized")

    # --- Data Ingestion (Buffering with Timestamps) ---

    def _get_ts(self, header):
        return header.stamp.sec + (header.stamp.nanosec / 1e9)

    def _gaze_cb(self, msg):
        self.gaze_buffer.append((self._get_ts(msg.header), msg.x, msg.y))

    def _corr_gaze_cb(self, msg):
        self.corr_gaze_buffer.append(
            (self._get_ts(msg.header), msg.point.x, msg.point.y)
        )

    def _button_cb(self, msg):
        btns = {btn.button_id: btn for btn in msg.inputs}
        self.button_buffer.append((self._get_ts(msg.header), btns))

    def _aruco_cb(self, msg):
        self.marker_buffer.append((self._get_ts(msg.header), msg.markers))

    def _camera_info_cb(self, msg):
        self.camera_matrix = np.array(msg.k).reshape(3, 3)
        self.dist_coeffs = np.array(msg.d)
        self.cam_res = (msg.width, msg.height)

    # --- Helper: Find Closest Data in Buffer ---
    def _find_closest(self, buffer, target_ts):
        if not buffer:
            return None
        # Simple closest-neighbor search
        return min(buffer, key=lambda x: abs(x[0] - target_ts))

    # --- Main Loop (Triggered by Image) ---
    def _camera_image_cb(self, msg):
        img_ts = self._get_ts(msg.header)

        # 1. Decode Image
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            raw_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if raw_img is None:
                return
            img = cv2.resize(raw_img, (self.screen_width, self.screen_height))
        except Exception as e:
            self.get_logger().error(f"Decode error: {e}")
            return

        # 2. Find matching data for THIS image's timestamp
        gaze = self._find_closest(self.gaze_buffer, img_ts)
        corr = self._find_closest(self.corr_gaze_buffer, img_ts)
        btns_entry = self._find_closest(self.button_buffer, img_ts)
        markers_entry = self._find_closest(self.marker_buffer, img_ts)

        # 3. Draw Overlays
        scale_x = self.screen_width / self.base_width
        scale_y = self.screen_height / self.base_height

        # Draw Buttons
        if btns_entry:
            for b_id, status in btns_entry[1].items():
                color = (
                    (0, 255, 0)
                    if status.button_status == status.BUTTON_ACTIVE
                    else (
                        (0, 255, 255)
                        if status.button_status == status.BUTTON_HOVER
                        else (200, 200, 200)
                    )
                )
                if len(status.button.x_points) == 4:
                    pts = np.array(
                        [
                            [
                                int(status.button.x_points[i] * scale_x),
                                int(status.button.y_points[i] * scale_y),
                            ]
                            for i in range(4)
                        ],
                        np.int32,
                    )
                    cv2.polylines(img, [pts], True, color, 2)
                    if status.percent > 0.5:
                        cv2.fillPoly(img, [pts], color)
                # Red dot at center
                cv2.circle(
                    img,
                    (
                        int(status.button.center_x * scale_x),
                        int(status.button.center_y * scale_y),
                    ),
                    4,
                    (0, 0, 255),
                    -1,
                )

        # Draw Markers
        if markers_entry and self.camera_matrix is not None:
            for m in markers_entry[1]:
                obj_pt = np.array(
                    [[m.pose.position.x, m.pose.position.y, m.pose.position.z]],
                    dtype=np.float32,
                )
                img_pt, _ = cv2.projectPoints(
                    obj_pt,
                    np.zeros(3),
                    np.zeros(3),
                    self.camera_matrix,
                    self.dist_coeffs,
                )
                px, py = img_pt.ravel()
                # Scale projection to display resolution
                px = int(px * self.screen_width / self.cam_res[0])
                py = int(py * self.screen_height / self.cam_res[1])
                cv2.circle(img, (px, py), 6, (255, 0, 255), -1)

        # Draw Gaze
        if gaze:
            cv2.circle(
                img,
                (int(gaze[1] * scale_x), int(gaze[2] * scale_y)),
                10,
                (0, 255, 0),
                2,
            )
        if corr:
            cv2.circle(
                img,
                (int(corr[1] * scale_x), int(corr[2] * scale_y)),
                8,
                (255, 255, 255),
                1,
            )
            cv2.circle(
                img,
                (int(corr[1] * scale_x), int(corr[2] * scale_y)),
                4,
                (0, 128, 255),
                -1,
            )

        # 4. Publish
        out_msg = self.cv_bridge.cv2_to_imgmsg(img, "bgr8")
        out_msg.header = msg.header  # Keep original image timestamp
        self.debug_image_pub.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(Visualizer2D())
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()
