#!/usr/bin/env python3

"""
Gaze Interaction Node

This node processes gaze data and 2D button positions to determine button activation
through dwell time or other interaction methods.

Usage:
    ros2 run gaze_interaction gaze_interaction_node --ros-args --params-file config/params.yaml
"""

# from build.diegetic_transform_engine.rosidl_generator_py import diegetic_transform_engine
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
import numpy as np
import cv2
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from threading import Lock

# ROS2 Messages
from geometry_msgs.msg import PointStamped, Point
from std_msgs.msg import String, Header
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

# Custom Messages (adjust import paths as needed)
from diegetic_transform_engine.msg import DiegeticButton2DArray, DiegeticButton2D
from gaze_interaction_manager.msg import ButtonStatus as ButtonStatus_msg
from gaze_interaction_manager.msg import ButtonStatusArray as ButtonStatusArray_msg

# For gamepad/keyboard input (optional)
try:
    from sensor_msgs.msg import Joy
    from pynput import keyboard

    HAS_INPUT_SUPPORT = True
except ImportError:
    HAS_INPUT_SUPPORT = False


class InteractionMode(Enum):
    """Available interaction modes for button activation"""

    DWELL_TIME = "dwell_time"
    KEYBOARD_TRIGGER = "keyboard_trigger"
    GAMEPAD_TRIGGER = "gamepad_trigger"
    IMMEDIATE = "immediate"  # Activate immediately on hover


class ButtonState(Enum):
    """Button activation states"""

    INACTIVE = "inactive"
    HOVERED = "hovered"
    ACTIVE = "active"


@dataclass
class ButtonStatus:
    """Represents the current status of a button"""

    button_id: str
    state: ButtonState = ButtonState.INACTIVE
    activation_level: float = 0.0  # 0.0 to 1.0
    last_seen_stamp: rclpy.time.Time = None
    # Button center position
    center_x: float = 0.0
    center_y: float = 0.0
    # Store all 4 corner coordinates as arrays
    x_points: List[float] = None  # Array of 4 x coordinates
    y_points: List[float] = None  # Array of 4 y coordinates

    def __post_init__(self):
        if self.x_points is None:
            self.x_points = [0.0, 0.0, 0.0, 0.0]
        if self.y_points is None:
            self.y_points = [0.0, 0.0, 0.0, 0.0]


