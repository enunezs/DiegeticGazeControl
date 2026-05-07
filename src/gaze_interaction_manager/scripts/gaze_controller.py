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

# For plotting
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io


class GazeController(Node):

### === 1. Initialization & Parameters === ###

    def __init__(self):
        super().__init__("gaze_controller")
        self._lock = Lock()
        self.bridge = CvBridge()

        self.get_logger().info("Gaze Controller Node Initialized")

        # --- 1. Parameters ---
        # Filtering
        self.declare_parameter("history_length_s", 30.0)
        self.declare_parameter("internal_pipeline_delay_ms", 0.0)
        self.declare_parameter("median_window", 20)
        self.declare_parameter("ema_alpha", 0.2)
        self.declare_parameter("edge_margin", 50)

        # Timing properties
        self.declare_parameter(
            "start_trim_ms", 100.0
        )  # Padding for trimming the START of event
        self.declare_parameter(
            "terminal_trim_ms", 100.0
        )  # Padding for trimming the END of event
        self.declare_parameter("min_event_duration_ms", 200.0)

        self.declare_parameter("compensation_active", True)
        self.declare_parameter("max_compensation_px", 200.0)
        self.declare_parameter("use_temporal_alignment", True)
        self.declare_parameter("sticky_button_interaction", False)

        # --- Synchronization Parameters ---
        self.declare_parameter("max_gap_ms", 300.0)
        self.declare_parameter("max_error_px", 200.0)

        # --- Visualization Parameters ---
        self.declare_parameter("viz_enabled", False)
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

        self.get_logger().info(f"Compensation Active: {self.get_parameter('compensation_active').value}") 

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

        self.start_trim_ms = int(
            (self.get_parameter("start_trim_ms").value / 1000.0) * self.hz_gaze
        )
        self.min_samples = int(
            (self.get_parameter("min_event_duration_ms").value / 1000.0) * self.hz_gaze
        )


        self.max_gap_s = self.get_parameter("max_gap_ms").value / 1000.0
        self.max_error_px = self.get_parameter("max_error_px").value

        self._resize_gaze_buffer(self.get_parameter("history_length_s").value)

    def _resize_gaze_buffer(self, length_s):
        new_size = int(length_s * self.hz_gaze)
        if getattr(self, 'gaze_history', None) is None or new_size != len(self.gaze_history):
            self.get_logger().info(f"Initializing Gaze Buffer: {new_size} samples")
            self.gaze_buffer_size = new_size
            self.gaze_history = np.zeros((self.gaze_buffer_size, 3))
            self.gaze_ptr = 0
            self.gaze_buffer_filled = False

    def param_callback(self, params):
        """
        Dynamically handles parameter updates. 
        MUST extract from `params` directly because self.get_parameter() 
        still holds old values during this callback.
        """
        for p in params:
            if p.name == "median_window":
                self.median_window = p.value
            elif p.name == "ema_alpha":
                self.ema_alpha = p.value
            elif p.name == "edge_margin":
                self.edge_margin = p.value
            elif p.name == "max_compensation_px":
                self.max_compensation = p.value
            elif p.name == "start_trim_ms":
                self.start_trim_ms = int((p.value / 1000.0) * self.hz_gaze)
            elif p.name == "min_event_duration_ms":
                self.min_samples = int((p.value / 1000.0) * self.hz_gaze)
            elif p.name == "history_length_s":
                self._resize_gaze_buffer(p.value)
            elif p.name == "max_gap_ms":
                self.max_gap_s = p.value / 1000.0
            elif p.name == "max_error_px":
                self.max_error_px = p.value

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
                    # self.get_logger().info(
                    #     f"Gaze out of bounds at {ts:.3f}. Ending segment."
                    # )

            # Debug signals
            # self.publish_debug_signals(in_fov, is_clean)

    def _process_and_publish_corrected_gaze(self, msg):

        # --- A. SMOOTHING (Median + EMA) ---
        if self.gaze_buffer_filled or self.gaze_ptr >= self.median_window:
            # We need a min number of samples for smoothing
            idx = (
                np.arange(self.gaze_ptr - self.median_window, self.gaze_ptr)
                % self.gaze_buffer_size
            )
            # TODO: Would prefer as a function
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
            # Just pass without smoothing
            self.smoothed_x, self.smoothed_y = msg.x, msg.y

        # --- B. CORRECTION ---
        if self.get_parameter("compensation_active").value:
            dx, dy = self.get_correction(self.smoothed_x, self.smoothed_y)
            dx = np.clip(dx, -self.max_compensation, self.max_compensation)
            dy = np.clip(dy, -self.max_compensation, self.max_compensation)
        else:
            dx, dy = 0.0, 0.0

        # --- C. PUBLISH ---
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
                # event_start_ts = msg.start_time_ns / 1e9
                event_start_ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
                # self.get_logger().info(
                #     f"Saccade detected! Terminating segment at {event_start_ts:.3f}"
                # )
                self._trigger_segment_end(event_start_ts, reason="SACCADE")

    def blink_cb(self, msg: GazeEvent):
        with self._lock:
            if self.is_recording:
                # event_start_ts = msg.start_time_ns / 1e9
                event_start_ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)

                # self.get_logger().info(
                #     f"Blink detected! Terminating segment at {event_start_ts:.3f}"
                # )
                self._trigger_segment_end(event_start_ts, reason="BLINK")

    ### === 2. Core Callbacks: Buttons === ###
    def button_cb(self, msg: ButtonStatus):
        """
        Triggered at ~30Hz by the active button topic.

        Responsibilities (in order):
          1. Latency logging              — always, unconditional
          2. Timestamp adjustment         — always, unconditional
          3. Ground truth append          — always for ACTIVE+valid, unconditional
          4. State machine                — delegated to _handle_button_standard()
                                           or _handle_button_sticky()
          5. Visualization trigger        — always, at the end

        The ground truth append (step 3) is intentionally separated from the
        state machine (step 4).  Previously they were interleaved, which caused
        btn_history to be empty on the first button_cb call (before is_recording
        was set), breaking interpolation.
        """
        with self._lock:

            # ----------------------------------------------------------------
            # 1. Latency logging (diagnostic only, does not affect data flow)
            # ----------------------------------------------------------------
            button_ts = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
            if self.latest_gaze_time > 0 and button_ts > 0:
                latency_ms = (self.latest_gaze_time - button_ts) * 1000.0
                self.update_latency_metrics(latency_ms)

            # ----------------------------------------------------------------
            # 2. Pipeline delay adjustment
            #    adjusted_ts is what we use for EVERYTHING downstream.
            #    button_ts is only kept for latency logging above.
            # ----------------------------------------------------------------
            adjusted_ts = button_ts - (
                self.get_parameter("internal_pipeline_delay_ms").value / 1000.0
            )

            incoming_id = msg.button.button_id
            is_active = msg.button_status == ButtonStatus.BUTTON_ACTIVE
            is_pos_valid = (
                abs(msg.button.center_x) > 1e-5
                and abs(msg.button.center_y) > 1e-5
            )

            # ----------------------------------------------------------------
            # 3. Ground truth history append — UNCONDITIONAL
            #    Every valid ACTIVE position gets logged regardless of recording
            #    state.  _publish_segment() reads btn_history for interpolation,
            #    so this must be populated before is_recording is ever set.
            # ----------------------------------------------------------------
            if is_active and is_pos_valid:
                self.btn_history.append((
                    adjusted_ts,
                    msg.button.center_x,
                    msg.button.center_y,
                    incoming_id,
                    is_active,
                ))
                self.last_valid_btn_ts = adjusted_ts
                self.latest_raw_button_msg = msg  # Keep geometry fresh for teleop

            # ----------------------------------------------------------------
            # 4. State machine — delegated based on mode
            # ----------------------------------------------------------------
            if self.get_parameter("sticky_button_interaction").value:
                self._handle_button_sticky(msg, adjusted_ts, incoming_id, is_active)
            else:
                self._handle_button_standard(msg, adjusted_ts, incoming_id, is_active)

            # ----------------------------------------------------------------
            # 5. Visualization
            # ----------------------------------------------------------------
            if self.get_parameter("viz_enabled").value:
                self.publish_live_debug_plot(msg)

    # -------------------------------------------------------------------------

    def _handle_button_standard(self, msg, adjusted_ts, incoming_id, is_active):
        """
        Simple non-sticky state machine.

        Rising edge  → start recording, lock onto this button ID.
        Falling edge → if we were recording, end the segment immediately.
        Different ID while recording → switch lock (non-sticky allows this).

        This is the baseline.  All tests should pass against this path.
        """
        # Rising edge: a new ACTIVE signal while we are not yet recording
        if is_active and not self.is_recording:
            self.is_recording = True
            # self.button_engaged = True
            self.current_button_id = incoming_id
            self.rec_start_ts = adjusted_ts
            self.get_logger().debug(f"[Standard] Recording started: {incoming_id}")
            return

        # While recording: allow lock switch to a different button
        if self.is_recording and is_active and incoming_id != self.current_button_id:
            self.get_logger().warning(
                f"[Standard] Switching lock: {self.current_button_id} → {incoming_id}"
            )
            self.current_button_id = incoming_id

        # Falling edge: button released while we were recording
        if not is_active :
            # and self.button_engaged and incoming_id == self.current_button_id
            # self.button_engaged = False
            if self.is_recording:
                terminal_trim_s = self.get_parameter("terminal_trim_ms").value / 1000.0
                end_point = self.last_valid_btn_ts - terminal_trim_s
                self._trigger_segment_end(end_point, reason="BUTTON_RELEASE")
                self.get_logger().debug(
                    f"[Standard] Button released. Segment ended at {end_point:.3f}"
                )

    # -------------------------------------------------------------------------

    def _handle_button_sticky(self, msg, adjusted_ts, incoming_id, is_active):
        """
        Sticky state machine.

        The key assumption: if the user started an interaction with button A,
        we assume they are STILL interacting with A even if:
          - the sensor drifts and reports a different active button
          - the sensor briefly loses the button entirely
          - the button goes INACTIVE (release is ignored)

        Only a physiological signal (saccade, blink) ends the segment.
        Those are handled in saccade_cb / blink_cb → _trigger_segment_end.

        Ground truth collection:
          - While no interaction is active: log ALL arriving button positions
            normally (already done in step 3 of button_cb above).
          - Once locked: only log positions for current_button_id.
            Positions for other buttons are ignored for interpolation.
            If current_button_id disappears from the active topic, we leave
            a gap in btn_history (honest — no extrapolation).
            A future enhancement could query latest_all_buttons here to fill
            gaps, but that is left as a TODO to keep this path simple.

        Rising edge  → start recording, lock onto this button ID.
        Falling edge → ignored (button_engaged flag updated for bookkeeping
                       only; no segment is triggered).
        Different ID → if not recording, start fresh on the new ID.
                       If already recording, ignore (stay locked on original).
        """
        if is_active and not self.is_recording:
            # Fresh start: lock onto whatever just became active
            self.is_recording = True
            self.button_engaged = True
            self.current_button_id = incoming_id
            self.rec_start_ts = adjusted_ts
            self.get_logger().info(f"[Sticky] Recording started: {incoming_id}")
            return

        if self.is_recording:
            if incoming_id != self.current_button_id:
                # Sensor drift / glitch — do NOT switch lock, do NOT log this
                # button's position into btn_history for interpolation.
                # (The append in step 3 already happened for the raw history,
                # but the interpolation in _publish_segment only uses samples
                # where the ID matches current_button_id — see note below.)
                #
                # TODO: query self.latest_all_buttons to find current_button_id
                # and log its position here if available, to reduce gaps.
                self.get_logger().debug(
                    f"[Sticky] Ignoring {incoming_id}, locked on {self.current_button_id}"
                )
                return

            # Falling edge for the *locked* button: update bookkeeping only
            if not is_active and self.button_engaged:
                self.button_engaged = False
                self.get_logger().info(
                    f"[Sticky] Physical contact lost with {self.current_button_id}. "
                    "Maintaining lock — waiting for physiological signal."
                )
                # No _trigger_segment_end here — intentional.

    def all_buttons_cb(self, msg: ButtonStatusArray):
        """Simple storage of latest button states for background drawing."""
        if not self.get_parameter("viz_enabled").value:
            return
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
            self.get_logger().info(
                f"Attempted to end segment for reason {reason} at {end_ts:.3f}, but no recording was active."
            )
            return

        # self.get_logger().info(f"Processing segment: {reason} at {end_ts:.3f}")


        # 1. Slice and Sort Gaze
        # There is an issue with the raw_idx
        # Lets see first the data: (ts, x, y)
        # self.get_logger().info(f"Raw index info: Min ts {np.min(self.gaze_history[:, 0])}, Max ts {np.max(self.gaze_history[:, 0])}")
        # self.get_logger().info(f"Gaze data at ptr {self.gaze_ptr-1}: {self.gaze_history[self.gaze_ptr-1]}")
        # self.get_logger().info(f"Gaze is full? {self.gaze_buffer_filled}")
        
        gaze_data = (
            np.roll(self.gaze_history, -self.gaze_ptr, axis=0)
            if self.gaze_buffer_filled
            else self.gaze_history[: self.gaze_ptr]
        )
        # Is it in order?
        # self.get_logger().info(f"Gaze data is in order: {np.all(gaze_data[:-1, 0] <= gaze_data[1:, 0])}")

        # Prevent out of order timestamps
        # gaze_data = gaze_data[gaze_data[:, 0] > 0]
        # gaze_data = gaze_data[np.argsort(gaze_data[:, 0])]



        # 2. Windowing
        # This is always zero...
        raw_idx = np.where((gaze_data[:, 0] >= self.rec_start_ts) & (gaze_data[:, 0] <= end_ts))[0]

        # Check minimum duration
        segment_duration_ms = (raw_idx[-1] - raw_idx[0]) if len(raw_idx) > 0 else 0


        if len(raw_idx) == 0 or segment_duration_ms < (self.start_trim_ms + self.min_samples):
            # Segment discarded
            self.get_logger().info(
                f"Segment too short ({segment_duration_ms} ms, {len(raw_idx)} samples). Discarding. Reason = {reason}"
            )
            
        else:
            # Post-hoc trimming: Remove the start padding (eye settling)
            trimmed_idx = raw_idx[self.start_trim_ms :]

            trimmed_start_ts = gaze_data[trimmed_idx[0], 0]

            self._publish_segment(
                gaze_data[trimmed_idx], 
                end_ts,
                start_ts=self.rec_start_ts,
                trimmed_start_ts=trimmed_start_ts
                )
            self.get_logger().info(
                f"Segment finalized: {reason} with {len(trimmed_idx)} samples, {(end_ts - trimmed_start_ts)*1000:.3f} ms)"
            )
            # else:
            #     self.get_logger().error(
            #         f"All samples trimmed out after applying start_trim_ms. Discarding segment."
            #     )

        self.is_recording = False
        self.rec_start_ts = None
        self.button_engaged = False
        self.current_button_id = None

    def reset_recording_state(self):
        self.is_recording = False
        self.rec_start_ts = None
        self.button_engaged = False
        self.last_valid_btn_ts = 0.0

    def float_to_stamp(self, t_float):
        t = Header().stamp
        t.sec, t.nanosec = int(t_float), int((t_float - int(t_float)) * 1e9)
        return t

    def _publish_segment(self, gaze_slice, end_ts, start_ts, trimmed_start_ts):
        """Interpolates and sends the ROS message"""

        use_alignment = self.get_parameter("use_temporal_alignment").value
        sticky = self.get_parameter("sticky_button_interaction").value

        btn_data = list(self.btn_history)
        if not btn_data:
            return

        if sticky and self.current_button_id is not None:
            btn_data = [b for b in btn_data if b[3] == self.current_button_id]
 
        # We need at least 2 points to interpolate a timeline
        if len(btn_data) < 2:
            self.get_logger().warning("Not enough button history to interpolate. Discarding segment.")
            return
        
        # 1. Extract Button (Target) Arrays
        B_times = np.array([b[0] for b in btn_data])
        B_xs = np.array([b[1] for b in btn_data])
        B_ys = np.array([b[2] for b in btn_data])

        # 2. Extract Gaze Arrays
        G_times = gaze_slice[:, 0]
        G_xs = gaze_slice[:, 1]
        G_ys = gaze_slice[:, 2]

        # 3. Vectorized Interpolation
        if use_alignment:
            tx = np.interp(G_times, B_times, B_xs)
            ty = np.interp(G_times, B_times, B_ys)
        else:
            # Without alignment: find closest raw target preceding the gaze sample
            idxs = np.searchsorted(B_times, G_times) - 1
            idxs = np.clip(idxs, 0, len(B_times) - 1)
            tx = B_xs[idxs]
            ty = B_ys[idxs]


        # 4. Create Mask: Drop Gaps 
        # (Drop samples that fall in a gap > max_gap_s, or out of bounds)
        gap_mask = np.ones(len(G_times), dtype=bool)

        # A. Out of bounds (Extrapolation is dropped)
        gap_mask[G_times < B_times[0]] = False
        gap_mask[G_times > B_times[-1]] = False

        # B. Internal Gaps
        diffs = np.diff(B_times)
        bad_gap_indices = np.where(diffs > self.max_gap_s)[0]

        # np.searchsorted maps G_times to the interval they fall into
        interval_idx = np.searchsorted(B_times, G_times)
        for i in bad_gap_indices:
            # Drop gaze samples falling into the interval (B_times[i], B_times[i+1])
            gap_mask[interval_idx == i + 1] = False

        # 5. Create Mask: Drop Huge Errors
        errors = np.hypot(tx - G_xs, ty - G_ys)
        error_mask = errors <= self.max_error_px

        # 6. Final Valid Mask
        valid_mask = gap_mask & error_mask

        # 7. Build ROS Message (Iterate only over valid data)
        valid_indices = np.where(valid_mask)[0]

        if len(valid_indices) == 0:
            self.get_logger().warning("All gaze samples dropped (gaps or errors). Discarding segment.")
        else:
            segment = InteractionSegment()
            segment.header.stamp = self.get_clock().now().to_msg()
            segment.button_id = self.current_button_id

            for i in valid_indices:
                t_pt = Point(x=float(tx[i]), y=float(ty[i]), z=0.0)
                segment.target_samples.append(t_pt)

                g_msg = GazeData()
                g_msg.header.stamp = self.float_to_stamp(G_times[i])
                g_msg.x, g_msg.y = float(G_xs[i]), float(G_ys[i])
                segment.gaze_samples.append(g_msg)

            self.segment_pub.publish(segment)

        # 8. Trigger Matplotlib Visualization
        if self.get_parameter("viz_enabled").value:
            self.plot_ts_alignment_viz(
                G_times, G_xs, G_ys, 
                B_times, B_xs, B_ys, 
                tx, ty, 
                gap_mask, error_mask, valid_mask, 
                start_ts, trimmed_start_ts, end_ts
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

        # 4. Pure Radial Term [8: k_radial, 9: cross_radial]
        if len(cx) >= 9 or len(cy) >= 9:
            r = np.sqrt(dx**2 + dy**2)
            
            if len(cx) >= 9:
                corr_x += cx[8] * (dx * r)
            if len(cy) >= 9:
                corr_y += cy[8] * (dy * r)
                
            # NEW: Support cross-axis radial terms
            if len(cx) >= 10:
                corr_x += cx[9] * (dy * r)  
            if len(cy) >= 10:
                corr_y += cy[9] * (dx * r)  

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

    def plot_ts_alignment_viz(self, 
                              g_times, g_xs, g_ys, 
                              b_times, b_xs, b_ys, 
                              tx, ty, 
                              gap_mask, error_mask, valid_mask, 
                              start_ts, trimmed_start_ts, end_ts):
        """Generates a detailed Matplotlib figure of the synchronization and publishes it."""
        
        # Create figure with 2 vertically stacked subplots sharing the X (time) axis
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        fig.suptitle(f"Segment Synchronization Analysis (ID: {self.current_button_id})", fontsize=14)

        # -------------------------------------------------------------
        # Helper to plot a single axis (X or Y)
        # -------------------------------------------------------------
        def plot_lane(ax, b_vals, g_vals, t_vals, title, y_limit):
            ax.set_title(title, loc='left', fontsize=10, weight='bold')
            ax.set_ylim(0, y_limit)
            ax.set_xlim(end_ts - 5.0, end_ts + 0.2)
            ax.invert_yaxis() # Image coordinates: 0 at top
            ax.grid(True, linestyle='--', alpha=0.5)

            # 1. Background Shading
            # A. Start Trim Zone
            ax.axvspan(start_ts, trimmed_start_ts, color='yellow', alpha=0.2, label='Start Trim Padding')
            
            # B. Gap Zones (Highlight gaps > max_gap_s)
            diffs = np.diff(b_times)
            for i, d in enumerate(diffs):
                if d > self.max_gap_s:
                    label = f'Gap > {self.max_gap_s*1000:.0f}ms' if i == 0 else ""
                    ax.axvspan(b_times[i], b_times[i+1], color='red', alpha=0.15, hatch='//', label=label)

            # 2. Plot Button Target (Ground Truth)
            ax.plot(b_times, b_vals, color='gray', linestyle='--', alpha=0.6)
            ax.scatter(b_times, b_vals, marker='s', color='black', s=10, zorder=3, label='Target Samples')

            # 3. Plot Gaze Points
            # A. Continuous Gaze Trajectory (Always visible)
            ax.scatter(g_times, g_vals, 
                       color='blue', s=2, zorder=4, label='Gaze Trajectory')
            # ax.plot(g_times, g_vals, color='blue', alpha=0.2, linewidth=1, zorder=1)

            # B. Valid Gaze (Green)
            ax.scatter(g_times[valid_mask], g_vals[valid_mask], 
                       color='green', s=2, zorder=4, label='Valid Gaze')
            
            # C. Dropped due to Gap/Out-of-bounds (Red)
            ax.scatter(g_times[~gap_mask], g_vals[~gap_mask], 
                       color='red', s=2, zorder=4, label='Dropped (Gap/Extrap)')

            # D. Dropped due to Error Threshold (Orange Crosses)
            error_dropped = gap_mask & (~error_mask)
            ax.scatter(g_times[error_dropped], g_vals[error_dropped], 
                       facecolors='none', edgecolors='orange', marker='X', s=15, zorder=4, label='Dropped (Error > Thr)')

            # 4. Faint lines connecting dropped Gaze to Interpolated Target (shows *why* it exceeded error)
            for i in np.where(error_dropped)[0]:
                ax.plot([g_times[i], g_times[i]], [g_vals[i], t_vals[i]], color='orange', linestyle=':', alpha=0.7)

            # End line marker
            ax.axvline(end_ts, color='cyan', linestyle='-', label='Segment End')

        # -------------------------------------------------------------
        
        # Draw X Lane
        plot_lane(ax1, b_xs, g_xs, tx, "X-Coordinate Profile (Width: 1600)", 1600)
        # Draw Y Lane
        plot_lane(ax2, b_ys, g_ys, ty, "Y-Coordinate Profile (Height: 1200)", 1200)

        # Polish layout
        ax2.set_xlabel("Timestamp (Seconds)", fontsize=10, weight='bold')
        ax1.legend(loc='upper right', bbox_to_anchor=(1.15, 1.05), fontsize=8)
        fig.tight_layout()

        # Render Figure to Image Buffer
        fig.canvas.draw()
        
        # Extract RGB buffer and convert to BGR for CV Bridge
        img_np = np.asarray(fig.canvas.buffer_rgba())
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        
        plt.close(fig) # Prevent memory leaks!

        # Publish to ROS
        try:
            msg = self.bridge.cv2_to_imgmsg(img_bgr, encoding="bgr8")
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
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
