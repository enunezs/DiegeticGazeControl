#!/usr/bin/env python3
# joy_command_mapper.py

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32
from geometry_msgs.msg import TwistStamped, PoseStamped
from sensor_msgs.msg import Joy
from scipy.spatial.transform import Rotation
from builtin_interfaces.msg import Time
import math
from typing import Dict, Optional, Tuple, Set
from robot_command_mapper import ButtonStateManager, CommandMapper

"""
Joystick-based version of CommandMapper.
Subscribes to /joy (sensor_msgs/Joy) instead of /dwell_time/active_button.
Outputs are identical to the gaze version.
"""

class JoyCommandMapper(CommandMapper):
    def __init__(self):
        super().__init__()
        self.get_logger().info("JoyCommandMapper starting...")

        # Replace gaze button subscriber with joy input
        self.destroy_subscription(self.button_sub)
        self.button_sub = self.create_subscription(
            Joy, '/joy', self.joy_callback, 10
        )

        # Mapping joystick buttons to button IDs
        # Only mode changes remain; others commented
        self.joy_to_button_id = {
            0: "ContinueWaypoints",          # A button
            1: "PauseWaypoints",          # B button
            2: "SwitchRef1",  # X button -> Mode change
            3: "WaypointDemo",  # Y button -> Mode change
            # 4: "TL",         # LB
            # 5: "TR",         # RB
            # 6: "S1RotZ_+1",  # Back
            # 7: "S1RotZ_-1",  # Start
        }

        # D-pad axes indices (commonly axes[6] = left/right, axes[7] = up/down)
        # Shoulder buttons difference for depth: e.g., RB - LB
        self.axis_threshold = 0.6

    def joy_callback(self, msg: Joy):
        """Handle incoming /joy messages and map to gaze-style button IDs."""

        now = self.get_clock().now().nanoseconds / 1e9
        edges = {}

        # --- Buttons ---
        for idx, pressed in enumerate(msg.buttons):
            button_id = self.joy_to_button_id.get(idx)
            if not button_id:
                continue
            edge = self.button_state_mgr.update_button(button_id, int(pressed), now)
            if edge:
                edges[button_id] = edge

        # --- Continuous twist via D-pad ---
        if len(msg.axes) >= 8:  # Ensure D-pad axes exist
            dpad_x = msg.axes[6]  # -1 left, +1 right
            dpad_y = msg.axes[7]  # -1 down, +1 up

            # Left/right
            if dpad_x > self.axis_threshold:
                edge = self.button_state_mgr.update_button("RightHybrid", 1, now)
                if edge: edges["RightHybrid"] = edge
            elif dpad_x < -self.axis_threshold:
                edge = self.button_state_mgr.update_button("LeftHybrid", 1, now)
                if edge: edges["LeftHybrid"] = edge
            else:
                for b in ["LeftHybrid", "RightHybrid"]:
                    edge = self.button_state_mgr.update_button(b, 0, now)
                    if edge: edges[b] = edge

            # Up/down
            if dpad_y > self.axis_threshold:
                edge = self.button_state_mgr.update_button("UpHybrid", 1, now)
                if edge: edges["UpHybrid"] = edge
            elif dpad_y < -self.axis_threshold:
                edge = self.button_state_mgr.update_button("DownHybrid", 1, now)
                if edge: edges["DownHybrid"] = edge
            else:
                for b in ["UpHybrid", "DownHybrid"]:
                    edge = self.button_state_mgr.update_button(b, 0, now)
                    if edge: edges[b] = edge

        # --- Depth via shoulder buttons difference ---
        if len(msg.buttons) >= 6:  # LB = 4, RB = 5
            depth = msg.buttons[5] - msg.buttons[4]  # RB - LB
            if depth > 0:
                edge = self.button_state_mgr.update_button("FartherHybrid", 1, now)
                if edge: edges["FartherHybrid"] = edge
                edge = self.button_state_mgr.update_button("CloserHybrid", 0, now)
                if edge: edges["CloserHybrid"] = edge
            elif depth < 0:
                edge = self.button_state_mgr.update_button("CloserHybrid", 1, now)
                if edge: edges["CloserHybrid"] = edge
                edge = self.button_state_mgr.update_button("FartherHybrid", 0, now)
                if edge: edges["FartherHybrid"] = edge
            else:
                for b in ["FartherHybrid", "CloserHybrid"]:
                    edge = self.button_state_mgr.update_button(b, 0, now)
                    if edge: edges[b] = edge

        # --- Process edges ---
        for btn_id, edge in edges.items():
            self._process_button_edge(btn_id, edge, now)

        # --- Update continuous velocity state ---
        self._update_velocity_commands()


def main(args=None):
    rclpy.init(args=args)
    node = JoyCommandMapper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
