#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from rclpy.time import Time, Duration
from scipy.spatial.transform import Rotation
import math

class WaypointManager(Node):
    def __init__(self):
        super().__init__('waypoint_manager')

        # 1. Configuration: Define waypoints here
        # Students can easily modify this list
        self.waypoint_sequence_tea_pickup = [
            { "x": 0.5, "y": 0.0,  "z": 0.47, "roll": -200, "pitch": 85, "yaw": 170, "time": 5.0},
            { "x": 0.6, "y": 0.2,  "z": 0.50, "roll": -200, "pitch": 85, "yaw": 170, "time": 3.0},
            { "x": 0.4, "y": -0.2, "z": 0.40, "roll": -200, "pitch": 85, "yaw": 170, "time": 4.0}
        ]
        
        
        self.reference_frame = "j2n6s300_link_base"

        # 2. Publishers and Subscribers
        self.path_pub = self.create_publisher(Path, '/teleop/waypoint_path', 10)
        self.mode_pub = self.create_publisher(String, '/teleop/mode_command', 10)
        
        # Trigger: When any string is received on this topic, the path is sent
        self.trigger_sub = self.create_subscription(String, '/waypoint_trigger', self.trigger_callback, 10)

        # 3. Startup: Request Discrete Mode
        # We use a timer to give ROS a second to connect publishers before sending
        self.create_timer(1.0, self.request_discrete_mode)
        
        self.get_logger().info("Waypoint Manager Ready. Send a message to /waypoint_trigger to start.")

    def request_discrete_mode(self):
        msg = String()
        msg.data = "discrete"
        self.mode_pub.publish(msg)
        self.get_logger().info("Requested 'discrete' control mode.")
        # We only need to do this once, so cancel the timer
        if hasattr(self, 'timer'): self.timer.cancel()

    def trigger_callback(self, msg):
        self.get_logger().info(f"Trigger received: {msg.data}. Sending waypoints...")
        self.send_waypoint_path()

    def send_waypoint_path(self):
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = self.reference_frame

        current_time_offset = self.get_clock().now()

        for wp in self.waypoint_sequence_tea_pickup:
            pose = PoseStamped()
            
            # Timing calculation
            current_time_offset += Duration(seconds=wp["time"])
            pose.header.stamp = current_time_offset.to_msg()
            pose.header.frame_id = self.reference_frame

            # Position
            pose.pose.position.x = float(wp["x"])
            pose.pose.position.y = float(wp["y"])
            pose.pose.position.z = float(wp["z"])

            # Orientation (Euler Degrees -> Quaternion)
            rot = Rotation.from_euler('xyz', [wp["roll"], wp["pitch"], wp["yaw"]], degrees=True)
            quat = rot.as_quat()
            pose.pose.orientation.x = quat[0]
            pose.pose.orientation.y = quat[1]
            pose.pose.orientation.z = quat[2]
            pose.pose.orientation.w = quat[3]

            # NOTE: Standard nav_msgs/Path does not have a 'gripper' field.
            # Usually, you would publish the gripper command to a separate topic 
            # or use a custom message. For this minimal version, we log it:
            # self.get_logger().info(f"Waypoint: x={wp['x']} Gripper={wp['gripper']}")

            path_msg.poses.append(pose)

        self.path_pub.publish(path_msg)
        self.get_logger().info(f"Published {len(self.waypoint_sequence_tea_pickup)} waypoints.")

def main(args=None):
    rclpy.init(args=args)
    node = WaypointManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()