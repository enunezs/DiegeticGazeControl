#!/usr/bin/env python3
# command_mapper.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32
from geometry_msgs.msg import TwistStamped, PoseStamped
from builtin_interfaces.msg import Time

from gaze_interaction_manager.msg import ButtonStatus as ButtonStatusMsg

import math
from typing import Dict, Optional, Tuple, Set
from scipy.spatial.transform import Rotation

"""
Command mapping node:
- Subscribes to /dwell_time/active_button (ButtonStatus)
- Subscribes to /teleop/current_mode (String)
- Publishes:
    /teleop/cartesian_velocity -> TwistStamped (continuous)
    /teleop/discrete_pose   -> PoseStamped (on command)
    /teleop/system          -> String (on command)
    /teleop/mode_command    -> String (used to ask ModeManager to switch)
"""


class ButtonStateManager:
    """
    Manages button state tracking, debouncing, and edge detection.
    """
    
    def __init__(self, debounce_time: float = 0.3):
        self.debounce_time = debounce_time
        self.last_state: Dict[str, int] = {}
        self.last_trigger_time: Dict[str, float] = {}
        self.held_buttons: Set[str] = set()
    
    def update_button(self, button_id: str, status: int, current_time: float) -> Optional[str]:
        """
        Update state for a single button and detect edges.
        
        Args:
            button_id: Button identifier
            status: Current status (1 for active, 0 for inactive)
            current_time: Current timestamp in seconds
            
        Returns:
            Edge type: 'rising', 'falling', 'hold', or None
        """
        prev_status = self.last_state.get(button_id, 0)
        self.last_state[button_id] = status
        
        # Rising edge detection (button pressed)
        if status == 1 and prev_status != 1:
            if self._can_trigger(button_id, current_time):
                self.last_trigger_time[button_id] = current_time
                self.held_buttons.add(button_id)
                return 'rising'
            return None
        
        # Falling edge detection (button released)
        elif status == 0 and prev_status == 1:
            self.held_buttons.discard(button_id)
            return 'falling'
        
        # Hold state
        elif status == 1 and prev_status == 1:
            return 'hold'
        
        return None
    
    def update_all_buttons(self, active_button_id: Optional[str], active_status: int, current_time: float) -> Dict[str, str]:
        """
        Update all tracked buttons, marking non-active ones as released.
        
        Args:
            active_button_id: The currently active button (or None if no button active)
            active_status: Status of the active button
            current_time: Current timestamp in seconds
            
        Returns:
            Dictionary mapping button_id to edge type for all buttons that changed
        """
        edges = {}
        
        # Update the active button if provided
        if active_button_id:
            edge = self.update_button(active_button_id, active_status, current_time)
            if edge:
                edges[active_button_id] = edge
        
        # Check all other tracked buttons for auto-release
        for button_id in list(self.last_state.keys()):
            if button_id == active_button_id:
                continue
            
            prev_status = self.last_state.get(button_id, 0)
            
            # If button was active but not in current message, mark as released
            if prev_status == 1:
                edge = self.update_button(button_id, 0, current_time)
                if edge:
                    edges[button_id] = edge
        
        return edges
    
    def _can_trigger(self, button_id: str, current_time: float) -> bool:
        """Check if enough time has passed since last trigger (debouncing)."""
        last_trigger = self.last_trigger_time.get(button_id, 0)
        return (current_time - last_trigger) >= self.debounce_time
    
    def is_held(self, button_id: str) -> bool:
        """Check if a button is currently held down."""
        return button_id in self.held_buttons
    
    def get_all_held_buttons(self) -> Set[str]:
        """Get all currently held buttons."""
        return self.held_buttons.copy()


