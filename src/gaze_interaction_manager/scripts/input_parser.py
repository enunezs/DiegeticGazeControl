#!/usr/bin/env python3
"""
Parser node: ButtonStatus → Robot Commands

Converts single ButtonStatus messages to semantic button events
that the controller can understand.

This sits between your gaze system and the robot controller.
"""

import rclpy
from rclpy.node import Node

from gaze_interaction_manager.msg import ButtonStatus as ButtonStatus_msg
from std_msgs.msg import String
import yaml
import traceback


class InputParser(Node):
    """Parses ButtonStatus_msg into semantic button commands"""
    
    def __init__(self):
        super().__init__('input_parser_node')
        
        # Load button mappings
        config_file = self.declare_parameter(
            'config_file',
            'src/gaze_interaction_manager/config/button_config.yaml'
        ).value
        self.config = self._load_config(config_file)
        
        # Subscriber - receives single ButtonStatus messages
        self.input_sub = self.create_subscription(
            ButtonStatus_msg,
            '/dwell_time/active_button',
            self.parse_input,
            1
        )
        
        # Publisher
        self.button_pub = self.create_publisher(
            String,
            '/diegetic_inputs/robot_commands',
            1
        )
        
        # Track previous state for edge detection (button_id → previous status)
        self.prev_button_status = {}
        
        self.get_logger().info("Input Parser ready")
    
    def _load_config(self, path: str) -> dict:
        """Load YAML configuration"""
        try:
            with open(path, 'r') as f:
                self.get_logger().info(f"Loading config from {path}")
                return yaml.safe_load(f)
        except Exception as e:
            self.get_logger().error(f"Failed to load config: {e}")
            return {}
    
    def parse_input(self, msg: ButtonStatus_msg):
        """
        Parse single ButtonStatus_msg and emit button commands on state change
        
        Example:
          ButtonStatus_msg(button_id="button_0", button_status=BUTTON_ACTIVE, percent=1.0)
          ↓
          Look up in config: button_0 → "vel_x_pos"
          ↓
          Publish: "vel_x_pos:press"
        """
        try:
            # self.get_logger().info(f"Parsing input: {msg}")
            button_id = msg.button_id
            button_status = msg.button_status
            
            # Get previous status for edge detection
            prev_status = self.prev_button_status.get(button_id, None)
            
            # Only process on state change
            if button_status == prev_status:
                return
            
            # Look up what this button maps to
            input_mappings = self.config.get('input_to_button_mappings', {})
            
            if button_id not in input_mappings:
                self.get_logger().warning(f"Unmapped button: {button_id}")
                self.prev_button_status[button_id] = button_status
                return
            
            button_name = input_mappings[button_id]
            
            # Detect press vs release
            if button_status == ButtonStatus_msg.BUTTON_ACTIVE:
                # Button pressed
                self.emit_button_command(button_name, "press")
            
            elif button_status == ButtonStatus_msg.BUTTON_INACTIVE:
                # Button released
                self.emit_button_command(button_name, "release")
            
            elif button_status == ButtonStatus_msg.BUTTON_HOVER:
                # Hover state - optional, you may ignore or handle differently
                pass
            
            # Update tracking
            self.prev_button_status[button_id] = button_status
        
        except Exception as e:
            self.get_logger().error(f"Error parsing input: {e}")
            traceback.print_exc()
    
    def emit_button_command(self, button_name: str, action: str):
        """Emit a button command as a string message"""
        msg = String()
        msg.data = f"{button_name}:{action}"
        self.button_pub.publish(msg)
        self.get_logger().info(f"Button event: {button_name} {action}")


def main():
    rclpy.init()
    parser = InputParser()
    
    print("Input Parser Node is Running...")
    
    try:
        rclpy.spin(parser)
    except KeyboardInterrupt:
        pass
    finally:
        parser.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()