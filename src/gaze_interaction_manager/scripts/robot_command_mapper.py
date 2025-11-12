#!/usr/bin/env python3
# command_mapper.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import TwistStamped, PoseStamped
from builtin_interfaces.msg import Time

from gaze_interaction_manager.msg import ButtonStatus as ButtonStatusMsg

import math

"""
Minimal mapping node:
- Subscribes to /dwell_time/active_button (ButtonStatus)
- Subscribes to /teleop/current_mode (String)
- Publishes:
    /teleop/cartesian_velocity -> TwistStamped (continuous)
    /teleop/discrete_pose   -> PoseStamped (on command)
    /teleop/system          -> String (on command)
    /teleop/mode_command    -> String (used to ask ModeManager to switch)
"""

class CommandMapper(Node):

    def __init__(self):
        super().__init__('command_mapper')
        self.get_logger().info("CommandMapper starting...")
        self.current_mode = "translation"

        # Publishers
        self.vel_pub = self.create_publisher(TwistStamped, '/teleop/cartesian_velocity', 10)
        self.pose_pub = self.create_publisher(PoseStamped, '/teleop/discrete_pose', 10)
        self.sys_pub = self.create_publisher(String, '/teleop/system', 10)
        self.mode_cmd_pub = self.create_publisher(String, '/teleop/mode_command', 10)

        # Subscribers
        self.button_sub = self.create_subscription(ButtonStatusMsg, '/dwell_time/active_button', self.button_callback, 10)
        self.mode_sub = self.create_subscription(String, '/teleop/current_mode', self.mode_callback, 10)

        ### TODO: Mode-aware mapping for testing. (Later: load from YAML)
        # Structure: button_id -> mode -> action_params
        # Use "*" as wildcard for mode-independent buttons
        # action_type: "velocity" (continuous, hold-based) or "discrete" (one-shot pose/rotation)
        # axis: x,y,z for linear, rx,ry,rz for angular
        self.mode_mappings = {
            # Mode-specific hybrid buttons (different behavior per mode)
            "UpHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "x",
                    "speed": 0.05,
                    "reference_frame": "base_link"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "rx",
                    "speed": 0.3,  # rad/s
                    "reference_frame": "base_link"
                }
            },
            "DownHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "x",
                    "speed": -0.05,
                    "reference_frame": "base_link"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "rx",
                    "speed": -0.3,
                    "reference_frame": "base_link"
                }
            },
            "LeftHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "y",
                    "speed": 0.03,
                    "reference_frame": "base_link"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "ry",
                    "speed": 0.3,
                    "reference_frame": "base_link"
                }
            },
            "RightHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "y",
                    "speed": -0.03,
                    "reference_frame": "base_link"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "ry",
                    "speed": -0.3,
                    "reference_frame": "base_link"
                }
            },
            "CloserHybrid"  : {
                "translation": {
                    "action_type": "velocity",
                    "axis": "z",
                    "speed": -0.03,
                    "reference_frame": "base_link"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "rz",
                    "speed": -0.3,
                    "reference_frame": "base_link"
                }
            },
            "FartherHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "z",
                    "speed": 0.03,
                    "reference_frame": "base_link"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "rz",
                    "speed": 0.3,
                    "reference_frame": "base_link"
                }
            },
            "SwitchRef1": {
                "*": {
                    "action_type": "mode",
                    "mode_cmd": "toggle_next"
                }
            },
            "SwitchRef2": {
                "*": {
                    "action_type": "mode",
                    "mode_cmd": "toggle_next"
                }
            },
            # Mode-independent buttons (always use velocity, continuous)
            "S1X_+1": {
                "*": {
                    "action_type": "velocity",
                    "axis": "x",
                    "speed": 0.05,
                    "reference_frame": "base_link"
                }
            },
            "S1X_-1": {
                "*": {
                    "action_type": "velocity",
                    "axis": "x",
                    "speed": -0.05,
                    "reference_frame": "base_link"
                }
            },
            "S1Y_+1": {
                "*": {
                    "action_type": "velocity",
                    "axis": "y",
                    "speed": 0.03,
                    "reference_frame": "base_link"
                }
            },
            "S1Y_-1": {
                "*": {
                    "action_type": "velocity",
                    "axis": "y",
                    "speed": -0.03,
                    "reference_frame": "base_link"
                }
            },
            "TR": {
                "*": {
                    "action_type": "velocity",
                    "axis": "z",
                    "speed": 0.03,
                    "reference_frame": "base_link"
                }
            },
            "TL": {
                "*": {
                    "action_type": "velocity",
                    "axis": "z",
                    "speed": -0.03,
                    "reference_frame": "base_link"
                }
            },
            # Discrete rotation buttons (step-based, one-shot)
            "S1RotZ_+1": {
                "*": {
                    "action_type": "discrete",
                    "axis": "rz",
                    "step_deg": 30.0,
                    "reference_frame": "base_link"
                }
            },
            "S1RotZ_-1": {
                "*": {
                    "action_type": "discrete",
                    "axis": "rz",
                    "step_deg": -30.0,
                    "reference_frame": "base_link"
                }
            },
            # System commands
            "S1Reset": {
                "*": {
                    "action_type": "system",
                    "cmd": "reset_pose"
                }
            },
            "A": {
                "*": {
                    "action_type": "mode",
                    "mode_cmd": "toggle_next"
                }
            },
            "B": {
                "*": {
                    "action_type": "mode",
                    "mode_cmd": "toggle_next"
                }
            },
        }

        # Debouncing
        self.last_button_state = {}  # store last seen status per button
        self.debounce_time = 0.3  # seconds
        self.last_trigger_time = {}  # store last trigger per button

        # Velocity state tracking
        self.held_velocity_buttons = set()  # buttons currently held that produce velocity
        self.current_velocity_params = {}  # params of the "active" velocity command (last one pressed)

        # Timer to publish velocity continuously at 50 Hz
        self.vel_publish_timer = self.create_timer(0.02, self.publish_velocity_tick)


    def mode_callback(self, msg: String):
        self.current_mode = msg.data
        self.get_logger().info(f"CommandMapper: current_mode = {self.current_mode}")

    def get_action_for_button(self, button_id):
        """
        Look up action parameters for a button in the current mode.
        Returns (action_type, params) or (None, None) if not found.
        Supports wildcard "*" for mode-independent buttons.
        """
        if button_id not in self.mode_mappings:
            return None, None
        
        mode_dict = self.mode_mappings[button_id]
        
        # Try current mode first
        if self.current_mode in mode_dict:
            params = mode_dict[self.current_mode]
            return params.get("action_type"), params
        
        # Fallback to wildcard
        if "*" in mode_dict:
            params = mode_dict["*"]
            return params.get("action_type"), params
        
        # No mapping found for this mode
        self.get_logger().warn(f"Button {button_id} has no mapping for mode '{self.current_mode}'")
        return None, None

    def button_callback(self, msg):
        button_id = msg.button_id
        status = msg.button_status
        now = self.get_clock().now().nanoseconds / 1e9
        
        # self.get_logger().info(f"[RECV] Button '{button_id}', status={status}")
        
        if status is None or button_id is None:
            self.get_logger().warn("Received button msg without expected fields.")
            return
        
        # Empty button_id means all buttons are released
        if button_id == "":
            # self.get_logger().debug(f"[RELEASE_ALL] All buttons released at {now}")
            self.held_velocity_buttons.clear()
            self.current_velocity_params = {}
            return
        
        # Look up action for this button in current mode
        action_type, params = self.get_action_for_button(button_id)
        
        if action_type is None:
            self.get_logger().info(f"No mapping defined for {button_id} in mode {self.current_mode}")
            return
        
        prev_status = self.last_button_state.get(button_id, 0)
        self.last_button_state[button_id] = status
        
        BUTTON_ACTIVE = getattr(msg, "BUTTON_ACTIVE", 1)
        
        # Handle button release
        if status != BUTTON_ACTIVE:
            # Button released
            if action_type == "velocity":
                self.held_velocity_buttons.discard(button_id)
                # If this was the active velocity button, clear params
                if button_id in self.held_velocity_buttons or not self.held_velocity_buttons:
                    self.current_velocity_params = {}
            return
        
        # Button is now active
        if action_type == "velocity":
            # Track this velocity button as held (continuous command)
            self.held_velocity_buttons.add(button_id)
            self.current_velocity_params = params
            self.get_logger().info(f"[VELOCITY_HOLD] Button {button_id} held: {params}")
            return
        
        # For discrete, system, and mode commands: debounce and trigger on new press only
        if prev_status != BUTTON_ACTIVE:
            # This is a new press (prev was inactive, now active)
            last_trigger_time = self.last_trigger_time.get(button_id, 0)
            time_since_trigger = now - last_trigger_time
            
            self.get_logger().info(f"[NEW_PRESS] Button {button_id}: {time_since_trigger:.3f}s since last trigger")
            
            # Apply debounce only to new presses
            if time_since_trigger < self.debounce_time:
                self.get_logger().info(f"[DEBOUNCE] Ignoring press (too soon)")
                return
            
            # Passed debounce - trigger the action
            self.last_trigger_time[button_id] = now
            self.get_logger().info(f"[ACTION] Triggering {action_type} for {button_id}")
            
            if action_type == "discrete":
                self.publish_discrete(params)
            elif action_type == "system":
                self.publish_system(params)
            elif action_type == "mode":
                self.publish_mode_command(params)
        else:
            # Button was already active, still active - ignore (hold state, already handled for velocity)
            return

    def publish_velocity_tick(self):
        """Called periodically (50 Hz) to publish current velocity state."""
        twist = TwistStamped()
        twist.header.stamp = self.get_clock().now().to_msg()
        
        if self.current_velocity_params:
            params = self.current_velocity_params
            axis = params.get("axis", "x")
            speed = float(params.get("speed", 0.0))
            reference_frame = params.get("reference_frame", "base_link")
            
            # Use the reference frame from params (BUG FIX)
            twist.header.frame_id = reference_frame
            
            # Initialize all to zero
            twist.twist.linear.x = 0.0
            twist.twist.linear.y = 0.0
            twist.twist.linear.z = 0.0
            twist.twist.angular.x = 0.0
            twist.twist.angular.y = 0.0
            twist.twist.angular.z = 0.0

            # Set the appropriate axis (merged linear and angular)
            if axis == "x":
                twist.twist.linear.x = speed
            elif axis == "y":
                twist.twist.linear.y = speed
            elif axis == "z":
                twist.twist.linear.z = speed
            elif axis == "rx":
                twist.twist.angular.x = speed
            elif axis == "ry":
                twist.twist.angular.y = speed
            elif axis == "rz":
                twist.twist.angular.z = speed
        else:
            # Publish zero velocity if no buttons held
            twist.header.frame_id = "base_link"
            twist.twist.linear.x = 0.0
            twist.twist.linear.y = 0.0
            twist.twist.linear.z = 0.0
            twist.twist.angular.x = 0.0
            twist.twist.angular.y = 0.0
            twist.twist.angular.z = 0.0
        
        self.vel_pub.publish(twist)

    def publish_discrete(self, params):
        """
        Publish a discrete pose/rotation command.
        For rotations: sends a relative rotation as a quaternion.
        For translations: sends a relative position delta.
        """
        axis = params.get("axis", "z")
        reference_frame = params.get("reference_frame", "base_link")
        
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = reference_frame  # Use reference frame from params (BUG FIX)
        
        # Check if this is a rotation (rx, ry, rz) or translation (x, y, z)
        if axis.startswith("r"):
            # Discrete rotation
            step_deg = float(params.get("step_deg", 30.0))
            
            # Represent rotation as quaternion
            from scipy.spatial.transform import Rotation
            rads = math.radians(step_deg)
            
            if axis == "rx":
                r = Rotation.from_euler('x', rads, degrees=False)
            elif axis == "ry":
                r = Rotation.from_euler('y', rads, degrees=False)
            else:  # rz
                r = Rotation.from_euler('z', rads, degrees=False)

            q = r.as_quat()  # x, y, z, w
            pose.pose.orientation.x = float(q[0])
            pose.pose.orientation.y = float(q[1])
            pose.pose.orientation.z = float(q[2])
            pose.pose.orientation.w = float(q[3])
            
            # Position left zero for pure rotation
            pose.pose.position.x = 0.0
            pose.pose.position.y = 0.0
            pose.pose.position.z = 0.0
            
            self.get_logger().info(f"Published discrete rotation: axis={axis} step_deg={step_deg} frame={reference_frame}")
        else:
            # Discrete translation
            step_m = float(params.get("step_m", 0.05))
            
            # Set position delta
            pose.pose.position.x = step_m if axis == "x" else 0.0
            pose.pose.position.y = step_m if axis == "y" else 0.0
            pose.pose.position.z = step_m if axis == "z" else 0.0
            
            # Identity orientation (no rotation)
            pose.pose.orientation.x = 0.0
            pose.pose.orientation.y = 0.0
            pose.pose.orientation.z = 0.0
            pose.pose.orientation.w = 1.0
            
            self.get_logger().info(f"Published discrete translation: axis={axis} step_m={step_m} frame={reference_frame}")

        self.pose_pub.publish(pose)

    def publish_system(self, params):
        cmd = params.get("cmd", "noop")
        msg = String()
        msg.data = cmd
        self.sys_pub.publish(msg)
        self.get_logger().info(f"Published system command: {cmd}")

    def publish_mode_command(self, params):
        # Mode change request to ModeManager
        cmd = String()
        cmd.data = params["mode_cmd"]
        
        # send mode change request to ModeManager
        self.mode_cmd_pub.publish(cmd)
        self.get_logger().info(f"Published mode_command: {cmd.data}")


def main(args=None):
    rclpy.init(args=args)
    node = CommandMapper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()