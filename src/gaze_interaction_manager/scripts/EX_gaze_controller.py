#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult
from collections import deque
import numpy as np
from threading import Lock
from statistics import median
import time

# Messages
from std_msgs.msg import Float32, Header
from geometry_msgs.msg import Point, PointStamped
from pupil_neon_ros.msg import GazeData, GazeEvent
from gaze_interaction_manager.msg import ButtonStatus
from gaze_interaction_manager.msg import InteractionSegment, CalibrationModel


class GazeController(Node):
    def __init__(self):
        super().__init__("gaze_controller")
        self._lock = Lock()
        self.get_logger().info("Gaze Controller Node Initialized")

        # --- 1. Expose Parameters ---
        self.declare_parameter("median_window", 20)  # 100ms @ 200Hz
        self.declare_parameter("ema_alpha", 0.2)
        self.declare_parameter("edge_margin", 100)  # px from edge
        self.declare_parameter("pad_duration_ms", 100.0)  # padding around events
        self.declare_parameter("min_event_duration_ms", 200.0)  # min duration to save
        self.declare_parameter("history_length_s", 5.0)  # buffer depth
        self.declare_parameter("max_offset_px", 200.0)  # cap for compensation

        self.declare_parameter("compensation_active", False)  # Perform compensation

        # Add a callback to update these live
        self.add_on_set_parameters_callback(self.param_callback)
        self.update_internal_params()

        # --- 2. Buffers & State ---
        self.raw_history = deque(maxlen=self.history_depth_samples)
        self.active_segment_samples = []

        self.smoothed_x = 0.0
        self.smoothed_y = 0.0
        self.coeffs_x = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.coeffs_y = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        # Logical States for Debug
        self.is_hovering = False
        self.in_saccade = False
        self.in_blink = False
        self.last_event_time = 0.0  # To track padding AFTER an event

        # --- 3. Publishers ---
        # Main Publishers
        self.segment_pub = self.create_publisher(
            InteractionSegment, "calibration/interaction_segment", 10
        )
        self.corrected_gaze_pub = self.create_publisher(
            PointStamped, "gaze_controller/corrected_gaze", 10
        )

        # We use Float32 for easy plotting in rqt_plot
        self.debug_pub_saccade = self.create_publisher(
            Float32, "debug/signal_saccade", 10
        )
        self.debug_pub_blink = self.create_publisher(Float32, "debug/signal_blink", 10)
        self.debug_pub_fov = self.create_publisher(Float32, "debug/signal_in_fov", 10)
        self.debug_pub_hover = self.create_publisher(
            Float32, "debug/signal_hovering", 10
        )
        self.debug_pub_clean = self.create_publisher(
            Float32, "debug/signal_is_clean", 10
        )

        # --- 4. Subscriptions ---
        self.create_subscription(GazeData, "pupil_glasses/gaze_data", self.gaze_cb, 10)
        self.create_subscription(
            GazeEvent, "pupil_glasses/event/saccade", self.saccade_cb, 10
        )
        self.create_subscription(
            GazeEvent, "pupil_glasses/event/blink", self.blink_cb, 10
        )
        self.create_subscription(
            ButtonStatus, "dwell_time/active_button", self.button_cb, 10
        )
        self.create_subscription(
            CalibrationModel, "calibration/model_update", self.model_cb, 10
        )

        # Latency Debugging
        self.latency_ema_alpha = 0.1  # Weight for the moving average
        self.mean_latency_ms = 0.0
        self.rms_latency_ms = 0.0

        self.debug_pub_latency = self.create_publisher(Float32, "debug/latency_ms", 10)
        self.debug_pub_latency_rms = self.create_publisher(
            Float32, "debug/latency_rms", 10
        )

    def update_internal_params(self):
        """Calculates internal sample counts based on time parameters."""
        self.median_window = self.get_parameter("median_window").value
        self.ema_alpha = self.get_parameter("ema_alpha").value
        self.edge_margin = self.get_parameter("edge_margin").value
        self.max_offset = self.get_parameter("max_offset_px").value

        # 200Hz assumption for sample calculation
        hz = 200.0
        self.history_depth_samples = int(
            self.get_parameter("history_length_s").value * hz
        )
        self.pad_samples = int(
            (self.get_parameter("pad_duration_ms").value / 1000.0) * hz
        )
        self.min_samples = int(
            (self.get_parameter("min_event_duration_ms").value / 1000.0) * hz
        )

    def param_callback(self, params):
        self.update_internal_params()
        return SetParametersResult(successful=True)

    # The Gaze Callback (High Speed):
    # Takes the latest available correction model and applies it to the current point.
    # Avoid heavy math.
    def gaze_cb(self, msg: GazeData):
        with self._lock:
            now = self.get_clock().now().nanoseconds / 1e9
            self.raw_history.append(msg)

            # --- A. CLEANING CRITERIA ---
            # 1. FOV Check
            in_fov = (
                self.edge_margin < msg.x < 1600 - self.edge_margin
                and self.edge_margin < msg.y < 1200 - self.edge_margin
            )

            # 2. Time-since-event Check (100ms padding AFTER an event)
            event_padding_active = (now - self.last_event_time) < (
                self.get_parameter("pad_duration_ms").value / 1000.0
            )

            # 3. Overall Validity
            is_clean = (
                in_fov
                and not self.in_saccade
                and not self.in_blink
                and not event_padding_active
            )

            # --- B. SMOOTHING ---
            last_samples = list(self.raw_history)[-self.median_window :]
            if len(last_samples) >= self.median_window:
                mx = median([s.x for s in last_samples])
                my = median([s.y for s in last_samples])
                self.smoothed_x = (self.ema_alpha * mx) + (
                    1 - self.ema_alpha
                ) * self.smoothed_x
                self.smoothed_y = (self.ema_alpha * my) + (
                    1 - self.ema_alpha
                ) * self.smoothed_y
            else:
                self.smoothed_x, self.smoothed_y = msg.x, msg.y

            # --- C. CORRECTION ---
            dx, dy = self.get_quadratic_correction(self.smoothed_x, self.smoothed_y)

            self.compensation_active = self.get_parameter("compensation_active").value

            # Apply capped correction
            if self.compensation_active:
                dx = np.clip(dx, -self.max_offset, self.max_offset)
                dy = np.clip(dy, -self.max_offset, self.max_offset)
            else:
                dx, dy = 0.0, 0.0

            out_msg = PointStamped()
            out_msg.header = msg.header
            out_msg.point = Point(x=self.smoothed_x - dx, y=self.smoothed_y - dy, z=0.0)
            self.corrected_gaze_pub.publish(out_msg)

            # --- D. DATA COLLECTION ---
            if self.is_hovering:
                if is_clean:
                    # Append sample to the current "Fixation Chunk"
                    self.active_segment_samples.append(msg)
                else:
                    # An interruption occurred (e.g. eye moved or blinked)
                    # Try to finalize whatever we collected before the interruption
                    if len(self.active_segment_samples) > 0:
                        self.finalize_and_send_segment()

            # --- E. DEBUG SIGNALS ---
            offset = 0.1  # To separate lines in rqt_plot
            self.debug_pub_hover.publish(
                Float32(data=1.0 - offset if self.is_hovering else 0.0)
            )
            self.debug_pub_saccade.publish(
                Float32(data=2.0 - offset if self.in_saccade else 1.0)
            )
            self.debug_pub_blink.publish(
                Float32(data=3.0 - offset if self.in_blink else 2.0)
            )
            self.debug_pub_fov.publish(Float32(data=4.0 - offset if in_fov else 3.0))
            self.debug_pub_clean.publish(
                Float32(data=5.0 - offset if is_clean else 4.0)
            )

    def get_quadratic_correction(self, x, y):
        # [x^2, y^2, xy, x, y, 1]
        feats = np.array([x**2, y**2, x * y, x, y, 1.0])
        return np.dot(self.coeffs_x, feats), np.dot(self.coeffs_y, feats)

    # --- Event Handlers ---
    def saccade_cb(self, msg: GazeEvent):
        with self._lock:
            # Saccades usually have a status or are sent at the START of movement
            # self.in_saccade = True
            self.last_event_time = self.get_clock().now().nanoseconds / 1e9

            # If we were collecting data, the saccade just ended the clean fixation
            self.finalize_and_send_segment()

    def blink_cb(self, msg: GazeEvent):
        with self._lock:
            # self.in_blink = True
            self.last_event_time = self.get_clock().now().nanoseconds / 1e9

            # If we were collecting data, the blink just ended the clean fixation
            self.finalize_and_send_segment()

    # The Button Callback (Lower Speed):
    # It looks back in time, calculates the error, and updates the model that the gaze callback is using.

    def button_cb(self, msg: ButtonStatus):
        with self._lock:
            # 1. Calculate Latency (Time-of-arrival vs Time-of-capture)
            # msg.header.stamp should be the time the image was captured
            now_ns = self.get_clock().now().nanoseconds
            button_time_ns = msg.header.stamp.sec * 1e9 + msg.header.stamp.nanosec

            latency_ms = (
                now_ns - button_time_ns
            ) / 1e6  # Total delay from camera to this node

            # 2. Update RMS/EMA (Efficiently)
            self.mean_latency_ms = (self.latency_ema_alpha * latency_ms) + (
                1 - self.latency_ema_alpha
            ) * self.mean_latency_ms
            self.rms_latency_ms = np.sqrt(
                (self.latency_ema_alpha * (latency_ms**2))
                + (1 - self.latency_ema_alpha) * (self.rms_latency_ms**2)
            )

            self.debug_pub_latency.publish(Float32(data=latency_ms))
            self.debug_pub_latency_rms.publish(Float32(data=self.rms_latency_ms))

            # 3. Time-Matching (Finding the exact gaze point when the button was seen)
            matched_gaze = self.get_interpolated_gaze(button_time_ns)

            if matched_gaze:
                # This is your "Ground Truth" comparison
                # Error = Matched Gaze - Button Center
                pass

            # Status: 0=Inactive, 1=Active/Hovering
            new_hover_state = msg.button_status == ButtonStatus.BUTTON_ACTIVE

            if new_hover_state != self.is_hovering:
                if not new_hover_state:
                    # User just looked away from the button
                    self.finalize_and_send_segment()

                self.is_hovering = new_hover_state
                self.current_button_target = msg.button if self.is_hovering else None

    def get_interpolated_gaze(self, target_time_ns):
        """
        Efficiently finds/interpolates gaze data from the buffer for a specific timestamp.
        """
        if len(self.raw_history) < 2:
            return None

        # Convert target_time to seconds to match GazeData headers if necessary
        target_time = target_time_ns / 1e9

        # Since deque is ordered, we search backwards (most recent first)
        # because the button timestamp is likely very recent.
        history_list = list(self.raw_history)  # Snapshot for iteration

        g2 = None
        g1 = None

        for i in range(len(history_list) - 1, 0, -1):
            t_current = history_list[i].header.stamp.sec + (
                history_list[i].header.stamp.nanosec / 1e9
            )
            t_prev = history_list[i - 1].header.stamp.sec + (
                history_list[i - 1].header.stamp.nanosec / 1e9
            )

            if t_current >= target_time >= t_prev:
                g2 = history_list[i]
                g1 = history_list[i - 1]
                break

        if g1 and g2:
            t1 = g1.header.stamp.sec + (g1.header.stamp.nanosec / 1e9)
            t2 = g2.header.stamp.sec + (g2.header.stamp.nanosec / 1e9)

            # Linear Interpolation Factor (0 to 1)
            alpha = (target_time - t1) / (t2 - t1)

            interp_x = g1.x + alpha * (g2.x - g1.x)
            interp_y = g1.y + alpha * (g2.y - g1.y)
            return (interp_x, interp_y)

        # If target_time is newer than our newest gaze, we extrapolate (risky)
        # or just return the latest sample.
        return None

    # ---------------- HELPER ----------------
    def finalize_and_send_segment(self):
        """
        Validates the current buffer and sends it to the Learner.
        Called by Saccades, Blinks, and Look-Aways.
        """
        # 1. Check if we have enough samples to be mathematically useful
        if len(self.active_segment_samples) >= self.min_samples:

            # 2. Trim the start padding (100ms) to ensure we aren't
            # including the "landing" part of the previous saccade
            if len(self.active_segment_samples) > self.pad_samples * 2:
                trimmed_samples = self.active_segment_samples[self.pad_samples :]
            else:
                trimmed_samples = self.active_segment_samples

            # 3. Construct and Publish Batch
            batch = InteractionSegment()
            batch.header.stamp = self.get_clock().now().to_msg()
            batch.button_id = self.current_button_target.button_id
            batch.target_pixel = Point(
                x=float(self.current_button_target.center_x),
                y=float(self.current_button_target.center_y),
            )
            batch.samples = trimmed_samples

            self.segment_pub.publish(batch)
            self.get_logger().info(
                f"Sent segment: {len(trimmed_samples)} samples for {batch.button_id}"
            )

        # 4. Clear the buffer regardless of whether it was sent
        self.active_segment_samples = []


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
