#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
import numpy as np
from threading import Lock, RLock  # Add RLock to imports

from collections import deque
from statistics import median

# Messages
from std_msgs.msg import Float32, Header
from geometry_msgs.msg import Point, PointStamped
from pupil_neon_ros.msg import GazeData, GazeEvent
from gaze_interaction_manager.msg import ButtonStatus
from gaze_interaction_manager.msg import InteractionSegment, CalibrationModel

import cv2  # New: for plotting
from cv_bridge import CvBridge  # New: for ROS image conversion
from sensor_msgs.msg import Image  # New: for RViz output


class GazeController(Node):
    def __init__(self):
        super().__init__("gaze_controller")
        self._lock = Lock()
        self.bridge = CvBridge()

        self.get_logger().info("Gaze Controller Node Initialized")

        # --- 1. Parameters ---
        self.declare_parameter("history_length_s", 15.0)
        self.declare_parameter("internal_pipeline_delay_ms", 0.0)
        self.declare_parameter(
            "use_button_termination", True
        )  # If False, only gaze events end segments
        self.declare_parameter("median_window", 20)
        self.declare_parameter("ema_alpha", 0.2)
        self.declare_parameter("edge_margin", 50)

        self.declare_parameter(
            "pad_duration_ms", 200.0
        )  # Padding for trimming the START of event
        self.declare_parameter(
            "terminal_trim_ms", 200.0
        )  # Padding for trimming the END of event
        self.declare_parameter("min_event_duration_ms", 200.0)
        self.declare_parameter("max_offset_px", 200.0)
        self.declare_parameter("compensation_active", False)
        self.declare_parameter("use_temporal_alignment", False)

        # --- 2. Circular Buffers ---
        # Gaze History: [timestamp, x, y]
        self.hz_gaze = 200
        self.gaze_ptr = 0
        self.gaze_buffer_filled = False
        self.update_internal_params()

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
        self.coeffs_x[5], self.coeffs_y[5] = 0.0, 0.0  # Bias terms

        self.is_recording = False
        self.rec_start_ts = None
        self.last_valid_btn_ts = (
            0.0  # FIX: Track last valid timestamp from active button
        )
        self.active_button_id = None
        self.in_saccade, self.in_blink = False, False
        self.latest_gaze_time = 0.0

        # Latency/RMS Tracking
        self.mean_latency = 0.0
        self.sq_latency_ema = 0.0  # For RMS calculation
        self.latency_ema_alpha = 0.05

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

        self.debug_pub_viz = self.create_publisher(
            Image, "debug/interaction_plot", 10
        )  # New Viz Pub

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

        self.add_on_set_parameters_callback(self.param_callback)

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
        self.gaze_buffer_size = int(
            self.get_parameter("history_length_s").value * self.hz_gaze
        )
        self.gaze_history = np.zeros((self.gaze_buffer_size, 3))  # [ts, x, y]

        # Buffer Resizing
        new_size = int(self.get_parameter("history_length_s").value * self.hz_gaze)

        # Only re-init if size actually changed to avoid losing data on minor param tweaks
        if self.gaze_history is None or new_size != len(self.gaze_history):
            self.get_logger().info(f"Initializing Gaze Buffer: {new_size} samples")
            self.gaze_buffer_size = new_size
            self.gaze_history = np.zeros((self.gaze_buffer_size, 3))
            self.gaze_ptr = 0
            self.gaze_buffer_filled = False  # CRITICAL FIX

    def param_callback(self, params):
        self.update_internal_params()
        return SetParametersResult(successful=True)

    def gaze_cb(self, msg: GazeData):
        with self._lock:
            ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
            self.latest_gaze_time = ts

            # --- A. HIGH SPEED STORAGE (NumPy Circular Buffer) ---
            self.gaze_history[self.gaze_ptr] = [ts, msg.x, msg.y]
            self.gaze_ptr = (self.gaze_ptr + 1) % self.gaze_buffer_size
            if self.gaze_ptr == 0:
                self.gaze_buffer_filled = True

            # --- B. SMOOTHING (Median + EMA) ---
            if self.gaze_buffer_filled or self.gaze_ptr >= self.median_window:
                idx = (
                    np.arange(self.gaze_ptr - self.median_window, self.gaze_ptr)
                    % self.gaze_buffer_size
                )
                window = self.gaze_history[idx]
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
            if self.get_parameter("compensation_active").value:
                dx, dy = self.get_quadratic_correction(self.smoothed_x, self.smoothed_y)
                dx = np.clip(dx, -self.max_offset, self.max_offset)
                dy = np.clip(dy, -self.max_offset, self.max_offset)
            else:
                dx, dy = 0.0, 0.0

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
                trim_s = self.get_parameter("terminal_trim_ms").value / 1000.0
                self.finalize_and_send_segment(ts - trim_s)

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
            is_pos_valid = (
                abs(msg.button.center_x) > 1e-5 and abs(msg.button.center_y) > 1e-5
            )
            is_active = msg.button_status == ButtonStatus.BUTTON_ACTIVE

            # Store ground truth history for interpolation
            if is_pos_valid:
                self.btn_history.append(
                    (
                        adjusted_ts,
                        msg.button.center_x,
                        msg.button.center_y,
                        msg.button.button_id,
                        is_active,
                    )
                )
                self.last_valid_btn_ts = adjusted_ts

            # 3. Handle Transitions
            if is_active and is_pos_valid:
                # Rising Edge: Start Recording only if we have valid coordinates
                # Update the last known valid timestamp for the ground truth
                if not self.is_recording:
                    # Rising Edge: Start Recording
                    self.is_recording = True
                    self.rec_start_ts = adjusted_ts
                    self.current_button_id = msg.button.button_id

            elif not is_active and self.is_recording:
                # Falling Edge: Button Release
                if self.get_parameter("use_button_termination").value:
                    # FIX: Use the last known valid timestamp, not the current (potentially 0) adjusted_ts
                    # Also apply the terminal trim (~100ms)
                    trim_s = self.get_parameter("terminal_trim_ms").value / 1000.0
                    end_point = self.last_valid_btn_ts - trim_s
                    self.finalize_and_send_segment(end_point)

    def finalize_and_send_segment(self, end_ts):
        """Extracts 200Hz gaze slice and interpolates 30Hz button ground truth."""
        self.get_logger().info(
            f"Finalizing segment for button {self.current_button_id} with end timestamp {end_ts:.3f}"
        )

        if not self.is_recording or self.rec_start_ts is None:
            return

        # 1. Extraction: Get all rows with a valid timestamp
        # This handles wrapping automatically because we sort by timestamp

        # 1. Slice Gaze Buffer
        data = (
            np.roll(self.gaze_history, -self.gaze_ptr, axis=0)
            if self.gaze_buffer_filled
            else self.gaze_history[: self.gaze_ptr]
        )
        valid_mask = data[:, 0] > 0
        data = data[valid_mask]

        if len(data) < 2:
            self.get_logger().warning("Not enough valid gaze data to finalize segment.")
            self.reset_recording_state()
            return

        # Sort chronologically
        data = data[np.argsort(data[:, 0])]
        g_times = data[:, 0]

        # 2. Windowing
        raw_idx = np.where((g_times >= self.rec_start_ts) & (g_times <= end_ts))[0]
        total_samples = self.pad_samples + self.min_samples

        # Check if we have enough data (Padding + Minimum duration)
        if len(raw_idx) < total_samples:
            self.get_logger().info(
                f"Segment too short ({len(raw_idx)} samples). Discarding."
            )
            self.reset_recording_state()
            return

        # Apply padding: remove the first few samples where eyes were still moving
        # Apply internal padding (trim the start of the event where eyes are settling)
        trimmed_idx = raw_idx[self.pad_samples :]

        # 2. Match and Interpolate
        ## Slice buttons coordinates
        btn_data = list(self.btn_history)
        if not btn_data:
            self.get_logger().warning(
                "Button history is empty, cannot interpolate ground truth for segment."
            )
            self.reset_recording_state()
            return

        b_times = np.array([b[0] for b in btn_data])
        if len(b_times) < 2:
            self.get_logger().warning("Not enough valid button history to interpolate.")
            self.reset_recording_state()
            return
        b_xs, b_ys = np.array([b[1] for b in btn_data]), np.array(
            [b[2] for b in btn_data]
        )

        # Sort button data
        order = np.argsort(b_times)
        b_times = b_times[order]
        b_xs, b_ys = b_xs[order], b_ys[order]

        # Get the toggle value
        use_alignment = self.get_parameter("use_temporal_alignment").value

        gaze_slice = data[trimmed_idx]
        segment = InteractionSegment()
        segment.header.stamp = self.get_clock().now().to_msg()
        segment.button_id = self.current_button_id

        # Interpolate button center for every gaze timestamp
        for gt, gx, gy in gaze_slice:
            if use_alignment:
                # Standard Mode: Temporal Interpolation
                target_x = np.interp(gt, b_times, b_xs)
                target_y = np.interp(gt, b_times, b_ys)
            else:
                # Snapshot Mode: Use latest known point before or at gaze timestamp
                # Find indices where button time is less than or equal to gaze time
                valid_mask = b_times <= gt
                if np.any(valid_mask):
                    idx = np.where(valid_mask)[0][-1]
                    target_x = b_xs[idx]
                    target_y = b_ys[idx]
                else:
                    # Fallback if no prior data exists
                    target_x = b_xs[0]
                    target_y = b_ys[0]

            # Pack GazeData (Preserving 200Hz)
            g_msg = GazeData()
            g_msg.header.stamp = self.float_to_stamp(gt)
            g_msg.x, g_msg.y = float(gx), float(gy)

            segment.samples.append(g_msg)
            self.get_logger().info(
                f"Interpolated GT for gaze at {gt:.3f}s: ({gx:.1f}, {gy:.1f}) -> ({target_x:.1f}, {target_y:.1f})"
            )

        # Representative target (mean of the button's position during the slice)
        segment.target_pixel = Point(x=float(np.mean(b_xs)), y=float(np.mean(b_ys)))
        self.segment_pub.publish(segment)
        self.get_logger().info(
            f"Published segment: {len(segment.samples)} samples @ 200Hz for ID {segment.button_id}"
        )

        # 3. GENERATE DEBUG PLOT
        self.plot_debug_viz(data, btn_data, self.rec_start_ts, end_ts, trimmed_idx)
        self.reset_recording_state()

    def plot_debug_viz(self, gaze_data, btn_data, start_ts, end_ts, used_indices):
        """Creates a 1200x400 image. Handles coordinate conversion strictly for OpenCV."""
        W, H = 1200, 400
        img = np.zeros((H, W, 3), dtype=np.uint8)

        if len(gaze_data) < 2:
            return

        # Use actual data limits for scaling to prevent "empty" plots due to time gaps
        t_min = float(np.min(gaze_data[:, 0]))
        t_max = float(np.max(gaze_data[:, 0]))
        t_range = t_max - t_min if t_max > t_min else 1.0

        def to_pixels(t, val, is_y=False):
            try:
                # Calculate normalized position (0.0 to 1.0)
                norm_x = (float(t) - t_min) / t_range
                # Normalize Y based on 1200 (common gaze height)
                norm_y = float(val) / 1200.0

                px_x = norm_x * (W - 40) + 20
                px_y = norm_y * (H - 40) + 20

                # CRITICAL: Convert to standard Python int and clip to prevent Overflow
                # OpenCV fails if these are numpy.int64 or outside visible range
                return (
                    int(np.clip(px_x, -100, W + 100)),
                    int(np.clip(px_y, -100, H + 100)),
                )
            except (ValueError, TypeError):
                return None

        # 1. Background blocks (Button Activity)
        for i in range(len(btn_data) - 1):
            t1, _, _, _, act = btn_data[i]
            t2, _, _, _, _ = btn_data[i + 1]
            p1 = to_pixels(t1, 0)
            p2 = to_pixels(t2, 0)
            if p1 and p2:
                # Force standard int tuples for OpenCV
                cv2.rectangle(
                    img, (p1[0], 0), (p2[0], H), (0, 30, 0) if act else (0, 0, 30), -1
                )

        # 2. History (Blue) & 3. Segment (Yellow)
        for i, (t, gx, gy) in enumerate(gaze_data):
            p = to_pixels(t, gx)
            if p:
                is_used = i in used_indices
                use_alignment = self.get_parameter("use_temporal_alignment").value
                if is_used:

                    if use_alignment:
                        color = (0, 255, 255)
                    else:
                        color = (0, 255, 0)
                else:
                    color = (200, 100, 50)
                radius = 2 if is_used else 1
                cv2.circle(img, p, radius, color, -1)

        # 4. Truth Line (White)
        btn_pts = []
        for b in btn_data:
            p = to_pixels(b[0], b[1])
            if p:
                btn_pts.append(p)

        if len(btn_pts) > 1:
            # Ensure we pass a list of numpy int32 arrays to polylines
            cv2.polylines(
                img, [np.array(btn_pts, dtype=np.int32)], False, (255, 255, 255), 1
            )

        # 5. Timing Markers
        ps = to_pixels(start_ts, 0)
        pe = to_pixels(end_ts, 0)
        if ps:
            cv2.line(img, (ps[0], 0), (ps[0], H), (255, 255, 0), 2)
        if pe:
            cv2.line(img, (pe[0], 0), (pe[0], H), (0, 255, 255), 2)

        # Publish
        try:
            msg = self.bridge.cv2_to_imgmsg(img, encoding="bgr8")
            msg.header.stamp = self.get_clock().now().to_msg()
            self.debug_pub_viz.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Viz Error: {e}")

    def reset_recording_state(self):
        self.is_recording = False
        self.rec_start_ts = None
        self.last_valid_btn_ts = 0.0

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
        # self.debug_pub_hover.publish(
        #     Float32(data=1.0 - offset if self.is_hovering else 0.0)
        # )
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
