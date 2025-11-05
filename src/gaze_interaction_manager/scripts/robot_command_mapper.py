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

        ### TODO: Simple inline mapping for testing. (Later: load from YAML)
        # Each entry maps button_id -> (action_type, action_params)
        # action_type in {"velocity","rotate_step","system","mode"}
        self.mapping = {
            "S1X_+1":   ("velocity", {"axis":"x", "speed": 0.05}),
            "S1X_-1":   ("velocity", {"axis":"x", "speed": -0.05}),
            "S1Y_+1":   ("velocity", {"axis":"y", "speed": 0.03}),
            "S1Y_-1":   ("velocity", {"axis":"y", "speed": -0.03}),
            "TR":       ("velocity", {"axis":"z", "speed": 0.03}),
            "TL":       ("velocity", {"axis":"z", "speed": -0.03}),
            "S1RotZ_+1":("rotate_step", {"axis":"z", "step_deg": 30}),
            "S1RotZ_-1":("rotate_step", {"axis":"z", "step_deg": -30}),
            # "A":      ("system", {"cmd":"grab_toggle"}),
            # "B":      ("system", {"cmd":"grab_toggle"}),
            "S1Reset":  ("system", {"cmd":"reset_pose"}),
            "A":        ("mode", {"mode_cmd":"toggle_next"}),
            "B":        ("mode", {"mode_cmd":"toggle_next"}),
            # add more test mappings as needed
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

    def button_callback(self, msg):
        button_id = msg.button_id
        status = msg.button_status
        now = self.get_clock().now().nanoseconds / 1e9
        
        self.get_logger().info(f"[RECV] Button '{button_id}', status={status}")
        
        if status is None or button_id is None:
            self.get_logger().warn("Received button msg without expected fields.")
            return
        
        # Empty button_id means all buttons are released
        if button_id == "":
            self.get_logger().info(f"[RELEASE_ALL] All buttons released at {now}")
            self.held_velocity_buttons.clear()
            self.current_velocity_params = {}
            return
        
        if button_id not in self.mapping:
            self.get_logger().info(f"No mapping defined for {button_id}")
            return
        
        action_type, params = self.mapping[button_id]
        prev_status = self.last_button_state.get(button_id, 0)
        self.last_button_state[button_id] = status
        
        BUTTON_ACTIVE = getattr(msg, "BUTTON_ACTIVE", 1)
        
        # Only process active signals
        if status != BUTTON_ACTIVE:
            # Button released
            if action_type == "velocity":
                self.held_velocity_buttons.discard(button_id)
                if not self.held_velocity_buttons:
                    self.current_velocity_params = {}
            return
        
        # Button is now active
        if action_type == "velocity":
            # Track this velocity button as held
            self.held_velocity_buttons.add(button_id)
            self.current_velocity_params = params
            self.get_logger().info(f"[VELOCITY_HOLD] Button {button_id} held: {params}")
            return
        
        if action_type == "rotate_step":
            self.publish_rotate_step(params)
            return
        
        # Debounce logic: only trigger on NEW press (transition from inactive to active)
        if prev_status != BUTTON_ACTIVE:
            # This is a new press (prev was inactive, now active)
            last_trigger_time = self.last_trigger_time.get(button_id, 0)
            time_since_trigger = now - last_trigger_time
            
            self.get_logger().info(f"[NEW_PRESS] Button {button_id}: {time_since_trigger:.3f}s since last trigger")
            
            # Apply debounce only to new presses
            if time_since_trigger < self.debounce_time:
                return
            
            # Passed debounce - trigger the action
            self.last_trigger_time[button_id] = now
            self.get_logger().info(f"[ACTION] Triggering {action_type} for {button_id}")
            
            if action_type == "system":
                self.publish_system(params)
            elif action_type == "mode":
                self.publish_mode_command(params)
        else:
            # Button was already active, still active - ignore (hold)
            return

    def publish_velocity_tick(self):
        """Called periodically (50 Hz) to publish current velocity state."""
        if self.current_velocity_params:
            params = self.current_velocity_params
            axis = params.get("axis", "x")
            speed = float(params.get("speed", 0.0))
            
            twist = TwistStamped()
            twist.header.stamp = self.get_clock().now().to_msg()
            twist.header.frame_id = "base_link"
            # zero by default
            twist.twist.linear.x = 0.0
            twist.twist.linear.y = 0.0
            twist.twist.linear.z = 0.0
            twist.twist.angular.x = 0.0
            twist.twist.angular.y = 0.0
            twist.twist.angular.z = 0.0

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

            self.vel_pub.publish(twist)
        else:
            # Publish zero velocity if no buttons held
            twist = TwistStamped()
            twist.header.stamp = self.get_clock().now().to_msg()
            twist.header.frame_id = "base_link"
            twist.twist.linear.x = 0.0
            twist.twist.linear.y = 0.0
            twist.twist.linear.z = 0.0
            twist.twist.angular.x = 0.0
            twist.twist.angular.y = 0.0
            twist.twist.angular.z = 0.0
            self.vel_pub.publish(twist)

    def publish_rotate_step(self, params):
        # publish a PoseStamped containing a rotation delta (relative)
        axis = params.get("axis", "z")
        step = float(params.get("step_deg", 30.0))

        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = "base_link"
        # For discrete rotations we send the delta rotation encoded in orientation (quaternion).
        # Consumers should interpret PoseStamped as "apply this rotation (relative) to current pose".
        # Represent rotation as Euler (radians) in the quaternion.
        from scipy.spatial.transform import Rotation
        rads = math.radians(step)
        if axis == "x":
            r = Rotation.from_euler('x', rads, degrees=False)
        elif axis == "y":
            r = Rotation.from_euler('y', rads, degrees=False)
        else:
            r = Rotation.from_euler('z', rads, degrees=False)

        q = r.as_quat()  # x, y, z, w
        pose.pose.orientation.x = float(q[0])
        pose.pose.orientation.y = float(q[1])
        pose.pose.orientation.z = float(q[2])
        pose.pose.orientation.w = float(q[3])

        # position left zero — consumer applies rotation relative to current pose
        pose.pose.position.x = 0.0
        pose.pose.position.y = 0.0
        pose.pose.position.z = 0.0

        self.pose_pub.publish(pose)
        self.get_logger().info(f"Published rotate_step axis={axis} step_deg={step}")

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