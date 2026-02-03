#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult
import numpy as np
from threading import Lock
from statistics import median

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

        # --- 1. Parameters ---
        self.declare_parameter("median_window", 20)
        self.declare_parameter("ema_alpha", 0.2)
        self.declare_parameter("edge_margin", 100)
        self.declare_parameter("pad_duration_ms", 100.0)
        self.declare_parameter("min_event_duration_ms", 200.0)
        self.declare_parameter("history_length_s", 5.0)
        self.declare_parameter("max_offset_px", 200.0)
        self.declare_parameter("compensation_active", False)

        # New Latency Tuning Parameter
        self.declare_parameter("internal_pipeline_delay_ms", 0.0)

        self.add_on_set_parameters_callback(self.param_callback)
        self.update_internal_params()

        # --- 2. Efficient Buffers (NumPy) ---
        # We store [timestamp, x, y] in a pre-allocated array
        self.buffer_max_size = self.history_depth_samples
        self.gaze_history_np = np.zeros((self.buffer_max_size, 3))
        self.gaze_ptr = 0
        self.buffer_filled = False

        # Legacy buffer for "InteractionSegments" (as these require full objects)
        self.active_segment_samples = []

        # --- 3. State & Metrics ---
        self.smoothed_x = 0.0
        self.smoothed_y = 0.0
        self.coeffs_x = np.zeros(6)
        self.coeffs_y = np.zeros(6)
        self.coeffs_x[5], self.coeffs_y[5] = 0.0, 0.0  # Bias terms

        self.is_hovering = False
        self.in_saccade = False
        self.in_blink = False
        self.last_event_time = 0.0

        # Latency/RMS Tracking
        self.latency_ema_alpha = 0.05
        self.mean_latency = 0.0
        self.sq_latency_ema = 0.0  # For RMS calculation

        # --- 4. Publishers ---
        self.segment_pub = self.create_publisher(
            InteractionSegment, "calibration/interaction_segment", 10
        )
        self.corrected_gaze_pub = self.create_publisher(
            PointStamped, "gaze_controller/corrected_gaze", 10
        )

        # Debug Publishers
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

        # Timing Debug
        self.debug_pub_latency = self.create_publisher(Float32, "debug/latency_ms", 10)
        self.debug_pub_latency_rms = self.create_publisher(
            Float32, "debug/latency_rms", 10
        )

        # --- 5. Subscriptions ---
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

    def update_internal_params(self):
        hz = 200.0
        self.median_window = self.get_parameter("median_window").value
        self.ema_alpha = self.get_parameter("ema_alpha").value
        self.edge_margin = self.get_parameter("edge_margin").value
        self.max_offset = self.get_parameter("max_offset_px").value
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

    def gaze_cb(self, msg: GazeData):
        with self._lock:
            now_s = self.get_clock().now().nanoseconds / 1e9
            ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)

            # --- A. HIGH SPEED STORAGE (NumPy Circular Buffer) ---
            self.gaze_history_np[self.gaze_ptr] = [ts, msg.x, msg.y]
            self.gaze_ptr = (self.gaze_ptr + 1) % self.buffer_max_size
            if self.gaze_ptr == 0:
                self.buffer_filled = True

            # --- B. SMOOTHING (Keep in Gaze CB for low latency output) ---
            # Get latest window from circular buffer
            if self.buffer_filled or self.gaze_ptr >= self.median_window:
                idx = (
                    np.arange(self.gaze_ptr - self.median_window, self.gaze_ptr)
                    % self.buffer_max_size
                )
                window = self.gaze_history_np[idx]
                mx = np.median(window[:, 1])
                my = np.median(window[:, 2])
                self.smoothed_x = (self.ema_alpha * mx) + (
                    1 - self.ema_alpha
                ) * self.smoothed_x
                self.smoothed_y = (self.ema_alpha * my) + (
                    1 - self.ema_alpha
                ) * self.smoothed_y
            else:
                self.smoothed_x, self.smoothed_y = msg.x, msg.y

            # --- C. CORRECTION & PUBLISH ---
            dx, dy = self.get_quadratic_correction(self.smoothed_x, self.smoothed_y)
            if not self.get_parameter("compensation_active").value:
                dx, dy = 0.0, 0.0

            dx = np.clip(dx, -self.max_offset, self.max_offset)
            dy = np.clip(dy, -self.max_offset, self.max_offset)

            out_msg = PointStamped()
            out_msg.header = msg.header
            out_msg.point = Point(x=self.smoothed_x - dx, y=self.smoothed_y - dy, z=0.0)
            self.corrected_gaze_pub.publish(out_msg)

            # --- D. LOGIC FOR DATA COLLECTION ---
            in_fov = (
                self.edge_margin < msg.x < 1600 - self.edge_margin
                and self.edge_margin < msg.y < 1200 - self.edge_margin
            )
            event_padding_active = (now_s - self.last_event_time) < (
                self.get_parameter("pad_duration_ms").value / 1000.0
            )
            is_clean = (
                in_fov
                and not self.in_saccade
                and not self.in_blink
                and not event_padding_active
            )

            if self.is_hovering:
                if is_clean:
                    self.active_segment_samples.append(msg)
                else:
                    self.finalize_and_send_segment()

            # Debug signals
            self.publish_debug_signals(in_fov, is_clean)

    def button_cb(self, msg: ButtonStatus):
        """
        Triggered at ~30Hz. Performs the heavy time-matching and error calculation.
        """
        arrival_time_ns = self.get_clock().now().nanoseconds

        with self._lock:
            # 1. Temporal Registration
            capture_ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
            # Adjust for known pipeline delay (shutter to CPU)
            adj_capture_ts = capture_ts - (
                self.get_parameter("internal_pipeline_delay_ms").value / 1000.0
            )

            matched_gaze = self.get_interpolated_gaze(adj_capture_ts)

            if matched_gaze:
                gx, gy = matched_gaze
                # Calculate Spacial Error (for future model training)
                err_x = gx - msg.button.center_x
                err_y = gy - msg.button.center_y

                # 2. Quantify Latency (Arrival vs Capture)
                latency_ms = (arrival_time_ns - (capture_ts * 1e9)) / 1e6
                self.update_latency_metrics(latency_ms)

            # 3. Handle Hover Logic
            new_hover_state = msg.button_status == ButtonStatus.BUTTON_ACTIVE
            if new_hover_state != self.is_hovering:
                if not new_hover_state:
                    self.finalize_and_send_segment()
                self.is_hovering = new_hover_state
                self.current_button_target = msg.button if self.is_hovering else None

    def get_interpolated_gaze(self, target_t):
        """
        Finds exact gaze coordinates at target_t using the NumPy buffer.
        """
        if not self.buffer_filled and self.gaze_ptr < 2:
            self.get_logger().warning("Not enough gaze data for interpolation.")
            return None

        # Get a copy of valid data, sorted by time
        if self.buffer_filled:
            # Linearize the circular buffer: [oldest -> newest]
            data = np.roll(self.gaze_history_np, -self.gaze_ptr, axis=0)
        else:
            data = self.gaze_history_np[: self.gaze_ptr]

        times = data[:, 0]

        # Find position where target_t would be inserted
        idx = np.searchsorted(times, target_t)

        if idx == 0 or idx >= len(times):
            self.get_logger().warning(
                f"Target time is outside the gaze data buffer range. Difference of {target_t - times[0]:.3f}s to {target_t - times[-1]:.3f}s."
            )
            return None  # target_t is outside our buffer range

        # Linear Interpolation
        t1, x1, y1 = data[idx - 1]
        t2, x2, y2 = data[idx]

        fraction = (target_t - t1) / (t2 - t1)
        interp_x = x1 + fraction * (x2 - x1)
        interp_y = y1 + fraction * (y2 - y1)

        return interp_x, interp_y

    def update_latency_metrics(self, lat):
        # EMA
        self.mean_latency = (self.latency_ema_alpha * lat) + (
            1 - self.latency_ema_alpha
        ) * self.mean_latency
        # RMS (via EMA of square)
        self.sq_latency_ema = (self.latency_ema_alpha * (lat**2)) + (
            1 - self.latency_ema_alpha
        ) * self.sq_latency_ema
        rms = np.sqrt(self.sq_latency_ema)

        self.debug_pub_latency.publish(Float32(data=float(lat)))
        self.debug_pub_latency_rms.publish(Float32(data=float(rms)))

    def get_quadratic_correction(self, x, y):
        feats = np.array([x**2, y**2, x * y, x, y, 1.0])
        return np.dot(self.coeffs_x, feats), np.dot(self.coeffs_y, feats)

    def publish_debug_signals(self, in_fov, is_clean):
        offset = 0.1
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
        self.debug_pub_clean.publish(Float32(data=5.0 - offset if is_clean else 4.0))

    def model_cb(self, msg: CalibrationModel):
        with self._lock:
            self.coeffs_x = np.array(msg.coeffs_x)
            self.coeffs_y = np.array(msg.coeffs_y)
            self.get_logger().info("Updated calibration coefficients.")

    def saccade_cb(self, msg: GazeEvent):
        with self._lock:
            self.last_event_time = self.get_clock().now().nanoseconds / 1e9
            self.finalize_and_send_segment()

    def blink_cb(self, msg: GazeEvent):
        with self._lock:
            self.last_event_time = self.get_clock().now().nanoseconds / 1e9
            self.finalize_and_send_segment()

    def finalize_and_send_segment(self):
        if len(self.active_segment_samples) >= self.min_samples:
            if len(self.active_segment_samples) > self.pad_samples * 2:
                trimmed = self.active_segment_samples[self.pad_samples :]
            else:
                trimmed = self.active_segment_samples

            batch = InteractionSegment()
            batch.header.stamp = self.get_clock().now().to_msg()
            batch.button_id = self.current_button_target.button_id
            batch.target_pixel = Point(
                x=float(self.current_button_target.center_x),
                y=float(self.current_button_target.center_y),
            )
            batch.samples = trimmed
            self.segment_pub.publish(batch)
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
