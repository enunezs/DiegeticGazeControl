#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
import numpy as np
from threading import Lock
from collections import deque
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
        self.declare_parameter("history_length_s", 5.0)
        self.declare_parameter("internal_pipeline_delay_ms", 0.0)
        self.declare_parameter(
            "use_button_termination", True
        )  # If False, only gaze events end segments
        self.declare_parameter("median_window", 20)
        self.declare_parameter("ema_alpha", 0.2)
        self.declare_parameter("edge_margin", 100)
        self.declare_parameter("pad_duration_ms", 100.0)
        self.declare_parameter("min_event_duration_ms", 200.0)
        self.declare_parameter("max_offset_px", 200.0)
        self.declare_parameter("compensation_active", False)

        self.add_on_set_parameters_callback(self.param_callback)
        self.update_internal_params()

        # --- 2. Circular Buffers ---
        # Gaze History: [timestamp, x, y]
        self.hz_gaze = 200

        self.gaze_buf_size = int(
            self.get_parameter("history_length_s").value * self.hz_gaze
        )
        self.gaze_history = np.zeros((self.gaze_buf_size, 3))  # [ts, x, y]
        self.gaze_ptr = 0
        self.gaze_filled = False

        # Button History (Ground Truth): stores (adj_timestamp, x, y, id, is_active)
        # Used for linear interpolation against the gaze timestamps
        self.btn_history = deque(
            maxlen=int(self.get_parameter("history_length_s").value * 40)
        )

        # --- 3. State & Metrics ---
        self.smoothed_x = 0.0
        self.smoothed_y = 0.0
        self.coeffs_x = np.zeros(6)
        self.coeffs_y = np.zeros(6)

        self.is_recording = False
        self.rec_start_ts = None
        self.active_button_id = None

        self.coeffs_x[5], self.coeffs_y[5] = 0.0, 0.0  # Bias terms

        self.in_saccade = False
        self.in_blink = False
        self.latest_gaze_time = 0.0

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
        self.median_window = self.get_parameter("median_window").value
        self.ema_alpha = self.get_parameter("ema_alpha").value
        self.edge_margin = self.get_parameter("edge_margin").value
        self.max_offset = self.get_parameter("max_offset_px").value

        self.pad_samples = int(
            (self.get_parameter("pad_duration_ms").value / 1000.0) * self.hz_gaze
        )
        self.min_samples = int(
            (self.get_parameter("min_event_duration_ms").value / 1000.0) * self.hz_gaze
        )

        # self.history_depth_samples = int(
        #     self.get_parameter("history_length_s").value * hz
        # )

    def param_callback(self, params):
        self.update_internal_params()
        return SetParametersResult(successful=True)

    def gaze_cb(self, msg: GazeData):
        with self._lock:
            ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
            self.latest_gaze_time = ts

            # --- A. HIGH SPEED STORAGE (NumPy Circular Buffer) ---
            self.gaze_history_np[self.gaze_ptr] = [ts, msg.x, msg.y]
            self.gaze_ptr = (self.gaze_ptr + 1) % self.buffer_max_size
            if self.gaze_ptr == 0:
                self.buffer_filled = True

            # --- B. SMOOTHING (Median + EMA) ---
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

            # --- D. BOUNDARY MONITORING ---
            in_fov = (
                self.edge_margin < msg.x < 1600 - self.edge_margin
                and self.edge_margin < msg.y < 1200 - self.edge_margin
            )

            is_clean = (
                in_fov
                and not self.in_saccade
                and not self.in_blink
                # and not event_padding_active
            )

            # If gaze becomes "dirty", terminate segment immediately
            if self.is_recording and not is_clean:
                self.finalize_and_send_segment(ts)

            # Debug signals
            self.publish_debug_signals(in_fov, is_clean)

    def button_cb(self, msg: ButtonStatus):
        """
        Triggered at ~30Hz. Performs the heavy time-matching and error calculation.
        """

        # TODO: Calculated wrong
        # arrival_time_ns = self.get_clock().now().nanoseconds
        # last_gaze_time = self.latest_gaze_time

        with self._lock:
            # 1. Temporal Registration + Latency relative to the gaze stream
            button_capture_ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
            if self.latest_gaze_time > 0 and button_capture_ts > 0:
                latency_sec = self.latest_gaze_time - button_capture_ts
                latency_ms = latency_sec * 1000.0
                self.update_latency_metrics(latency_ms)

            # 2. Adjust for vision pipeline delay
            adjusted_ts = button_capture_ts - (
                self.get_parameter("internal_pipeline_delay_ms").value / 1000.0
            )
            is_active = msg.button_status == ButtonStatus.BUTTON_ACTIVE

            # Store ground truth history for interpolation
            self.btn_history.append(
                (
                    adjusted_ts,
                    msg.button.center_x,
                    msg.button.center_y,
                    msg.button.button_id,
                    is_active,
                )
            )

            # 3. Handle Transitions
            if is_active and not self.is_recording:
                # Start Recording (Rising Edge)
                self.is_recording = True
                self.rec_start_ts = adjusted_ts
                self.current_button_id = msg.button.button_id

            elif not is_active and self.is_recording:
                # End Recording (Falling Edge)
                if self.get_parameter("use_button_termination").value:
                    self.finalize_and_send_segment(adjusted_ts)

    def finalize_and_send_segment(self, end_ts):
        """Extracts 200Hz gaze slice and interpolates 30Hz button ground truth."""
        if not self.is_recording or self.rec_start_ts is None:
            return

        # 1. Slice Gaze Buffer
        data = (
            np.roll(self.gaze_history_np, -self.gaze_ptr, axis=0)
            if self.buffer_filled
            else self.gaze_history_np[: self.gaze_ptr]
        )
        g_times = data[:, 0]
        idx = np.where((g_times >= self.rec_start_ts) & (g_times <= end_ts))[0]

        if len(idx) < self.min_samples:
            self.is_recording = False
            return

        # 2. Apply Padding (Trimming)
        if len(idx) > self.pad_samples * 2:
            idx = idx[self.pad_samples : -self.pad_samples]

        gaze_slice = data[idx]

        # 3. Interpolate Button Ground Truth
        btn_data = list(self.btn_history)
        if not btn_data:
            return
        b_times = np.array([b[0] for b in btn_data])
        b_xs, b_ys = np.array([b[1] for b in btn_data]), np.array(
            [b[2] for b in btn_data]
        )

        segment = InteractionSegment()
        segment.header.stamp = self.get_clock().now().to_msg()
        segment.button_id = self.current_button_id

        # We find the exact button target for EVERY gaze sample
        for gt, gx, gy in gaze_slice:
            target_x = np.interp(gt, b_times, b_xs)
            target_y = np.interp(gt, b_times, b_ys)

            # Pack GazeData (Preserving 200Hz)
            g_msg = GazeData()
            g_msg.header.stamp = self.float_to_stamp(gt)
            g_msg.x, g_msg.y = gx, gy
            segment.samples.append(g_msg)

        # Representative target (mean of the button's position during the slice)
        segment.target_pixel = Point(x=float(np.mean(b_xs)), y=float(np.mean(b_ys)))

        self.segment_pub.publish(segment)
        self.is_recording = False
        self.rec_start_ts = None
        self.get_logger().info(
            f"Published segment: {len(segment.samples)} samples @ 200Hz"
        )

    def get_quadratic_correction(self, x, y):
        feats = np.array([x**2, y**2, x * y, x, y, 1.0])
        return np.dot(self.coeffs_x, feats), np.dot(self.coeffs_y, feats)

    def update_latency_metrics(self, lat):
        # lat is in milliseconds
        # Exponential Moving Average for Mean
        self.mean_latency = (self.latency_ema_alpha * lat) + (
            1 - self.latency_ema_alpha
        ) * self.mean_latency

        # Exponential Moving Average for Mean Square
        self.sq_latency_ema = (self.latency_ema_alpha * (lat**2)) + (
            1 - self.latency_ema_alpha
        ) * self.sq_latency_ema

        # Calculate RMS
        rms = np.sqrt(max(0.0, self.sq_latency_ema))

        self.debug_pub_latency.publish(Float32(data=float(lat)))
        self.debug_pub_latency_rms.publish(Float32(data=float(rms)))

        # Throttle logs so they don't flood the terminal (every ~10 second at 30Hz)
        self.get_logger().info(
            f"Gaze to camera pipeline latency: {lat:.1f}ms | RMS: {rms:.1f}ms",
            throttle_duration_sec=10.0,
        )

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
            self.coeffs_x, self.coeffs_y = np.array(msg.coeffs_x), np.array(
                msg.coeffs_y
            )

    def saccade_cb(self, msg: GazeEvent):
        with self._lock:
            self.in_saccade = msg.event_type == "START"

    def blink_cb(self, msg: GazeEvent):
        with self._lock:
            self.in_blink = msg.event_type == "START"

    def float_to_stamp(self, t_float):
        t = Header().stamp
        t.sec, t.nanosec = int(t_float), int((t_float - int(t_float)) * 1e9)
        return t


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
