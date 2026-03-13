#!/usr/bin/env python3
# command_mapper.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32, Float64MultiArray
from geometry_msgs.msg import TwistStamped, PoseStamped
from nav_msgs.msg import Path   
from builtin_interfaces.msg import Time
from rclpy.time import Time, Duration

from gaze_interaction_manager.msg import ButtonStatus as ButtonStatusMsg

import math
from typing import Dict, Optional, Tuple, Set, List
from scipy.spatial.transform import Rotation

import yaml
from ament_index_python.packages import get_package_share_directory
import os

from random import shuffle

PUBLISH_RATE_HZ = 100

# from geometry_msgs.msg import PoseArray


"""
Command mapping node:
- Subscribes to /dwell_time/active_button (ButtonStatus)
- Subscribes to /teleop/current_mode (String)
- Publishes:
    /teleop/cartesian_velocity -> TwistStamped (continuous)
    /teleop/waypoint_path      -> Path (waypoint list for discrete mode)
    /teleop/system             -> String (system commands)
    /teleop/mode_command       -> String (mode change requests)
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
        super().__init__('command_mapper_node')
        self.get_logger().info("CommandMapper starting...")
        
        # Current control mode
        self.current_mode = "translation"
        
        # Button state management
        self.button_state_mgr = ButtonStateManager(debounce_time=0.3)
        
        # Velocity tracking
        self.current_velocity_params: Dict = {}
        
        # Finger pose control
        self.finger_pub = self.create_publisher(Float64MultiArray, '/teleop/finger_velocity', 10)
        self.current_finger_params = {} # Tracks currently held finger buttons

        self._init_publishers()
        self._init_subscribers()
        
        # tODO: Load mode mappings (move to YAML config later)
        self._init_mode_mappings()
        
        # Timer to publish velocity continuously at 100 Hz
        self.vel_publish_timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._publish_velocity_tick)



    def _init_publishers(self):
        """Initialize all ROS publishers:
        - /teleop/cartesian_velocity -> TwistStamped (Velocity and frame of reference for movement)
        - /teleop/waypoint_path -> Path (Planned path for the robot to follow)
        - /teleop/system -> String (System status messages)
        - /teleop/mode_command -> String (Commands to change control modes)

        """
        self.vel_pub = self.create_publisher(TwistStamped, '/teleop/cartesian_velocity', 10)
        
        self.pose_pub = self.create_publisher(Path, '/teleop/waypoint_path', 10)
        
        self.sys_pub = self.create_publisher(String, '/teleop/system', 10)
        self.mode_cmd_pub = self.create_publisher(String, '/teleop/mode_command', 10)

        # Publisher for button sound events
        self.button_sound_pub = self.create_publisher(Int32, '/button_events', 10)

    def _init_subscribers(self):
        """Initialize all ROS subscribers:
        - /dwell_time/active_button -> ButtonStatus
        - /teleop/current_mode -> String
        """

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

        self.declare_parameter("parser_mappings_file", "CALIB_mode_config.inputs.yaml")
        filename = self.get_parameter("parser_mappings_file").value

        config_file = os.path.join(
            get_package_share_directory("gaze_interaction_manager"),
            "config",
            filename
        )

        if not os.path.exists(config_file):
            self.get_logger().error(f"Config file not found: {config_file}")
            raise FileNotFoundError(config_file)

        with open(config_file, 'r') as f:
            cfg = yaml.safe_load(f)

        # Load mode mappings
        self.mode_mappings = cfg.get("mode_mappings", {})

        # Add calibration waypoint demo
        calibration_route = self.calculate_calibration_route_EX()
        self.mode_mappings["Y"] = calibration_route

        self.get_logger().info(f"Loaded {len(self.mode_mappings)} mode sets from {filename}")
        # self.get_logger().info(f"Mode mappings: {self.mode_mappings}")
        
        # print by mode_mappings for debug
        for button_id, modes in self.mode_mappings.items():
            self.get_logger().debug(f"Button {button_id}: modes = {list(modes.keys())}")


    def calculate_calibration_route_EX(self) -> Dict[str, Dict]:
        """Define a waypoint demo route for calibration purposes.
        The route visits predefined positions in space with orientations
        adapted depending on x and z.
        """

        far_x = 0.68
        close_x = 0.32
        mid_x = (far_x + close_x) / 2.0

        away_y = -0.225
        proximal_y = 0.225
        mid_y = (away_y + proximal_y) / 2.0

        low_z = 0.32
        high_z = 0.62
        mid_z = (low_z + high_z) / 2.0

        time_per_waypoint = 10.0
        calibration_route = []


        # Function to compute pitch depending on x and z
        def pitch_for_position(x, z):
            # Define center
            # center_x = mid_x
            center_x = 0
            center_z = mid_z

            # Compute angle using atan2
            angle_rad = math.atan2(-(z - center_z), (x - center_x))  # radians
            angle_deg = math.degrees(angle_rad)                 # convert to degrees
            print(f"DEBUG: x={x:.2f}, z={z:.2f} => angle_deg={angle_deg:.2f}")
            # Map angle to desired pitch range
            pitch = -5 + angle_deg
            return pitch 

        # Function to define orientation
        def orientation(x, z):
            roll = -200  # keep constant
            pitch =  90 -pitch_for_position(x, z)
            # pitch = 90

            yaw = 170    # keep constant
            return {"roll": roll, "pitch": pitch, "yaw": yaw}


        # Generate waypoints for all combinations 3X3X3:
        for x in [far_x, mid_x, close_x]:
            for y in [away_y, mid_y, proximal_y]:
                for z in [low_z, mid_z, high_z]:

        # For testing, only 2X2X2:
        # for x in [far_x, close_x]:
        #     for y in [away_y, proximal_y]:
        #         for z in [low_z, high_z]:
                    rot = orientation(x, z)
                    calibration_route.append(
                        {"x": x, "y": y, "z": z,
                        "roll": rot["roll"], "pitch": rot["pitch"], "yaw": rot["yaw"],
                        "time": time_per_waypoint}
                    )
                    self.get_logger().debug(f"Added waypoint at x={x}, y={y}, z={z}, roll={rot['roll']}, pitch={rot['pitch']}")

        self.get_logger().info(f"Generated {len(calibration_route)} calibration waypoints.")

        # Shuffle the waypoints
        shuffle(calibration_route)
        self.get_logger().info(f"Shuffled calibration route waypoints.")

        # Wrap into dictionary format
        calibration_route_dict = {
            "*": {
                "action_type": "waypoint_demo",
                "reference_frame": "j2n6s300_link_base",
                "waypoints": calibration_route
            }
        }

        return calibration_route_dict

    def calculate_calibration_route(self) -> Dict[str, Dict]:
        """Define a waypoint demo route for calibration purposes.
        The route visits predefined positions in space.
        """

        far_x = 0.50
        close_x = 0.25
        mid_x = (far_x + close_x) / 2.0

        away_y = -0.20
        proximal_y = 0.20
        mid_y = (away_y + proximal_y) / 2.0

        low_z = 0.22
        high_z = 0.40
        mid_z = (low_z + high_z) / 2.0

        rotation =  {"roll": -180-20, "pitch": -5, "yaw": 180-10}
        time_per_waypoint = 10.0
        # We need to define a route for all possible permutations of the positions
        calibration_route = []

        # Generate waypoints for all combinations 2X2X2:
        # * x: far, mid, close
        # * y: away, mid, proximal
        # * z: low, mid, high
        # for x in [far_x, close_x]:
        #     for y in [away_y, proximal_y]:
        #         for z in [low_z, high_z]:
        
        for x in [far_x, mid_x, close_x]:
            for y in [away_y, mid_y, proximal_y]:
                for z in [low_z, mid_z, high_z]:
                    calibration_route.append(
                        {"x": x, "y": y, "z": z, "roll": rotation["roll"], "pitch": rotation["pitch"], "yaw": rotation["yaw"], "time": time_per_waypoint}
                    )
                    self.get_logger().debug(f"Added calibration waypoint at x={x}, y={y}, z={z}")
                    # break  # IGNORE --- only one waypoint per button for now
                # break  # IGNORE --- only one waypoint per button for now
            # break  # IGNORE --- only one waypoint per button for now
        self.get_logger().info(f"Generated {len(calibration_route)} calibration waypoints.")

        # # Generate waypoints for all combinations 3X3X3:
        # # * x: far, mid, close
        # # * y: away, mid, proximal
        # # * z: low, mid, high
        # for x in [far_x, mid_x, close_x]:
        #     for y in [away_y, mid_y, proximal_y]:
        #         for z in [low_z, mid_z, high_z]:+

        #             calibration_route[f"WaypointDemo_{x}_{y}_{z}"] = {
        #                 "action_type": "waypoint_demo",
        #                 "waypoints": [
        #                     {"x": x, "y": y, "z": z, "roll": rotation["roll"], "pitch": rotation["pitch"], "yaw": rotation["yaw"], "time": time_per_waypoint}
        #                 ],
        #                 "reference_frame": "j2n6s300_link_base"
        #             }
        
        # # Emanuel strategy
        # calibration_route = {
        #     "WaypointDemo": { 
        #         "*": {
        #             "action_type": "waypoint_demo",  # special handler
        #             "waypoints": [  # hardcoded demo for now
        #                 {"x": far_x, "y": away_y, "z": low_z, "roll": rotation["roll"], "pitch": rotation["pitch"], "yaw": rotation["yaw"], "time": time_per_waypoint},
        #                 {"x": far_x, "y": proximal_y, "z": low_z, "roll": rotation["roll"], "pitch": rotation["pitch"], "yaw": rotation["yaw"], "time": time_per_waypoint},
        #                 {"x": close_x, "y": away_y, "z": low_z, "roll": rotation["roll"], "pitch": rotation["pitch"], "yaw": rotation["yaw"], "time": time_per_waypoint},
        #                 {"x": close_x, "y": proximal_y, "z": low_z, "roll": rotation["roll"], "pitch": rotation["pitch"], "yaw": rotation["yaw"], "time": time_per_waypoint},
        #             ],
        #             "reference_frame": "j2n6s300_link_base"
        #         }
        #     }
        # }


        ### shuffle
        shuffled_waypoints = list(calibration_route)
        shuffle(shuffled_waypoints) # from random import shuffle
        calibration_route = shuffled_waypoints
        self.get_logger().info(f"Shuffled calibration route waypoints.")

        # Finish shapping
        calibration_route = {
            "*": {
                "action_type": "waypoint_demo",
                "reference_frame": "j2n6s300_link_base",
                "waypoints": [wp for wp in calibration_route]
            }
        }

        """
          Y: # WaypointDemo
        "*":
        action_type: waypoint_demo
        reference_frame: j2n6s300_link_base
        waypoints:
            - { x: 0.50,  y: 0.20,  z: 0.22, roll: -200, pitch: -5, yaw: 170, time: 5.0 }
            - { x: 0.50,  y:-0.20,  z: 0.22, roll: -200, pitch: -5, yaw: 170, time: 5.0 }
            - { x: 0.30,  y: 0.20,  z: 0.22, roll: -200, pitch: -5, yaw: 170, time: 5.0 }
            - { x: 0.30,  y:-0.20,  z: 0.22, roll: -200, pitch: -5, yaw: 170, time: 5.0 }

        """        

        return calibration_route

    def mode_callback(self, msg: String):
        """Handle mode change notifications:"""
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
        # self.get_logger().info(f"Received button status: button_id={msg.button_id}, button_status={msg.button_status}")
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
            self.get_logger().debug(f"[RISING_EDGE] Button {button_id}: action_type={action_type}")
            
            # Publish button press sound
            self.button_sound_pub.publish(Int32(data=1))
            
            # Trigger discrete actions
            if action_type == "discrete":
                self._publish_discrete_command(params)
            elif action_type == "system":
                self._publish_system_command(params)
            elif action_type == "mode":
                self._publish_mode_command(params)
            elif action_type == "waypoint_demo":
                self._publish_waypoint_list(params)
         
        # Handle falling edge events (button release)
        elif edge == 'falling':
            self.get_logger().debug(f"[FALLING_EDGE] Button {button_id} released")
            self.button_sound_pub.publish(Int32(data=2))

    def _update_velocity_commands(self):
        """
        Update continuous velocity commands based on currently held buttons.
        Priority: last held velocity button wins.
        """
        held_buttons = self.button_state_mgr.get_all_held_buttons()
        
        # 1. Handle Arm Velocity 
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
        
        # 2. Handle Finger Velocity
        finger_button = None
        for button_id in held_buttons:
            action_type, params = self.get_action_for_button(button_id)
            if action_type == "finger":
                finger_button = button_id
                self.current_finger_params = params
            
        if finger_button is None:
            self.current_finger_params = {}
        
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

        # NEW: Finger Publishing
        f_msg = Float64MultiArray()
        if self.current_finger_params:
            params = self.current_finger_params
            speed = float(params.get("speed", 0.0))
            # 'fingers' can be a list in YAML like [1, 2, 3]
            target_fingers = params.get("fingers", [1, 2, 3]) 
            
            vels = [0.0, 0.0, 0.0]
            for f_idx in target_fingers:
                if 1 <= f_idx <= 3:
                    vels[f_idx-1] = speed
            f_msg.data = vels
        else:
            f_msg.data = [0.0, 0.0, 0.0]
        
        self.finger_pub.publish(f_msg)

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
        # TODO: I dont like the mode_cmd naming convention,
        cmd.data = params["mode_cmd"]
        self.mode_cmd_pub.publish(cmd)
        self.get_logger().info(f"Published mode_command: {cmd.data}")

    def _publish_waypoint_list(self, params: Dict):
        """
        Converts waypoint list from button mapping into a nav_msgs/Path message.
        Each waypoint includes absolute position and orientation.
    
        Args:
            params: Action parameters containing waypoint list and reference frame
        """
        waypoints = params.get("waypoints", [])
        reference_frame = params.get("reference_frame", "j2n6s300_link_base")

        if not waypoints:
            self.get_logger().warn("No waypoints defined for waypoint_demo button")
            return

        # Create Path message
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = reference_frame
        

        target_time = self.get_clock().now().to_msg()
        target_time = Time.from_msg(target_time)

        # Convert each waypoint dict to PoseStamped
        for i, wp in enumerate(waypoints):
            pose_stamped = PoseStamped()

            # Rollout timing
            extra = wp.get("time", 5.0)   # default 5 seconds
            target_time += Duration(seconds=extra)
            pose_stamped.header.stamp = target_time.to_msg()

            # Reference frame
            pose_stamped.header.frame_id = reference_frame
            
            # Position (absolute coordinates in meters)
            pose_stamped.pose.position.x = wp.get("x", 0.0)
            pose_stamped.pose.position.y = wp.get("y", 0.0)
            pose_stamped.pose.position.z = wp.get("z", 0.0)
            
            # Orientation (convert from euler angles in degrees to quaternion)
            roll_deg = (wp.get("roll", 0.0))
            pitch_deg = (wp.get("pitch", 0.0))
            yaw_deg = (wp.get("yaw", 0.0))

            rot = Rotation.from_euler('xyz', [roll_deg, pitch_deg, yaw_deg], degrees=True)
            quat = rot.as_quat()  # x, y, z, w

            pose_stamped.pose.orientation.x = float(quat[0])
            pose_stamped.pose.orientation.y = float(quat[1])
            pose_stamped.pose.orientation.z = float(quat[2])
            pose_stamped.pose.orientation.w = float(quat[3])
            
            path_msg.poses.append(pose_stamped)
        
        # Publish path
        self.pose_pub.publish(path_msg)
        self.get_logger().info(
            f"Published waypoint path with {len(waypoints)} waypoints to /teleop/waypoint_path"
        )

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