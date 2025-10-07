#!/usr/bin/env python3
"""
Gaze Controller Node

This node synchronizes gaze fixations with button activations and publishes
gaze error relative to active buttons.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from threading import Lock

# --- Import message types (adjust package names as needed) ---
from std_msgs.msg import Header, Float32
from geometry_msgs.msg import Point, Vector3
from gaze_interaction_manager.msg import ButtonStatus as ButtonStatus_msg
from pupil_neon_ros.msg import GazeData, GazeEvent  # <-- adjust if your msgs differ

# Custom output (you can replace with whatever you want)
from geometry_msgs.msg import PointStamped


class GazeControllerNode(Node):
    def __init__(self):
        super().__init__("gaze_controller_node")

        # Parameters for modular logic
        self.declare_parameter("use_fixation_condition", True)
        self.declare_parameter("use_button_condition", True)

        self.use_fixation_condition = self.get_parameter("use_fixation_condition").value
        self.use_button_condition = self.get_parameter("use_button_condition").value

        # Internal state
        self._lock = Lock()
        self.active_button_status : ButtonStatus_msg = None
        
        self.fixation_active = False
        self.dwell_active = False
        self.intersection_active = False

        self.last_fixation_end_ns = 0
        self.latest_saccade_end_ns = 0


        # Correction factor
        self.gaze_correction = Vector3()  # Placeholder for gaze correction values
        self.gaze_correction.x = 0.0
        self.gaze_correction.y = 0.0
        self.gaze_correction.z = 0.0

        self.max_offset = 30 # px

        # ROS interfaces
        qos = QoSProfile(depth=10)

        # Subscribers
        self.sub_saccade = self.create_subscription(
            GazeEvent,
            "pupil_glasses/event/saccade",
            self._saccade_cb,
            qos,
        )
        self.sub_fix_end = self.create_subscription(
            GazeEvent,
            "pupil_glasses/event/fixation",
            self._fixation_end_cb,
            qos,
        )
        self.sub_buttons = self.create_subscription(
            ButtonStatus_msg,
            "/dwell_time/active_button",
            self._buttons_cb,
            qos,
        )
        self.sub_gaze = self.create_subscription(
            GazeData, "pupil_glasses/gaze_data", self._gaze_cb, qos
        )

        # Publisher for gaze error
        self.error_pub = self.create_publisher(
            PointStamped, "/gaze_controller/error", 10
        )
        self.corrected_gaze_pub = self.create_publisher(
            PointStamped, "/gaze_controller/corrected_gaze", 10
        )
        self.correction_offset = self.create_publisher(
            PointStamped, "/gaze_controller/correction_offset", 10
        )

        # Repeat for dwell received (true/false)
        self.dwell_pub = self.create_publisher(
            Float32, "/gaze_controller/dwell_enabled", 10
        )
        # Repeat for Fixation received (true/false)
        self.gaze_pub = self.create_publisher(
            Float32, "/gaze_controller/fixation_enabled", 10
        )
        # Repeat for intersection received (true/false)
        self.intersection_pub = self.create_publisher(
            Float32, "/gaze_controller/intersection_enabled", 10
        )

        self.get_logger().info("Gaze Controller Node initialized.")

    # ---------------- Callbacks ---------------- #

    # Received saccade message, means fixation is starting
    def _saccade_cb(self, msg: GazeEvent):
        with self._lock:
            # self.latest_saccade_end_ns = msg.end_time_ns
            # if self.latest_saccade_end_ns > self.last_fixation_end_ns:
            self.fixation_active = True
            # self.get_logger().info("Fixation started.")

    # Received fixation message, means fixation has ended
    def _fixation_end_cb(self, msg: GazeEvent): 
        with self._lock:
            # self.last_fixation_end_ns = msg.end_time_ns
            self.fixation_active = False
            # self.get_logger().info("Fixation ended.")

    def _buttons_cb(self, msg: ButtonStatus_msg):
        with self._lock:    
            if msg.button_status == ButtonStatus_msg.BUTTON_INACTIVE:  # INACTIVE
                self.dwell_active = False
                self.active_button_status = None
            elif msg.button_status == ButtonStatus_msg.BUTTON_ACTIVE:  # ACTIVE
                self.dwell_active = True
                self.active_button_status = msg
                # self.get_logger().info(f"Received button with center at: {self.active_button_status.center_x}, {self.active_button_status.center_y}")
            else:
                # Hovered or undefined
                self.dwell_active = False


    def _gaze_cb(self, gaze_msg: GazeData):
        with self._lock:
            

            # Timing debug information
            self.debug_pub()

            # 1. Activate compensation?
            self.intersection_active = self._check_event_active()
            if self.intersection_active and self.active_button_status is not None:
                try:
                    # 2. Compute error with active button
                    err_x = gaze_msg.x - self.active_button_status.button.center_x
                    err_y = gaze_msg.y - self.active_button_status.button.center_y
                    # self.get_logger().info(f"Gaze at: {gaze_msg.x}, {gaze_msg.y}")
                    # self.get_logger().info(f"Button center at: {self.active_button_status.center_x}, {self.active_button_status.center_y}")
                    # self.get_logger().info(f"Corrected gaze by: {err_x}, {err_y}")

                    # Store, limit to 20px each side
                    if abs(err_x) < self.max_offset and abs(err_y) < self.max_offset:
                        # self.get_logger().info("Correction applied")
                        self.gaze_correction.x = max(-self.max_offset, min(self.max_offset, err_x))
                        self.gaze_correction.y = max(-self.max_offset, min(self.max_offset, err_y))
                    else:
                        pass
                        # self.get_logger().info(f"No correction applied, big error")
                    
                    self.gaze_correction.z = 0.0

                except Exception as e:
                    self.get_logger().error(f"Error computing gaze error: {e}")
                    # show traceback

                    
                    return
            else:
                self.gaze_correction.x = 0.0
                self.gaze_correction.y = 0.0
                self.gaze_correction.z = 0.0
            
            # 3. Apply correction and publish corrected gaze
            # TODO: To different node?
            corrected_gaze_msg = PointStamped()
            corrected_gaze_msg.header = Header()
            corrected_gaze_msg.header.stamp = self.get_clock().now().to_msg()
            corrected_gaze_msg.header.frame_id = "gaze_controller"

            corrected_gaze_msg.point = Point(x=gaze_msg.x - self.gaze_correction.x, 
                                             y=gaze_msg.y - self.gaze_correction.y, 
                                             z=0.0)

            self.corrected_gaze_pub.publish(corrected_gaze_msg)
            # Correction debug information
            corrected_gaze_msg.point = Point(x=self.gaze_correction.x, 
                                             y=self.gaze_correction.y, 
                                             z=0.0)
            self.correction_offset.publish(corrected_gaze_msg)

            # Publish as PointStamped
            err_msg = corrected_gaze_msg
            err_msg.point = Point(x=self.gaze_correction.x, y=self.gaze_correction.y, z=0.0)
            self.error_pub.publish(err_msg)

    def debug_pub(self):

        # Visualize intersection conditions
        # Repeat for dwell received (true/false)
        self.dwell_pub.publish(Float32(data=float(self.dwell_active)+0.0))

        # Repeat for Fixation received (true/false)
        self.gaze_pub.publish(Float32(data=float(self.fixation_active)-1.0))

        # Repeat for intersection received (true/false)
        self.intersection_pub.publish(Float32(data=float(self.intersection_active)-2.0))



    # ---------------- Helpers ---------------- #

    def _check_event_active(self) -> bool:
        """Check if conditions for event are satisfied."""
        active = True
        if self.use_fixation_condition:
            active = active and self.fixation_active
        if self.use_button_condition:
            active = active and self.dwell_active
        return active


def main(args=None):
    rclpy.init(args=args)
    node = GazeControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
