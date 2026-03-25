#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
import numpy as np
from threading import Lock  # Add RLock to imports

from collections import deque

# Messages
from std_msgs.msg import Float32, Header
from geometry_msgs.msg import Point, PointStamped
from pupil_neon_ros.msg import GazeData, GazeEvent
from gaze_interaction_manager.msg import ButtonStatus, ButtonStatusArray
from gaze_interaction_manager.msg import InteractionSegment, CalibrationModel

import cv2  # For plotting
from cv_bridge import CvBridge  # for ROS image conversion
from sensor_msgs.msg import Image  # for RViz output


class GazeController(Node):

### === 1. Initialization & Parameters === ###

    def __init__(self):
        super().__init__("gaze_controller")
        self._lock = Lock()
        self.bridge = CvBridge()

        self.get_logger().info("Gaze Controller Node Initialized")

        # --- 1. Parameters ---
        # Filtering
        self.declare_parameter("history_length_s", 5.0)
        self.declare_parameter("internal_pipeline_delay_ms", 0.0)
        self.declare_parameter("median_window", 20)
        self.declare_parameter("ema_alpha", 0.2)
        self.declare_parameter("edge_margin", 50)

        # Timing properties
        self.declare_parameter(
            "pad_duration_ms", 100.0
        )  # Padding for trimming the START of event
        self.declare_parameter(
            "terminal_trim_ms", 100.0
        )  # Padding for trimming the END of event
        self.declare_parameter("min_event_duration_ms", 200.0)

        self.declare_parameter("compensation_active", True)
        self.declare_parameter("max_compensation_px", 200.0)
        self.declare_parameter("use_temporal_alignment", True)
        self.declare_parameter("sticky_button_interaction", True)
        self.declare_parameter(
            "use_button_termination", False  # TODO: Repeated!
        )  # If False, only gaze events end segments

        # --- New Visualization Parameters ---
        self.declare_parameter("viz_enabled", True)
        self.declare_parameter("viz_show_raw", True)
        self.declare_parameter("viz_show_corrected", True)
        self.declare_parameter("viz_show_history", True)
        self.declare_parameter("viz_show_buttons", True)
        self.declare_parameter("viz_show_all_buttons", True)
        self.declare_parameter("viz_show_vectors", True)
        self.declare_parameter("viz_show_field", True)

        self.declare_parameter(
            "viz_history_limit", 50
        )  # Number of past gaze points to show

        # --- 2. Circular Buffers ---
        # Gaze History: [timestamp, x, y]
        self.hz_gaze = 200
        self.gaze_ptr = 0
        self.gaze_buffer_filled = False
        self.update_internal_params()

        # Button History (Ground Truth): stores (adj_timestamp, x, y, id, is_active),  for linear interpolation against gaze timestamps
        self.btn_history = deque(
            maxlen=int(self.get_parameter("history_length_s").value * 40)
        )

        self.latest_all_buttons = []  # <--- Stores the snapshot for background drawing

        # --- 3. State & Metrics ---
        self.smoothed_x, self.smoothed_y = 0.0, 0.0
        self.model_type = CalibrationModel.TYPE_BIAS
        self.coeffs_x, self.coeffs_y = np.zeros(6), np.zeros(6)
        self.coeffs_x[5], self.coeffs_y[5] = 0.0, 0.0  # Bias terms

        self.is_recording = False
        self.rec_start_ts = None
        self.current_button_id = None
        self.last_valid_btn_ts = 0.0
        self.latest_gaze_time = 0.0
        self.in_saccade, self.in_blink = False, False

        self.button_engaged = False # New: tracks if the button is physically held


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

        self.latest_raw_button_msg = None  # To store the last geometric data
        self.robot_output_timer = self.create_timer(1.0/30.0, self.publish_to_robot_loop)

        # New Publisher for the filtered teleop command
        self.teleop_pub = self.create_publisher(
            ButtonStatus, "gaze_controller/teleop_filtered", 10
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
            Image, "gaze_controller/interaction_plot", 10
        )  # New Viz Pub

        # New Publisher for the Live Debug Image
        self.live_viz_pub = self.create_publisher(
            Image, "gaze_controller/live_debug_canvas", 10
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
        if self.get_parameter("viz_show_all_buttons").value:
            self.create_subscription(
                ButtonStatusArray, "/dwell_time/input_status", self.all_buttons_cb, 10
            )

        self.add_on_set_parameters_callback(self.param_callback)

    def update_internal_params(self):
        self.median_window = self.get_parameter("median_window").value
        self.ema_alpha = self.get_parameter("ema_alpha").value
        self.edge_margin = self.get_parameter("edge_margin").value
        self.max_compensation = self.get_parameter("max_compensation_px").value

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

### === 2. Core Callbacks: Gaze === ###

    def gaze_cb(self, msg: GazeData):
        with self._lock:
            ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
            self.latest_gaze_time = ts

            # --- A. HIGH SPEED STORAGE (NumPy Circular Buffer) ---
            self.gaze_history[self.gaze_ptr] = [ts, msg.x, msg.y]
            self.gaze_ptr = (self.gaze_ptr + 1) % self.gaze_buffer_size
            if self.gaze_ptr == 0:
                self.gaze_buffer_filled = True

            self._process_and_publish_corrected_gaze(msg)

            # --- D. BOUNDARY MONITORING ---
            in_fov = (
                self.edge_margin < msg.x < 1600 - self.edge_margin
                and self.edge_margin < msg.y < 1200 - self.edge_margin
            )

            # If gaze becomes "dirty", terminate segment immediately
            if self.is_recording and not in_fov:
                if not self.get_parameter("sticky_button_interaction").value:
                    self._trigger_segment_end(ts, reason="OUT_OF_FOV")

            # Debug signals
            # self.publish_debug_signals(in_fov, is_clean)

    def _process_and_publish_corrected_gaze(self, msg):
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
            dx, dy = self.get_correction(self.smoothed_x, self.smoothed_y)
            dx = np.clip(dx, -self.max_compensation, self.max_compensation)
            dy = np.clip(dy, -self.max_compensation, self.max_compensation)
        else:
            dx, dy = 0.0, 0.0

        out_msg = PointStamped()
        out_msg.header = msg.header
        out_msg.point = Point(x=self.smoothed_x + dx, y=self.smoothed_y + dy, z=0.0)
        self.corrected_gaze_pub.publish(out_msg)
    
### === Pupil Event Callbacks === ###
    def saccade_cb(self, msg: GazeEvent):
        """Handles precise termination using Pupil Native Events"""
        # Assuming GazeEvent message has start_time_ns based on your FixationEventData example
        with self._lock:
            if self.is_recording:
                # Use the exact start of the saccade provided by the glasses
                event_start_ts = msg.start_time_ns / 1e9
                self.get_logger().info(
                    f"Saccade detected! Terminating segment at {event_start_ts:.3f}"
                )
                self._trigger_segment_end(event_start_ts, reason="SACCADE")

    def blink_cb(self, msg: GazeEvent):
        with self._lock:
            if self.is_recording:
                event_start_ts = msg.start_time_ns / 1e9
                self.get_logger().info(
                    f"Blink detected! Terminating segment at {event_start_ts:.3f}"
                )
                self._trigger_segment_end(event_start_ts, reason="BLINK")

### === 2. Core Callbacks: Buttons === ###

    def button_cb(self, msg: ButtonStatus):
        """
        Triggered at ~30Hz. P
        erforms the heavy time-matching and error calculation.
        """

        with self._lock:

            
            # 1. Latency adjustment relative to the gaze stream
            # ! Not in use
            button_ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
            if self.latest_gaze_time > 0 and button_ts > 0:
                latency_sec = self.latest_gaze_time - button_ts
                latency_ms = latency_sec * 1000.0
                self.update_latency_metrics(latency_ms)

            adjusted_ts = button_ts - (
                self.get_parameter("internal_pipeline_delay_ms").value / 1000.0
            )

            # 2. Run validity check and store ground truth history for interpolation
            # Cache the geometry so we can re-broadcast it even if the Dwell node stops
            self.latest_raw_button_msg = msg 
            is_active = msg.button_status == ButtonStatus.BUTTON_ACTIVE

            is_pos_valid = (
                abs(msg.button.center_x) > 1e-5 and abs(msg.button.center_y) > 1e-5
            )
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

            # 3. Rising Edge: User starts dwelling/pressing
            if is_active and not self.button_engaged:
                self.button_engaged = True
                self.is_recording = True
                self.rec_start_ts = adjusted_ts
                self.current_button_id = msg.button.button_id
                self.get_logger().info(f"Started Recording for Button {self.current_button_id}")
                

            # 4. Falling Edge: User stops dwelling/pressing
            elif not is_active and self.button_engaged:
                self.button_engaged = False
                
                # If NOT sticky, the button release ends the segment
                if not self.get_parameter("sticky_button_interaction").value:
                    if self.is_recording:
                        trim_s = self.get_parameter("terminal_trim_ms").value / 1000.0
                        end_point = self.last_valid_btn_ts - trim_s
                        self._trigger_segment_end(end_point, reason="BUTTON_RELEASE")
                        self.get_logger().info(f"Button released. Ending segment at {end_point:.3f}")
                    else:
                        self.get_logger().info(
                            "Sticky mode: Ignoring button release, waiting for physiological signal."
                        )

            # 5. Trigger Visualization
            if self.get_parameter("viz_enabled").value:
                self.publish_live_debug_plot(msg)

    def all_buttons_cb(self, msg: ButtonStatusArray):
        """Simple storage of latest button states for background drawing."""
        if not self.get_parameter("viz_show_all_buttons").value:
            return
        with self._lock:
            self.latest_all_buttons = msg.inputs
            
    def publish_to_robot_loop(self):
        """Safety-critical heartbeat loop for teleoperation."""
        with self._lock:
            # If we've never received a button message, we can't publish anything valid yet
            if self.latest_raw_button_msg is None:
                return

            # Create a new message based on the last known geometry
            out_msg = self.latest_raw_button_msg
            out_msg.header.stamp = self.get_clock().now().to_msg()
            
            # THE FILTER:
            # Even if the Dwell Node says "INACTIVE", if we are still 'recording' 
            # (because of Sticky Mode or a Blink), we force the status to ACTIVE.
            if self.is_recording:
                out_msg.button_status = ButtonStatus.BUTTON_ACTIVE
                out_msg.button.button_id = self.current_button_id # Ensure ID is consistent
            else:
                out_msg.button_status = ButtonStatus.BUTTON_INACTIVE
                out_msg.button_id = "" # Clear ID so robot stops

            self.teleop_pub.publish(out_msg)

    def _trigger_segment_end(self, end_ts, reason="UNKNOWN"):
        """Unified finalization logic"""
        if not self.is_recording:
            return

        # self.get_logger().info(f"Finalizing segment: {reason} at {end_ts:.3f}")

        # 1. Slice and Sort Gaze
        data = (
            np.roll(self.gaze_history, -self.gaze_ptr, axis=0)
            if self.gaze_buffer_filled
            else self.gaze_history[: self.gaze_ptr]
        )
        data = data[data[:, 0] > 0]
        data = data[np.argsort(data[:, 0])]

        # 2. Windowing
        raw_idx = np.where((data[:, 0] >= self.rec_start_ts) & (data[:, 0] <= end_ts))[
            0
        ]

        # Check minimum duration
        if len(raw_idx) < (self.pad_samples + self.min_samples):
            # self.get_logger().info(
            #     f"Segment too short ({len(raw_idx)} samples). Discarding."
            # )
            pass
        else:
            # Post-hoc trimming: Remove the start padding (eye settling)
            trimmed_idx = raw_idx[self.pad_samples :]
            self._publish_segment(data[trimmed_idx], end_ts, full_context_buffer=data)

        self.is_recording = False
        self.rec_start_ts = None

    def reset_recording_state(self):
        self.is_recording = False
        self.rec_start_ts = None
        self.last_valid_btn_ts = 0.0

    def float_to_stamp(self, t_float):
        t = Header().stamp
        t.sec, t.nanosec = int(t_float), int((t_float - int(t_float)) * 1e9)
        return t

    def _publish_segment(self, gaze_slice, end_ts, full_context_buffer=None):
        """Interpolates and sends the ROS message"""
        btn_data = list(self.btn_history)
        if not btn_data:
            return

        # Extract button timestamps and positions for interpolation
        b_times = np.array([b[0] for b in btn_data])
        b_xs = np.array([b[1] for b in btn_data])
        b_ys = np.array([b[2] for b in btn_data])

        segment = InteractionSegment()
        segment.header.stamp = self.get_clock().now().to_msg()
        segment.button_id = self.current_button_id

        target_points = np.zeros((len(gaze_slice), 2))
        for i, (gt, gx, gy) in enumerate(gaze_slice):
            # 1. Calculate ground truth for this specific gaze timestamp
            tx = np.interp(gt, b_times, b_xs)
            ty = np.interp(gt, b_times, b_ys)
            target_points[i] = [tx, ty]

            # 2. Add the Target point
            t_pt = Point(x=tx, y=ty, z=0.0)
            segment.target_samples.append(t_pt)

            # 3. Add the Gaze sample
            g_msg = GazeData()
            g_msg.header.stamp = self.float_to_stamp(gt)
            g_msg.x, g_msg.y = float(gx), float(gy)
            segment.gaze_samples.append(g_msg)

        # segment.target_pixel = Point(x=float(np.mean(b_xs)), y=float(np.mean(b_ys)))
        self.segment_pub.publish(segment)

        mean_error = np.mean(
            np.sqrt((target_points[:, 0] - gaze_slice[:, 1]) ** 2 + (target_points[:, 1] - gaze_slice[:, 2]) ** 2)
        )
        self.get_logger().info(
            f"Published segment with {len(segment.gaze_samples)} samples. Mean error to GT: {mean_error:.1f}px"
        )

        # If we weren't given the full buffer, just show the slice
        highlight_ts = gaze_slice[:, 0]
        plot_data = (
            full_context_buffer if full_context_buffer is not None else gaze_slice
        )

        # Plot Debug Viz
        self.plot_debug_viz(
            plot_data, btn_data, self.rec_start_ts, end_ts, highlight_ts
        )

### === Calibration Model Handling === ###
    def model_cb(self, msg: CalibrationModel):
        with self._lock:
            if msg.model_type in [CalibrationModel.TYPE_KNN_GRID]:
                self.get_logger().warning(
                    f"Received unsupported model type: {msg.model_type}"
                )
                return

            self.model_type = msg.model_type
            self.coeffs_x, self.coeffs_y = np.array(msg.coeffs_x), np.array(
                msg.coeffs_y
            )

    def get_correction(self, x, y):
        # Ensure coefficients exist
        cx, cy = self.coeffs_x, self.coeffs_y
        if len(cx) < 6 or len(cy) < 6:
            return 0.0, 0.0

        # 1. Use relative coordinates (centered at 800, 600)
        dx = x - 800.0
        dy = y - 600.0

        # 2. Polynomial Core (Indices 0-5)
        corr_x = (
            cx[0] * dx**2
            + cx[1] * dy**2
            + cx[2] * dx * dy
            + cx[3] * dx
            + cx[4] * dy
            + cx[5]
        )
        corr_y = (
            cy[0] * dx**2
            + cy[1] * dy**2
            + cy[2] * dx * dy
            + cy[3] * dx
            + cy[4] * dy
            + cy[5]
        )
        # 3. Sigmoid Terms [6: Amp, 7: Scale]
        if len(cx) >= 8 and abs(cx[7]) > 1e-3:
            corr_x += cx[6] * np.tanh(dx / cx[7])
        if len(cy) >= 8 and abs(cy[7]) > 1e-3:
            corr_y += cy[6] * np.tanh(dy / cy[7])

        # 4. Pure Radial Term [8: k_radial]
        # Corr = k * dist * displacement
        if len(cx) >= 9 or len(cy) >= 9:
            r = np.sqrt(dx**2 + dy**2)
            if len(cx) >= 9:
                corr_x += cx[8] * (dx * r)
            if len(cy) >= 9:
                corr_y += cy[8] * (dy * r)

        return corr_x, corr_y

### === Helper Methods for Segment Handling & Visualization === ###

    def publish_live_debug_plot(self, current_btn_msg: ButtonStatus):
        # Create a black canvas (1600x1200 scaled down for performance if needed)
        # We'll use 800x600 for the actual image to save bandwidth, but map coords
        scale = 0.5
        W, H = int(1600 * scale), int(1200 * scale)
        canvas = np.zeros((H, W, 3), dtype=np.uint8)

        def to_kv(x, y):
            return int(x * scale), int(y * scale)

        # --- LAYER 1: COMPENSATION VECTOR FIELD (Bottom Layer) ---
        if self.get_parameter("viz_show_field").value:
            grid_step = 100  # Pixels in 1600x1200 space
            for gy in range(0, 1200, grid_step):
                for gx in range(0, 1600, grid_step):
                    # Get the correction this node is CURRENTLY applying
                    dx, dy = self.get_correction(float(gx), float(gy))

                    p_start = to_kv(gx, gy)
                    # We subtract dx/dy because that's how the gaze is corrected
                    p_end = to_kv(gx + dx, gy + dy)

                    # Draw subtle grey arrows for the field
                    cv2.arrowedLine(
                        canvas, p_start, p_end, (40, 40, 40), 1, tipLength=0.3
                    )

        bin_size = 150  # Matches your Learner config
        grid_color = (30, 30, 30)
        for gx in range(0, 1600, bin_size):
            cv2.line(canvas, to_kv(gx, 0), to_kv(gx, 1200), grid_color, 1)
        for gy in range(0, 1200, bin_size):
            cv2.line(canvas, to_kv(0, gy), to_kv(1600, gy), grid_color, 1)

        # 2. DRAW ALL BUTTONS (BACKGROUND)
        if self.get_parameter("viz_show_all_buttons").value:
            for status in self.latest_all_buttons:
                # Skip the active one to draw it with highlight later
                if status.button.button_id == current_btn_msg.button.button_id:
                    continue

                # Colors from your reference: Hover=Yellowish, Inactive=Grey
                if status.button_status == ButtonStatus.BUTTON_HOVER:
                    color = (0, 180, 180)  # Dim Yellow
                else:
                    color = (100, 100, 100)  # Dark Grey

                if len(status.button.x_points) == 4:
                    pts = np.array(
                        [
                            [
                                to_kv(
                                    status.button.x_points[i], status.button.y_points[i]
                                )
                            ]
                            for i in range(4)
                        ],
                        np.int32,
                    )
                    cv2.polylines(canvas, [pts], True, color, 1)
                    center = to_kv(status.button.center_x, status.button.center_y)
                    cv2.putText(
                        canvas,
                        str(status.button.button_id),
                        (center[0] - 5, center[1] + 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.3,
                        color,
                        1,
                    )

        # 3. DRAW ACTIVE BUTTON (FOREGROUND)
        if self.get_parameter("viz_show_buttons").value:
            b = current_btn_msg.button

            # Check if we have valid corner data (4 points)
            if len(b.x_points) == 4 and len(b.y_points) == 4:
                # Determine color based on active status
                # Bright Green if active, Dark Red if inactive
                color = (
                    (0, 255, 0)
                    if current_btn_msg.button_status == ButtonStatus.BUTTON_ACTIVE
                    else (0, 0, 150)
                )

                # Create a list of points: [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
                # and scale them to the debug canvas size
                pts = []
                for i in range(4):
                    px, py = to_kv(b.x_points[i], b.y_points[i])
                    pts.append([px, py])

                # Convert to a numpy array of shape (4, 1, 2) and type int32 for OpenCV
                pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))

                # Draw the closed quadrilateral
                cv2.polylines(
                    canvas, [pts_arr], isClosed=True, color=color, thickness=2
                )

                # Draw the ID label at the button's center
                center = to_kv(b.center_x, b.center_y)
                cv2.putText(
                    canvas,
                    f"ID:{b.button_id}",
                    (center[0] - 20, center[1]),  # Offset slightly to center text
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    color,
                    1,
                )
                # and a circle
                cv2.circle(canvas, center, 5, color, -1)

        # 3. DRAW GAZE HISTORY (The 'Tail')
        if self.get_parameter("viz_show_history").value:
            hist_len = self.get_parameter("viz_history_limit").value
            # Get last N samples from circular buffer
            idx = (
                np.arange(self.gaze_ptr - hist_len, self.gaze_ptr)
                % self.gaze_buffer_size
            )
            history = self.gaze_history[idx]

            for i in range(len(history) - 1):
                p1 = to_kv(history[i, 1], history[i, 2])
                p2 = to_kv(history[i + 1, 1], history[i + 1, 2])
                if history[i, 0] > 0:  # Check if timestamp is valid
                    alpha = i / len(history)  # Fade effect
                    cv2.line(canvas, p1, p2, (255, 100, 0), 1)

        # 4. DRAW RAW AND CORRECTED GAZE
        # Use latest smoothed values calculated in gaze_cb
        raw_x, raw_y = self.smoothed_x, self.smoothed_y

        # Calculate correction for the current formula
        dx, dy = self.get_correction(raw_x, raw_y)
        corr_x, corr_y = raw_x + dx, raw_y + dy

        p_raw = to_kv(raw_x, raw_y)
        p_corr = to_kv(corr_x, corr_y)

        if (
            self.get_parameter("viz_show_vectors").value
            and current_btn_msg._button_status == ButtonStatus.BUTTON_ACTIVE
        ):

            b = current_btn_msg.button
            btn_center = to_kv(b.center_x, b.center_y)

            # 1. Calculate the Error Vector (from RAW Sensor to Target)
            error_x = b.center_x - raw_x
            error_y = b.center_y - raw_y

            # 2. Calculate Angle (matches Reservoir: atan2(y, x))
            angle = np.arctan2(error_y, error_x)
            hue = int(((angle + np.pi) / (2 * np.pi)) * 179)
            hsv_color = np.uint8([[[hue, 255, 255]]])
            bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
            vector_color = (int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2]))

            # 3. Draw the line and a small target circle with the synced color
            cv2.line(canvas, p_raw, btn_center, vector_color, 2)
            cv2.circle(canvas, btn_center, 4, vector_color, -1)

            # 4. Draw Dot at Target center with the same color
            cv2.circle(canvas, btn_center, 5, vector_color, -1)

            # 5. Label with the distance from CORRECTED gaze to Target
            # Calculate distance for the label
            dist = np.sqrt(error_x**2 + error_y**2)
            cv2.putText(
                canvas,
                f"Err: {dist:.1f}px",
                (p_raw[0] + 15, p_raw[1] - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                vector_color,  # Text matches the vector color
                1,
            )
        if self.get_parameter("viz_show_raw").value:
            cv2.drawMarker(canvas, p_raw, (0, 0, 255), cv2.MARKER_TILTED_CROSS, 15, 2)

        if self.get_parameter("viz_show_corrected").value:
            cv2.drawMarker(canvas, p_corr, (255, 255, 255), cv2.MARKER_CROSS, 20, 2)
            # Add a circle too in orange
            cv2.circle(canvas, p_corr, 4, (0, 165, 255), -1)

        if current_btn_msg._button_status == ButtonStatus.BUTTON_ACTIVE:
            # 1. Calculate Distances to Target
            dist_raw = np.sqrt((raw_x - b.center_x) ** 2 + (raw_y - b.center_y) ** 2)
            dist_corr = np.sqrt((corr_x - b.center_x) ** 2 + (corr_y - b.center_y) ** 2)

            # 2. Identify the "Winner" (Smaller Error)
            # Blue in BGR is (255, 0, 0)

            if dist_raw < dist_corr:
                # Sensor is performing better than the model
                cv2.circle(canvas, p_raw, 15, (0, 0, 255), 2)
            else:
                # Model is successfully improving the sensor data
                cv2.circle(canvas, p_corr, 15, (0, 255, 0), 2)

        # 4. OVERLAY INFO
        cv2.putText(
            canvas,
            f"Pipeline Delay: {self.get_parameter('internal_pipeline_delay_ms').value}ms",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )
        cv2.putText(
            canvas,
            f"Active Model: {self.model_type}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )

        # Publish to ROS
        try:
            img_msg = self.bridge.cv2_to_imgmsg(canvas, encoding="bgr8")
            img_msg.header.stamp = self.get_clock().now().to_msg()
            self.live_viz_pub.publish(img_msg)
        except Exception as e:
            self.get_logger().error(f"Live Viz Error: {e}")

    def plot_debug_viz(
        self, gaze_data, btn_data, start_ts, end_ts, highlight_timestamps
    ):
        """Creates a 1200x400 image. Handles coordinate conversion strictly for OpenCV."""
        W, H = 1200, 400
        img = np.zeros((H, W, 3), dtype=np.uint8)

        if len(gaze_data) < 2:
            return
        # FIX: used_indices is now a set of timestamps (floats)
        # We ensure it's a set for O(1) lookup speed
        if isinstance(highlight_timestamps, np.ndarray):
            # If it's the [ts, x, y] array, just take the ts column
            used_set = (
                set(highlight_timestamps[:, 0])
                if highlight_timestamps.ndim > 1
                else set(highlight_timestamps)
            )
        else:
            used_set = set(highlight_timestamps)

        # 1. Setup Scaling
        # Use actual data limits for scaling to prevent "empty" plots due to time gaps
        t_min = float(np.min(gaze_data[:, 0]))
        t_max = float(np.max(gaze_data[:, 0]))
        t_range = t_max - t_min if t_max > t_min else 1.0

        def to_pixels(t, val, is_y=False):
            try:
                # Calculate normalized position (0.0 to 1.0)
                norm_x = (float(t) - t_min) / t_range
                px_x = int(norm_x * (W - 60) + 30)
                # px_y = norm_y * (H - 40) + 20
                # Y-axis is Coordinate Value (normalized to 1600 width)
                # We use 1600 because this plot shows the X-profile
                norm_val = float(val) / 1600.0
                # Flip Y so 0 is at bottom, 1600 is at top of the strip
                px_y = int((H - 60) - (norm_val * (H - 60)) + 30)
                return (np.clip(px_x, 0, W - 1), np.clip(px_y, 0, H - 1))

            except (ValueError, TypeError):
                return None

        # 2. Draw Background (Button Activity State)
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

        # 3. Draw Gaze Samples
        for i, (t, gx, gy) in enumerate(gaze_data):
            p = to_pixels(t, gx)
            # Color logic:
            # Yellow/Cyan = The actual data sent to the learner
            # Dim Blue = Buffer history not included in the segment
            if i in used_set:
                use_alignment = self.get_parameter("use_temporal_alignment").value
                color = (0, 255, 255) if use_alignment else (0, 255, 0)
                radius = 2
            else:
                color = (80, 40, 20)
                radius = 1

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

        # 5. Draw Timing Markers (Trimming visualization)
        ps = to_pixels(start_ts, 0)
        pe = to_pixels(end_ts, 0)
        # Start marker (Yellow)
        cv2.line(img, (ps[0], 0), (ps[0], H), (0, 255, 255), 1)
        # End marker (Cyan)
        cv2.line(img, (pe[0], 0), (pe[0], H), (255, 255, 0), 1)

        # 6. UI Overlays
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(
            img,
            "X-Coordinate Temporal Profile",
            (10, 25),
            font,
            0.6,
            (255, 255, 255),
            1,
        )

        duration = end_ts - start_ts
        cv2.putText(
            img,
            f"Segment: {duration:.2f}s | Samples: {len(used_set)}",
            (10, H - 15),
            font,
            0.5,
            (200, 200, 200),
            1,
        )

        # Legend
        cv2.putText(
            img, "TRUTH (BUTTON X)", (W - 180, 25), font, 0.4, (200, 200, 200), 1
        )
        cv2.putText(img, "USED GAZE", (W - 180, 45), font, 0.4, (0, 255, 255), 1)

        # Publish
        try:
            msg = self.bridge.cv2_to_imgmsg(img, encoding="bgr8")
            msg.header.stamp = self.get_clock().now().to_msg()
            self.debug_pub_viz.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Viz Error: {e}")

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
        # Todo:
        # self.get_logger().debug(
        #     f"Gaze to camera pipeline latency: {lat:.1f}ms | RMS: {rms:.1f}ms",
        #     throttle_duration_sec=10.0,
        # )

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
