#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from pupil_neon_ros.msg import GazeData
from geometry_msgs.msg import PointStamped
from gaze_interaction_manager.msg import ButtonStatusArray as ButtonStatusArray_msg

import cv2
import numpy as np
from cv_bridge import CvBridge
import threading


class Visualizer2D(Node):
    def __init__(self):
        super().__init__("visualizer_2d")

        # --- Parameters ---
        self.debug_fps = 10.0 # configurable frame rate (Hz)
        self.base_width = 1920
        self.base_height = 1080
        self.screen_width = 960
        self.screen_height = 540
        self.scale_x = self.screen_width / self.base_width
        self.scale_y = self.screen_height / self.base_height

        # Subscriptions
        self.create_subscription(GazeData, "pupil_glasses/gaze_data", self._gaze_cb, 10)
        self.create_subscription(PointStamped, "/gaze_controller/corrected_gaze", self._corrected_gaze_cb, 10)
        self.create_subscription(ButtonStatusArray_msg, "/dwell_time/input_status", self._button_cb, 10)

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
        img[:] = 0  # clear image in place

        with self._button_lock:
            for button_id, status in self.button_statuses.items():
                # Pick color
                color = (200, 200, 200)  # Default gray
                if status.button_status == status.BUTTON_ACTIVE:
                    color = (0, 255, 0)
                elif status.button_status == status.BUTTON_HOVER:
                    color = (0, 255, 255)

                # Draw polygon buttons (scaled)
                if len(status.button.x_points) == 4 and len(status.button.y_points) == 4:
                    pts = np.array([
                        [int(status.button.x_points[i] * self.scale_x),
                         int(status.button.y_points[i] * self.scale_y)]
                        for i in range(4)
                    ], np.int32)
                    cv2.polylines(img, [pts], True, color, 2)

                    # Simplified fill (no alpha blending)
                    if status.percent > 0.5:
                        cv2.fillPoly(img, [pts], color)

                    # Simplified text (only for hover/active)
                    if status.button_status != status.BUTTON_INACTIVE:
                        cx = int(status.button.center_x * self.scale_x)
                        cy = int(status.button.center_y * self.scale_y)
                        cv2.putText(img, button_id, (cx - 20, cy),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                        cv2.circle(img, (cx, cy), 5, color, 1)

                else:
                    # Fallback rectangle (scaled)
                    x0, y0 = int(status.x0 * self.scale_x), int(status.y0 * self.scale_y)
                    x1, y1 = int(status.x1 * self.scale_x), int(status.y1 * self.scale_y)
                    cv2.rectangle(img, (x0, y0), (x1, y1), color, 2)

                    if status.button_status != status.BUTTON_IDLE:
                        cv2.putText(img, button_id, (x0, y0 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Draw gaze points (scaled)
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