class GazeInteractionNode(Node):
    """
    ROS2 node that processes gaze data and 2D button positions for interaction.

    Subscribes to:
    - /diegetic_buttons_2d (DiegeticButton2DArray): 2D button positions and dimensions
    - /pupil_glasses/gaze_position (PointStamped): 2D gaze coordinates in screen space
    - /joy (Joy): Gamepad input (optional, if gamepad mode enabled)

    Publishes:
    - /gaze_interaction/input_status (ButtonStatusArray_msg): Status of all tracked buttons
    - /gaze_interaction/active_buttons (ButtonStatusArray_msg): Currently active buttons (same message type)
    - /gaze_interaction/debug_image (Image): Debug visualization (optional)
    - /haptic_feedback_input_string (String): Haptic feedback triggers
    """

    def __init__(self):
        super().__init__("dwell_time_node")

        # Thread safety
        self._button_lock = Lock()
        self._declare_parameters()

        # State tracking
        self.button_statuses: Dict[str, ButtonStatus] = {}

        # Track the timestamp of the last gaze msg used for dt
        self.last_gaze_stamp: Optional[rclpy.time.Time] = None
        self.current_gaze_pos = Point(x=0.5, y=0.5)  # Normalized coordinates (0-1)
        # self.last_update_time = 0.0

        self._setup_input_handling()
        self._setup_subscribers()
        self._setup_publishers()

        # Setup processing timer based on mode
        if self.processing_mode == "fixed_rate":
            # Create timer for fixed-rate processing
            self.processing_timer = self.create_timer(
                1.0 / self.processing_frequency, self._process_interaction
            )
        if self.processing_mode == "gaze_driven":
            # For gaze_driven mode, processing happens in gaze callback
            pass

        self.get_logger().info(
            f"Gaze Interaction Node initialized with mode: {self.interaction_mode.value}"
        )

    def _declare_parameters(self):
        """Declare and retrieve ROS parameters"""
        # Interaction mode
        self.declare_parameter("interaction_mode", "dwell_time")
        mode_str = self.get_parameter("interaction_mode").value
        try:
            self.interaction_mode = InteractionMode(mode_str)
        except ValueError:
            self.get_logger().warning(
                f"Unknown interaction mode {mode_str}, using DWELL_TIME"
            )
            self.interaction_mode = InteractionMode.DWELL_TIME

        # Timing parameters
        self.declare_parameter("dwell_duration_seconds", 1.0)
        self.dwell_duration = self.get_parameter("dwell_duration_seconds").value

        self.declare_parameter("activation_threshold", 0.7)
        self.activation_threshold = self.get_parameter("activation_threshold").value

        self.declare_parameter("hover_threshold", 0.2)
        self.hover_threshold = self.get_parameter("hover_threshold").value

        self.declare_parameter("deactivation_threshold", 0.1)
        self.deactivation_threshold = self.get_parameter("deactivation_threshold").value

        # Processing timing mode
        self.declare_parameter(
            "processing_mode", "fixed_rate"
        )  # 'fixed_rate' or 'gaze_driven'
        self.processing_mode = self.get_parameter("processing_mode").value

        # Processing frequency (for fixed rate mode)
        self.declare_parameter("processing_frequency", 30.0)
        self.processing_frequency = self.get_parameter("processing_frequency").value

        # Button cleanup parameters
        self.declare_parameter("button_timeout_seconds", 0.5)
        self.button_timeout = self.get_parameter("button_timeout_seconds").value

        # Debug parameters
        self.declare_parameter("publish_debug_image", False)
        self.publish_debug_image = self.get_parameter("publish_debug_image").value

        self.declare_parameter("verbose_logging", False)
        self.verbose_logging = self.get_parameter("verbose_logging").value

        # Screen resolution (for debug visualization)
        self.declare_parameter("screen_width", 1600)
        self.declare_parameter("screen_height", 1200)
        self.screen_width = self.get_parameter("screen_width").value
        self.screen_height = self.get_parameter("screen_height").value

        # Log key parameters
        self.get_logger().info(f"Processing mode: {self.processing_mode}")
        self.get_logger().info(f"Dwell duration: {self.dwell_duration}s")
        self.get_logger().info(f"Activation threshold: {self.activation_threshold}")
        if self.processing_mode == "fixed_rate":
            self.get_logger().info(
                f"Processing frequency: {self.processing_frequency} Hz"
            )

        # TODO: Cleanup and test unused parameters
        # Input handling
        self.external_trigger_active = False

        # OpenCV bridge for debug visualization
        if self.publish_debug_image:
            self.cv_bridge = CvBridge()
            self.debug_frame = np.zeros((720, 1280, 3), dtype=np.uint8)  # Default size

    def _setup_input_handling(self):
        """Setup external input handling (keyboard/gamepad) if needed"""
        if not HAS_INPUT_SUPPORT:
            if self.interaction_mode in [
                InteractionMode.KEYBOARD_TRIGGER,
                InteractionMode.GAMEPAD_TRIGGER,
            ]:
                self.get_logger().error(
                    "Input support not available but required for selected mode"
                )
                return

        if self.interaction_mode == InteractionMode.KEYBOARD_TRIGGER:
            self._setup_keyboard_listener()
        # Gamepad is handled via ROS subscription

    def _setup_keyboard_listener(self):
        """Setup keyboard listener for keyboard trigger mode"""
        if not HAS_INPUT_SUPPORT:
            return

        def on_press(key):
            self.external_trigger_active = True

        def on_release(key):
            self.external_trigger_active = False

        try:
            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
            self.get_logger().info("Keyboard listener initialized")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize keyboard listener: {e}")

    def _setup_subscribers(self):
        """Setup ROS subscribers"""
        # Gaze position (high frequency)
        self.gaze_subscriber = self.create_subscription(
            PointStamped, "/gaze_controller/corrected_gaze", self._gaze_callback, 10
        )

        # 2D Buttons (lower frequency, buffered)
        self.buttons_subscriber = self.create_subscription(
            DiegeticButton2DArray, "/diegetic_buttons_2d", self._buttons_callback, 10
        )

        # Gamepad input (if needed)
        if self.interaction_mode == InteractionMode.GAMEPAD_TRIGGER:
            self.joy_subscriber = self.create_subscription(
                Joy, "/joy", self._joy_callback, 10
            )

    def _setup_publishers(self):
        """Setup ROS publishers"""
        # Button status array
        self.status_publisher = self.create_publisher(
            ButtonStatusArray_msg, "/dwell_time/input_status", 10
        )

        # Active button info (using same message type)
        self.active_button_publisher = self.create_publisher(
            ButtonStatus_msg, "/dwell_time/active_button", 10
        )

        # Haptic feedback
        self.haptic_publisher = self.create_publisher(
            String, "/haptic_feedback_input_string", 10
        )

        # Debug image (optional)
        if self.publish_debug_image:
            self.debug_image_publisher = self.create_publisher(
                Image, "/dwell_time/debug_image", 10
            )

    def _buttons_callback(self, msg: DiegeticButton2DArray):
        # The main video callback
        """Buffer 2D button positions and update tracking"""
        button_msg_time = rclpy.time.Time.from_msg(msg.header.stamp)

        with self._button_lock:
            # Update existing buttons and add new ones
            received_button_ids = set()

            for button_2d in msg.buttons:
                button_id = button_2d.button_id
                received_button_ids.add(button_id)

                if button_id in self.button_statuses:
                    # Update existing button with new corner points format
                    status = self.button_statuses[button_id]
                    status.last_seen_stamp = button_msg_time

                    # Should not change unless we move to screen approach
                    status.center_x = button_2d.center_x
                    status.center_y = button_2d.center_y
                    status.x_points = list(button_2d.x_points)
                    status.y_points = list(button_2d.y_points)
                else:
                    # Create new button status
                    self.button_statuses[button_id] = ButtonStatus(
                        button_id=button_id,
                        last_seen_stamp=button_msg_time,
                        center_x=button_2d.center_x,
                        center_y=button_2d.center_y,
                        x_points=list(button_2d.x_points),
                        y_points=list(button_2d.y_points),
                    )

                    self.get_logger().debug(f"Tracking new button: {button_id}")

            # TODO: Remove?
            # Mark buttons not in current message (for potential cleanup)
            for button_id in list(self.button_statuses.keys()):
                if button_id not in received_button_ids:
                    # Button not seen in this update, but keep it for now
                    # Cleanup happens in _cleanup_old_buttons()
                    pass

    def _gaze_callback(self, msg: PointStamped):
        ### --- High-frequency gaze position updates --- ###
        gaze_ts = rclpy.time.Time.from_msg(msg.header.stamp)

        # Calculate dt based on gaze sensor clock, not CPU clock
        if self.last_gaze_stamp is None:
            dt = 0.005  # Default for 200Hz
        else:
            dt = (gaze_ts.nanoseconds - self.last_gaze_stamp.nanoseconds) / 1e9

        self.last_gaze_stamp = gaze_ts
        self.current_gaze_pos = msg.point

        if self.processing_mode == "gaze_driven":
            self._process_interaction(dt, gaze_ts)

    def _joy_callback(self, msg: Joy):
        """Handle gamepad input for trigger mode"""
        if self.interaction_mode == InteractionMode.GAMEPAD_TRIGGER:
            # Assuming button 0 is the trigger (A button on Xbox controller)
            if len(msg.buttons) > 0:
                self.external_trigger_active = bool(msg.buttons[0])

    def _process_interaction(self, dt=None, trigger_stamp=None):
        """
        --- Main processing loop - called by timer or gaze callback ---
        dt: The time delta since last gaze (for dwell accumulation)
        trigger_stamp: The timestamp of the current gaze point
        """

        # Fallback if called by timer
        if dt is None:
            dt = 1.0 / self.processing_frequency
        if trigger_stamp is None:
            trigger_stamp = self.last_gaze_stamp

        active_buttons: List[ButtonStatus] = []
        status_updates: List[ButtonStatus_msg] = []

        with self._button_lock:
            # Process each tracked button
            gaze_screen_x = self.current_gaze_pos.x
            gaze_screen_y = self.current_gaze_pos.y

            for button_id, status in self.button_statuses.items():

                # 1. Check if gaze intersects with button using new polygon-based method
                is_gazed = self._point_in_button_polygon(
                    gaze_screen_x, gaze_screen_y, status
                )
                # self.get_logger().info(
                #     f"Gaze at ({gaze_screen_x:.2f}, {gaze_screen_y:.2f}) on button {button_id}: {is_gazed}"
                # )

                # 2. Update activation level based on interaction mode
                self._update_button_activation(status, is_gazed, dt)

                # 3. Determine new button state (State Machine)
                previous_state = status.state
                status.state = self._determine_button_state(status)

                # Handle state transitions
                if previous_state != status.state:
                    self._handle_state_transition(status, previous_state, status.state)
                # If active, add button to the list
                if status.state == ButtonState.ACTIVE:
                    active_buttons.append(status)

                # 4. Build status message
                status_msg = ButtonStatus_msg()
                status_msg.header.stamp = status.last_seen_stamp.to_msg()
                status_msg.header.frame_id = "glasses_camera_dwell_time"

                status_msg.button_id = button_id
                status_msg.percent = float(status.activation_level)
                status_msg.button_status = self._state_to_int(status.state)

                # ...and copy button info
                status_msg.button.button_id = button_id
                status_msg.button.center_x = status.center_x
                status_msg.button.center_y = status.center_y
                status_msg.button.x_points = status.x_points
                status_msg.button.y_points = status.y_points

                status_updates.append(status_msg)

            # Generate debug visualization
            if self.publish_debug_image:
                self._generate_debug_image(gaze_screen_x, gaze_screen_y)

        # Publish status updates
        self._publish_status_array(status_updates)
        self._publish_active_button(active_buttons)

        self._cleanup_old_buttons(trigger_stamp)

    def _state_to_int(self, state: ButtonState):
        mapping = {
            ButtonState.INACTIVE: 0,
            ButtonState.ACTIVE: 1,
            ButtonState.HOVERED: 2,
        }
        return mapping.get(state, 0)

    def _point_in_button_polygon(
        self, x: float, y: float, button_status: ButtonStatus
    ) -> bool:
        """Check if point is inside button using polygon (quadrilateral) method"""
        if not button_status.x_points or not button_status.y_points:
            return False

        if len(button_status.x_points) != 4 or len(button_status.y_points) != 4:
            self.get_logger().warning(
                f"Button {button_status.button_id} doesn't have 4 corner points"
            )
            return False

        # Create polygon from the 4 corner points
        polygon_points = []
        for i in range(4):
            polygon_points.append(
                [button_status.x_points[i], button_status.y_points[i]]
            )

        polygon_points = np.array(polygon_points, dtype=np.float32)
        test_point = np.array([x, y], dtype=np.float32)

        # Use OpenCV's pointPolygonTest to check if point is inside polygon
        result = cv2.pointPolygonTest(polygon_points, tuple(test_point), False)
        return result >= 0  # Returns >= 0 if point is inside or on the polygon

    def _point_in_button(self, x: float, y: float, button_status: ButtonStatus) -> bool:
        """Legacy method - replaced by _point_in_button_polygon"""
        return self._point_in_button_polygon(x, y, button_status)

    def _get_button_bounding_box(
        self, button_status: ButtonStatus
    ) -> Tuple[float, float, float, float]:
        """Get axis-aligned bounding box from corner points for visualization"""
        if not button_status.x_points or not button_status.y_points:
            return 0.0, 0.0, 0.0, 0.0

        x_min = min(button_status.x_points)
        x_max = max(button_status.x_points)
        y_min = min(button_status.y_points)
        y_max = max(button_status.y_points)

        return x_min, y_min, x_max, y_max

    def _update_button_activation(
        self, status: ButtonStatus, is_gazed: bool, dt: float
    ):
        """Update button activation level based on gaze and interaction mode"""
        if is_gazed:
            # Increase activation
            increment = dt / self.dwell_duration
            status.activation_level = min(1.0, status.activation_level + increment)
        else:
            # Decrease activation
            decrement = dt / self.dwell_duration
            status.activation_level = max(0.0, status.activation_level - decrement)

    def _determine_button_state(self, status: ButtonStatus) -> ButtonState:
        """Determine button state based on activation level and interaction mode"""
        if self.interaction_mode == InteractionMode.IMMEDIATE:
            # Immediate activation on any gaze
            return (
                ButtonState.ACTIVE
                if status.activation_level > 0
                else ButtonState.INACTIVE
            )

        elif self.interaction_mode == InteractionMode.DWELL_TIME:
            # Dwell time based activation
            if status.activation_level >= self.activation_threshold:
                return ButtonState.ACTIVE
            elif status.activation_level >= self.hover_threshold:
                return ButtonState.HOVERED
            else:
                return ButtonState.INACTIVE

        elif self.interaction_mode in [
            InteractionMode.KEYBOARD_TRIGGER,
            InteractionMode.GAMEPAD_TRIGGER,
        ]:
            # External trigger required
            if status.activation_level > 0 and self.external_trigger_active:
                return ButtonState.ACTIVE
            elif status.activation_level > 0:
                return ButtonState.HOVERED
            else:
                return ButtonState.INACTIVE

        return ButtonState.INACTIVE

    def _handle_state_transition(
        self, status: ButtonStatus, old_state: ButtonState, new_state: ButtonState
    ):
        """Handle button state transitions (e.g., trigger haptic feedback)"""
        if old_state != ButtonState.ACTIVE and new_state == ButtonState.ACTIVE:
            # Button just became active
            self._trigger_haptic_feedback("button_activated")

            if self.verbose_logging:
                self.get_logger().info(f"Button {status.button_id} activated")

        elif old_state == ButtonState.INACTIVE and new_state == ButtonState.HOVERED:
            # Button just became hovered
            self._trigger_haptic_feedback("button_hover")

    def _trigger_haptic_feedback(self, feedback_type: str):
        """Send haptic feedback message"""
        msg = String()
        msg.data = feedback_type
        self.haptic_publisher.publish(msg)

    def _publish_status_array(self, status_updates: List[ButtonStatus_msg]):
        """Publish array of button statuses"""

        # self.get_logger().debug(f"Publishing status for {status_updates}")
        msg = ButtonStatusArray_msg()
        # msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "gaze_interaction"
        msg.inputs = status_updates

        self.status_publisher.publish(msg)

    def _publish_active_button(self, active_buttons: List[ButtonStatus]):
        # TODO
        """Publish information about active buttons using ButtonStatusArray_msg"""
        status_msg = ButtonStatus_msg()
        status_msg.header.frame_id = "active_button"

        # self.get_logger().info(f"Active buttons: {(active_buttons)}")

        if not active_buttons:
            # Send empty message
            # status_msg.header.stamp = self.get_clock().now().to_msg()
            status_msg.button_status = 0  # INACTIVE
            status_msg.button_id = ""
            status_msg.percent = 0.0

            # Geometry
            status_msg.button.button_id = ""
            status_msg.button.center_x = 0.0
            status_msg.button.center_y = 0.0
            status_msg.button.x_points = [0.0] * 4
            status_msg.button.y_points = [0.0] * 4

        else:
            # Pick the highest-activation active button
            max_button_status = max(active_buttons, key=lambda b: b.activation_level)

            status_msg.header.stamp = max_button_status.last_seen_stamp.to_msg()

            status_msg.button_id = max_button_status.button_id
            status_msg.button_status = 1  # ACTIVE
            status_msg.percent = float(max_button_status.activation_level)

            # Geometry
            status_msg.button.button_id = max_button_status.button_id
            status_msg.button.center_x = max_button_status.center_x
            status_msg.button.center_y = max_button_status.center_y
            status_msg.button.x_points = max_button_status.x_points
            status_msg.button.y_points = max_button_status.y_points

        self.active_button_publisher.publish(status_msg)

    def _generate_debug_image(self, gaze_x: float, gaze_y: float):
        """Generate debug visualization image"""
        # Create black image
        img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)

        # Draw buttons
        with self._button_lock:
            for button_id, status in self.button_statuses.items():
                # Choose color based on state
                if status.state == ButtonState.ACTIVE:
                    color = (0, 255, 0)  # Green
                elif status.state == ButtonState.HOVERED:
                    color = (0, 255, 255)  # Yellow
                else:
                    color = (128, 128, 128)  # Gray

                # Draw button as polygon if we have corner points
                if len(status.x_points) == 4 and len(status.y_points) == 4:
                    # Create polygon points
                    polygon_points = []
                    for i in range(4):
                        polygon_points.append(
                            [int(status.x_points[i]), int(status.y_points[i])]
                        )
                    polygon_points = np.array(polygon_points, np.int32)

                    # Draw polygon outline
                    cv2.polylines(img, [polygon_points], True, color, 5)

                    # Draw activation level as filled polygon
                    if status.activation_level > 0:
                        alpha = int(
                            255 * status.activation_level * 0.3
                        )  # 30% max opacity
                        overlay = img.copy()
                        cv2.fillPoly(overlay, [polygon_points], color)
                        cv2.addWeighted(
                            overlay, status.activation_level * 0.3, img, 1.0, 0, img
                        )

                    # Draw button ID near the center
                    cv2.putText(
                        img,
                        button_id,
                        (int(status.center_x), int(status.center_y)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        1,
                    )
                else:
                    # Fallback: draw as bounding box
                    x0, y0, x1, y1 = self._get_button_bounding_box(status)
                    cv2.rectangle(img, (int(x0), int(y0)), (int(x1), int(y1)), color, 5)

                    # Draw button ID
                    cv2.putText(
                        img,
                        button_id,
                        (int(x0), int(y0) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        1,
                    )

        # Draw gaze point
        cv2.circle(img, (int(gaze_x), int(gaze_y)), 20, (0, 0, 255), 10)  # Red circle

        # Convert and publish
        try:
            img_msg = self.cv_bridge.cv2_to_imgmsg(img, "bgr8")
            img_msg.header.stamp = self.get_clock().now().to_msg()
            img_msg.header.frame_id = "debug_image"
            self.debug_image_publisher.publish(img_msg)
        except Exception as e:
            self.get_logger().debug(f"Failed to publish debug image: {e}")

    def _cleanup_old_buttons(self, current_stamp: rclpy.time.Time):
        """Remove buttons not seen in the last X seconds of CAMERA time"""

        with self._button_lock:
            buttons_to_remove = []

            for button_id, status in self.button_statuses.items():

                if current_stamp is not None:
                    button_age = (
                        current_stamp.nanoseconds - status.last_seen_stamp.nanoseconds
                    ) / 1e9

                    if button_age > self.button_timeout:
                        buttons_to_remove.append(button_id)

            for button_id in buttons_to_remove:
                del self.button_statuses[button_id]
                if self.verbose_logging:
                    self.get_logger().debug(f"Removed stale button: {button_id}")


def main(args=None):
    rclpy.init(args=args)

    node = GazeInteractionNode()

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
