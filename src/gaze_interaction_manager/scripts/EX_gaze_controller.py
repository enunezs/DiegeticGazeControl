#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from collections import deque
import numpy as np
from threading import Lock
from statistics import median

from pupil_neon_ros.msg import GazeData, GazeEvent
from gaze_interaction_manager.msg import ButtonStatus
from gaze_interaction_manager.msg import InteractionSegment, CalibrationModel
from geometry_msgs.msg import PointStamped, Point


class GazeController(Node):
    def __init__(self):
        super().__init__("EX_gaze_controller")
        self._lock = Lock()

        # --- Parameters & Buffers ---
        self.history_depth = 1000  # 5 seconds @ 200Hz
        self.smoothing_window = 20  # 100ms @ 200Hz
        self.ema_alpha = 0.2
        self.padding_samples = 20  # 100ms padding
        self.min_samples = 40  # 200ms min duration

        # Deques for rolling history
        self.raw_history = deque(maxlen=self.history_depth)
        self.smoothed_x = 0.0
        self.smoothed_y = 0.0

        # Interaction Tracking
        self.is_hovering = False
        self.current_target = None
        self.active_segment_samples = []

        # Calibration State
        self.model_type = 0  # Quadratic default
        self.coeffs_x = np.zeros(6)
        self.coeffs_y = np.zeros(6)

        # --- Subscriptions ---
        self.create_subscription(GazeData, "pupil_glasses/gaze_data", self.gaze_cb, 10)
        self.create_subscription(
            ButtonStatus, "dwell_time/active_button", self.button_cb, 10
        )
        self.create_subscription(
            GazeEvent, "pupil_glasses/event/saccade", self.event_cb, 10
        )
        self.create_subscription(
            GazeEvent, "pupil_glasses/event/blink", self.event_cb, 10
        )
        self.create_subscription(
            CalibrationModel, "calibration/model_update", self.model_cb, 10
        )

        # --- Publishers ---
        self.segment_pub = self.create_publisher(
            InteractionSegment, "calibration/interaction_segment", 10
        )
        self.corrected_gaze_pub = self.create_publisher(
            PointStamped, "gaze_controller/corrected_gaze", 10
        )

    def gaze_cb(self, msg: GazeData):
        with self._lock:
            # 1. Cleaning & Smoothing
            self.raw_history.append(msg)

            # FOV Check (100px border)
            is_valid_fov = 100 < msg.x < 1500 and 100 < msg.y < 1100

            # Rolling Median (approx 100ms)
            last_samples = list(self.raw_history)[-self.smoothing_window :]
            if len(last_samples) >= self.smoothing_window:
                med_x = median([s.x for s in last_samples])
                med_y = median([s.y for s in last_samples])

                # EMA
                self.smoothed_x = (self.ema_alpha * med_x) + (
                    1 - self.ema_alpha
                ) * self.smoothed_x
                self.smoothed_y = (self.ema_alpha * med_y) + (
                    1 - self.ema_alpha
                ) * self.smoothed_y
            else:
                self.smoothed_x, self.smoothed_y = msg.x, msg.y

            # 2. Apply Current Calibration
            # dx, dy = self.calculate_correction(self.smoothed_x, self.smoothed_y)
            dx, dy = 0, 0  # No correction for EX testing

            corr_msg = PointStamped()
            corr_msg.header = msg.header
            corr_msg.point = Point(
                x=self.smoothed_x - dx, y=self.smoothed_y - dy, z=0.0
            )
            self.corrected_gaze_pub.publish(corr_msg)

            # TODO: Remove debug after testing
            # self.get_logger().debug(
            #     f"Corrected Gaze: ({corr_msg.point.x:.1f}, {corr_msg.point.y:.1f})"
            # )

            # 3. Buffer samples if interacting
            if self.is_hovering and is_valid_fov:
                self.active_segment_samples.append(msg)

    def calculate_correction(self, x, y):
        if self.model_type == 0:  # Quadratic
            # x^2, y^2, xy, x, y, 1
            feats = np.array([x**2, y**2, x * y, x, y, 1.0])
            return np.dot(self.coeffs_x, feats), np.dot(self.coeffs_y, feats)
        return 0.0, 0.0

    def event_cb(self, msg):
        """Triggered by Saccade or Blink: End current segment"""
        self.process_and_send_segment()

    def button_cb(self, msg: ButtonStatus):
        with self._lock:
            if msg.button_status == ButtonStatus.BUTTON_ACTIVE:
                if not self.is_hovering:
                    self.is_hovering = True
                    self.current_target = msg.button
                    self.active_segment_samples = []
            else:
                if self.is_hovering:
                    self.process_and_send_segment()
                    self.is_hovering = False

    def process_and_send_segment(self):
        """The 'Post-Event' Trimming Logic"""
        if len(self.active_segment_samples) < (
            self.min_samples + 2 * self.padding_samples
        ):
            self.active_segment_samples = []
            return

        # Slice 100ms from start and end
        trimmed = self.active_segment_samples[
            self.padding_samples : -self.padding_samples
        ]

        seg_msg = InteractionSegment()
        seg_msg.header.stamp = self.get_clock().now().to_msg()
        seg_msg.button_id = self.current_target.button_id
        seg_msg.target_pixel = Point(
            x=self.current_target.center_x, y=self.current_target.center_y
        )
        seg_msg.samples = trimmed

        self.segment_pub.publish(seg_msg)
        self.active_segment_samples = []

    def model_cb(self, msg: CalibrationModel):
        with self._lock:
            self.model_type = msg.model_type
            self.coeffs_x = np.array(msg.coeffs_x)
            self.coeffs_y = np.array(msg.coeffs_y)
            self.get_logger().info("Calibration model updated.")


def main(args=None):
    rclpy.init(args=args)
    node = GazeController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
