"""
ROS2 Bridge for Gaze Screen Interface
Handles all ROS2 communication including publishing button positions
and subscribing to button status updates and gaze data.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from geometry_msgs.msg import PointStamped
from std_msgs.msg import Header
from diegetic_transform_engine.msg import DiegeticButton2DArray, DiegeticButton2D
from gaze_interaction_manager.msg import ButtonStatus


from PySide6.QtCore import QObject, Signal


"""
Qt-friendly wrapper around ROS2 node.
Emits Qt signals when ROS messages arrive.

Outputs:
The list of on-screen, interactive buttons as a DiegeticButton2DArray everytime there is a change.
Changes are reported from the Screen Interface.

Inputs:
A ButtonStatus_msg message with the button status updates. 

"""


class RosBridge(QObject):

    # Qt Signals
    button_status_received = Signal(str, int, float)  # button_id, status, percent
    gaze_point_received = Signal(float, float)  # x, y coordinates

    def __init__(self, node_name="gaze_screen_interface"):
        super().__init__()

        # Initialize ROS2 node
        if not rclpy.ok():
            rclpy.init()

        self.node = Node(node_name)

        # QoS profile for real-time data
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Publishers
        self.button_array_pub = self.node.create_publisher(
            DiegeticButton2DArray, "/screen_buttons", qos_profile
        )

        # Subscribers
        self.button_status_sub = self.node.create_subscription(
            ButtonStatus, "/active_button", self._button_status_callback, qos_profile
        )

        self.gaze_sub = self.node.create_subscription(
            PointStamped,
            "/gaze_controller/corrected_gaze",
            self._gaze_callback,
            qos_profile,
        )

        self.node.get_logger().info(f"ROS Bridge initialized: {node_name}")

    def publish_buttons(self, buttons_data):
        """
        Publish button array to ROS2.

        Args:
            buttons_data: List of dicts with keys:
                - button_id (str)
                - center_x (float): normalized [0,1]
                - center_y (float): normalized [0,1]
                - x_points (list[float]): 4 corner x coords, normalized
                - y_points (list[float]): 4 corner y coords, normalized
        """
        msg = DiegeticButton2DArray()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = "screen"

        for btn_data in buttons_data:
            btn = DiegeticButton2D()
            btn.button_id = btn_data["button_id"]
            btn.center_x = btn_data["center_x"]
            btn.center_y = btn_data["center_y"]
            btn.x_points = btn_data["x_points"]
            btn.y_points = btn_data["y_points"]
            msg.buttons.append(btn)

        self.button_array_pub.publish(msg)
        self.node.get_logger().info(
            f"Menu updated. Published {len(buttons_data)} buttons"
        )

    def _button_status_callback(self, msg):
        """Handle incoming button status updates."""
        self.button_status_received.emit(msg.button_id, msg.button_status, msg.percent)

    def _gaze_callback(self, msg):
        """Handle incoming gaze point data."""
        self.gaze_point_received.emit(msg.point.x, msg.point.y)

    def spin_once(self, timeout_sec=0.0):
        """Process ROS callbacks. Call this from Qt timer."""
        rclpy.spin_once(self.node, timeout_sec=timeout_sec)

    def shutdown(self):
        """Clean shutdown of ROS2 node."""
        self.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
