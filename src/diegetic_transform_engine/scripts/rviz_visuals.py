#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from pupil_neon_ros.msg import GazeData
from geometry_msgs.msg import PointStamped
# from diegetic_transform_engine.msg import DiegeticButton2DArray, DiegeticButton2D
from gaze_interaction_manager.msg import ButtonStatusArray as ButtonStatusArray_msg

import cv2
import numpy as np
from cv_bridge import CvBridge
import threading


# TODO: Add centers to buttons

class Visualizer2D(Node):
    def __init__(self):
        super().__init__("visualizer_2d")


        # Subscriptions
        self.create_subscription(GazeData, "pupil_glasses/gaze_data", self._gaze_cb, 50)
        self.create_subscription(PointStamped, "/gaze_controller/corrected_gaze", self._corrected_gaze_cb, 10)
        
        self.create_subscription(ButtonStatusArray_msg, "/dwell_time/input_status", self._button_cb, 10)
        # [ ] Aha 
        # if you want direct integration, subscribe to raw camera+detections here too
        
        # Publishers
        self.debug_image_pub = self.create_publisher(Image, "/visuals/debug_image", 10)

        # Internal state
        self._button_lock = threading.Lock()
        self.button_statuses = {}
        self.gaze_point = None
        self.corrected_gaze_point = None

        # Screen dimensions (for image canvas)
        self.screen_width = 1920
        self.screen_height = 1080

        # Vision helpers
        self.cv_bridge = CvBridge()
        self.get_logger().info("Visualizer2D Node started")

        # Timer
        self.create_timer(0.1, self._publish_debug_frame)

    # -------- BUTTONS --------
    def _button_cb(self, msg: ButtonStatusArray_msg):
        with self._button_lock:
            self.button_statuses = {btn.button_id: btn for btn in msg.inputs}
        # self._publish_debug_frame()

    # -------- GAZE --------
    def _gaze_cb(self, msg: GazeData):
        self.gaze_point = (msg.x, msg.y)
        # self._publish_debug_frame()

    def _corrected_gaze_cb(self, msg: PointStamped):
        self.corrected_gaze_point = (msg.point.x, msg.point.y)
        # self._publish_debug_frame()

    # -------- IMAGE GENERATION --------
    def _publish_debug_frame(self):
        """Assemble overlays and publish a debug image"""
        img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)

        # self.get_logger().info(f"Button statuses: {self.button_statuses.keys()}")

        # Draw buttons
        with self._button_lock:
            for button_id, status in self.button_statuses.items():
                # Pick color
                color = (200, 200, 200)  # Default gray
                if status.button_status == status.BUTTON_ACTIVE:
                    color = (0, 255, 0)
                elif status.button_status == status.BUTTON_HOVER:
                    color = (0, 255, 255)

                if len(status.button.x_points) == 4 and len(status.button.y_points) == 4:
                    pts = np.array([[int(status.button.x_points[i]), int(status.button.y_points[i])] for i in range(4)], np.int32)
                    cv2.polylines(img, [pts], True, color, 3)
                    if status.percent > 0:
                        overlay = img.copy()
                        cv2.fillPoly(overlay, [pts], color)
                        cv2.addWeighted(overlay, status.percent * 0.3, img, 1.0, 0, img)
                    cv2.putText(img, button_id, (int(status.button.center_x), int(status.button.center_y)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 3)
                else:
                    x0, y0, x1, y1 = int(status.x0), int(status.y0), int(status.x1), int(status.y1)
                    cv2.rectangle(img, (x0,y0), (x1,y1), color, 2)
                    cv2.putText(img, button_id, (x0, y0-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 3)

                # Draw circle in the center
                center_x = status.button.center_x
                center_y = status.button.center_y
                cv2.circle(img, (int(center_x), int(center_y)), 8, color, 2)

        # Draw gaze points
        if self.gaze_point:
            cv2.circle(img, (int(self.gaze_point[0]), int(self.gaze_point[1])), 20, (0, 255, 0), 2)  # Red = raw gaze
        if self.corrected_gaze_point:
            cv2.circle(img, (int(self.corrected_gaze_point[0]), int(self.corrected_gaze_point[1])), 15, (255, 255, 255), 2)  # White = corrected gaze
            cv2.circle(img, (int(self.corrected_gaze_point[0]), int(self.corrected_gaze_point[1])), 10, (0, 124, 255), 2)  
            cv2.circle(img, (int(self.corrected_gaze_point[0]), int(self.corrected_gaze_point[1])), 5, (255, 255, 255), 2)  # White = corrected gaze

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
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