class CommandMapper(Node):
    """
    Maps gaze-based button interactions to robot control commands.
    Supports multiple control modes with different button behaviors.
    """
    
    # Button status constants
    BUTTON_INACTIVE = 0
    BUTTON_ACTIVE = 1

    def __init__(self):
        super().__init__('command_mapper')
        self.get_logger().info("CommandMapper starting...")
        
        # Current control mode
        self.current_mode = "translation"
        
        # Button state management
        self.button_state_mgr = ButtonStateManager(debounce_time=0.3)
        
        # Velocity tracking
        self.current_velocity_params: Dict = {}
        
        self._init_publishers()
        self._init_subscribers()
        
        # TODO: Load mode mappings (move to YAML config)
        self._init_mode_mappings()
        
        # Timer to publish velocity continuously at 100 Hz
        self.vel_publish_timer = self.create_timer(0.01, self._publish_velocity_tick)

    def _init_publishers(self):
        """Initialize all ROS publishers."""
        self.vel_pub = self.create_publisher(TwistStamped, '/teleop/cartesian_velocity', 10)
        self.pose_pub = self.create_publisher(PoseStamped, '/teleop/discrete_pose', 10)
        
        self.sys_pub = self.create_publisher(String, '/teleop/system', 10)
        self.mode_cmd_pub = self.create_publisher(String, '/teleop/mode_command', 10)
        
        # Publisher for button sound events
        self.button_sound_pub = self.create_publisher(Int32, '/button_events', 10)

    def _init_subscribers(self):
        """Initialize all ROS subscribers."""
        self.button_sub = self.create_subscription(
            ButtonStatusMsg, 
            '/dwell_time/active_button', 
            self.button_callback, 
            10
        )
        self.mode_sub = self.create_subscription(
            String, 
            '/teleop/current_mode', 
            self.mode_callback, 
            10
        )

    def _init_mode_mappings(self):
        """
        Initialize mode-aware button mappings.
        
        Structure: button_id -> mode -> action_params
        - Use "*" as wildcard for mode-independent buttons
        - action_type: "velocity" (continuous), "discrete" (one-shot), "system", or "mode"
        - axis: x,y,z for linear, rx,ry,rz for angular
        
        TODO: Load from YAML configuration file
        """
        self.mode_mappings = {
            # Mode-specific hybrid buttons (different behavior per mode)
            "UpHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "x",
                    "speed": 0.05,
                    "reference_frame": "j2n6s300_link_base"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "rx",
                    "speed": 0.3,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "DownHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "x",
                    "speed": -0.05,
                    "reference_frame": "j2n6s300_link_base"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "rx",
                    "speed": -0.3,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "LeftHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "y",
                    "speed": 0.03,
                    "reference_frame": "j2n6s300_link_base"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "ry",
                    "speed": 0.3,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "RightHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "y",
                    "speed": -0.03,
                    "reference_frame": "j2n6s300_link_base"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "ry",
                    "speed": -0.3,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "CloserHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "z",
                    "speed": -0.03,
                    "reference_frame": "j2n6s300_link_base"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "rz",
                    "speed": -0.3,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "FartherHybrid": {
                "translation": {
                    "action_type": "velocity",
                    "axis": "z",
                    "speed": 0.03,
                    "reference_frame": "j2n6s300_link_base"
                },
                "rotation": {
                    "action_type": "velocity",
                    "axis": "rz",
                    "speed": 0.3,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "SwitchRef1": {
                "translation": {
                    "action_type": "mode",
                    "mode_cmd": "rotation"
                },
                "rotation": {
                    "action_type": "mode",
                    "mode_cmd": "translation"
                }
            },
            "SwitchRef2": {
                "translation": {
                    "action_type": "mode",
                    "mode_cmd": "rotation"
                },
                "rotation": {
                    "action_type": "mode",
                    "mode_cmd": "translation"
                }
            },
            # Mode-independent buttons (always use velocity, continuous)
            "S1X_+1": {
                "*": {
                    "action_type": "velocity",
                    "axis": "x",
                    "speed": 0.05,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "S1X_-1": {
                "*": {
                    "action_type": "velocity",
                    "axis": "x",
                    "speed": -0.05,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "S1Y_+1": {
                "*": {
                    "action_type": "velocity",
                    "axis": "y",
                    "speed": 0.03,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "S1Y_-1": {
                "*": {
                    "action_type": "velocity",
                    "axis": "y",
                    "speed": -0.03,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "TR": {
                "*": {
                    "action_type": "velocity",
                    "axis": "z",
                    "speed": 0.03,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "TL": {
                "*": {
                    "action_type": "velocity",
                    "axis": "z",
                    "speed": -0.03,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            # Discrete rotation buttons (step-based, one-shot)
            "S1RotZ_+1": {
                "*": {
                    "action_type": "discrete",
                    "axis": "rz",
                    "step_deg": 30.0,
                    "reference_frame": "j2n6s300_link_base"
                }
            },
            "S1RotZ_-1": {
                "*": {
                    "action_type": "discrete",
                    "axis": "rz",
                    "step_deg": -30.0,
                    "reference_frame": "j2n6s300_link_base"
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

    def mode_callback(self, msg: String):
        """Handle mode change notifications."""
        self.current_mode = msg.data
        self.get_logger().info(f"CommandMapper: current_mode = {self.current_mode}")

    def get_action_for_button(self, button_id: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Look up action parameters for a button in the current mode.
        Supports wildcard "*" for mode-independent buttons.
        
        Args:
            button_id: Button identifier
            
        Returns:
            Tuple of (action_type, params) or (None, None) if not found
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

    def button_callback(self, msg: ButtonStatusMsg):
        """
        Process incoming button status messages.
        Updates all button states and triggers appropriate actions.
        
        Note: Active button can arrive empty, so we independently update
        and debounce all existing buttons each cycle.
        """

        button_id = msg.button_id if msg.button_id else None
        status = msg.button_status if msg.button_status is not None else self.BUTTON_INACTIVE
        now = self.get_clock().now().nanoseconds / 1e9
        
        # Update all button states (active button + auto-release others)
        edges = self.button_state_mgr.update_all_buttons(button_id, status, now)
        
        # Process edges for all buttons that changed
        for btn_id, edge in edges.items():
            self._process_button_edge(btn_id, edge, now)
        
        # Update continuous velocity commands based on currently held buttons
        self._update_velocity_commands()

    def _process_button_edge(self, button_id: str, edge: str, current_time: float):
        """
        Process a button edge event (rising, falling, hold).
        
        Args:
            button_id: Button identifier
            edge: Edge type ('rising', 'falling', 'hold')
            current_time: Current timestamp
        """
        action_type, params = self.get_action_for_button(button_id)
        
        if not action_type:
            return
        
        # Handle rising edge events (button press)
        if edge == 'rising':
            # self.get_logger().debug(f"[RISING_EDGE] Button {button_id}: action_type={action_type}")
            
            # Publish button press sound
            self.button_sound_pub.publish(Int32(data=1))
            
            # Trigger discrete actions
            if action_type == "discrete":
                self._publish_discrete_command(params)
            elif action_type == "system":
                self._publish_system_command(params)
            elif action_type == "mode":
                self._publish_mode_command(params)
        
        # Handle falling edge events (button release)
        elif edge == 'falling':
            # self.get_logger().info(f"[FALLING_EDGE] Button {button_id} released")
            self.button_sound_pub.publish(Int32(data=2))


    def _update_velocity_commands(self):
        """
        Update continuous velocity commands based on currently held buttons.
        Priority: last held velocity button wins.
        """
        held_buttons = self.button_state_mgr.get_all_held_buttons()
        
        # Find the last held velocity button
        velocity_button = None
        for button_id in held_buttons:
            action_type, params = self.get_action_for_button(button_id)
            if action_type == "velocity":
                velocity_button = button_id
                self.current_velocity_params = params
        
        # If no velocity buttons held, clear velocity
        if velocity_button is None:
            self.current_velocity_params = {}

    def _publish_velocity_tick(self):
        """
        Periodically publish velocity commands at 100 Hz.
        Called by timer callback.
        """
        twist = TwistStamped()
        twist.header.stamp = self.get_clock().now().to_msg()
        
        if self.current_velocity_params:
            params = self.current_velocity_params
            axis = params.get("axis", "x")
            speed = float(params.get("speed", 0.0))
            reference_frame = params.get("reference_frame", "j2n6s300_link_base")
            
            twist.header.frame_id = reference_frame
            
            # Initialize all velocities to zero
            twist.twist.linear.x = 0.0
            twist.twist.linear.y = 0.0
            twist.twist.linear.z = 0.0
            twist.twist.angular.x = 0.0
            twist.twist.angular.y = 0.0
            twist.twist.angular.z = 0.0
            
            # Set the appropriate axis
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
            twist.header.frame_id = "j2n6s300_link_base"
            twist.twist.linear.x = 0.0
            twist.twist.linear.y = 0.0
            twist.twist.linear.z = 0.0
            twist.twist.angular.x = 0.0
            twist.twist.angular.y = 0.0
            twist.twist.angular.z = 0.0
        
        self.vel_pub.publish(twist)

    def _publish_discrete_command(self, params: Dict):
        """
        Publish a discrete pose/rotation command.
        
        For rotations: sends a relative rotation as a quaternion.
        For translations: sends a relative position delta.
        
        Args:
            params: Action parameters containing axis, step size, and reference frame
        """
        axis = params.get("axis", "z")
        reference_frame = params.get("reference_frame", "j2n6s300_link_base")
        
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = reference_frame
        
        # Check if this is a rotation (rx, ry, rz) or translation (x, y, z)
        if axis.startswith("r"):
            # Discrete rotation
            step_deg = float(params.get("step_deg", 30.0))
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
            
            self.get_logger().info(
                f"Published discrete rotation: axis={axis} step_deg={step_deg} frame={reference_frame}"
            )
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
            
            self.get_logger().info(
                f"Published discrete translation: axis={axis} step_m={step_m} frame={reference_frame}"
            )
        
        self.pose_pub.publish(pose)

    def _publish_system_command(self, params: Dict):
        """
        Publish a system command.
        
        Args:
            params: Action parameters containing the system command
        """
        cmd = params.get("cmd", "noop")
        msg = String()
        msg.data = cmd
        self.sys_pub.publish(msg)
        self.get_logger().info(f"Published system command: {cmd}")

    def _publish_mode_command(self, params: Dict):
        """
        Publish a mode change request to ModeManager.
        
        Args:
            params: Action parameters containing the mode command
        """
        cmd = String()
        cmd.data = params["mode_cmd"]
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