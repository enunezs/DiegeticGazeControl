#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import Header

# Import custom message types (adjust paths as needed)
# from diegetic_button_pkg.msg import DiegeticButtonArray
from diegetic_transform_engine.msg import DiegeticButtonArray, DiegeticButton2DArray


class DiegeticButtonVisualizer(Node):
    """
    ROS2 node that visualizes diegetic buttons as yellow cubes in RViz.

    Subscribes to:
    - /diegetic_buttons_3d (DiegeticButtonArray): 3D button transforms and dimensions

    Publishes:
    - /diegetic_buttons_viz (MarkerArray): Visualization markers for RViz
    """

    def __init__(self):
        super().__init__("diegetic_button_visualizer")

        # Subscribe to the button topic
        self.subscription = self.create_subscription(
            DiegeticButtonArray,
            "/diegetic_buttons_3d",
            self._button_callback,
            10,
        )

        # Publisher for visualization markers
        self.vis_pub = self.create_publisher(MarkerArray, "/diegetic_buttons_viz", 10)

        # Keep track of previously published markers for cleanup
        self.previous_marker_ids = set()

        self.get_logger().info("Diegetic Button Visualizer Node initialized")

    def _button_callback(self, msg: DiegeticButtonArray):
        """Callback to process button array and create visualization markers"""

        marker_array_viz = MarkerArray()
        current_marker_ids = set()

        for button in msg.buttons:
            button_id = button.button_id
            current_marker_ids.add(button_id)

            # Create visualization marker
            vis_marker = Marker()
            vis_marker.header = msg.header
            vis_marker.header.frame_id = "world"  # Use world frame for consistency
            vis_marker.ns = "diegetic_buttons"
            vis_marker.id = (
                hash(button_id) & 0x7FFFFFFF
            )  # Convert string to positive int
            vis_marker.type = Marker.CUBE
            vis_marker.action = Marker.ADD

            # Set the pose from the button transform
            vis_marker.pose.position.x = button.button_transform.translation.x
            vis_marker.pose.position.y = button.button_transform.translation.y
            vis_marker.pose.position.z = button.button_transform.translation.z
            vis_marker.pose.orientation.x = button.button_transform.rotation.x
            vis_marker.pose.orientation.y = button.button_transform.rotation.y
            vis_marker.pose.orientation.z = button.button_transform.rotation.z
            vis_marker.pose.orientation.w = button.button_transform.rotation.w

            # Set the scale based on button bounding box dimensions
            # Width and height from bounding box, depth = 1mm
            width = abs(button.x1 - button.x0)
            height = abs(button.y1 - button.y0)
            depth = 0.001  # 1 mm thickness

            vis_marker.scale.x = width
            vis_marker.scale.y = height
            vis_marker.scale.z = depth

            # Set yellow color
            vis_marker.color.r = 1.0  # Yellow
            vis_marker.color.g = 1.0  # Yellow
            vis_marker.color.b = 0.0  # Yellow
            vis_marker.color.a = 0.8  # Slightly transparent

            # Set marker lifetime (optional - markers persist until explicitly deleted)
            vis_marker.lifetime = rclpy.duration.Duration(seconds=1.0).to_msg()

            marker_array_viz.markers.append(vis_marker)

        # Add deletion markers for buttons that are no longer present
        markers_to_delete = self.previous_marker_ids - current_marker_ids
        for deleted_button_id in markers_to_delete:
            delete_marker = Marker()
            delete_marker.header = msg.header
            delete_marker.header.frame_id = "world"
            delete_marker.ns = "diegetic_buttons"
            delete_marker.id = hash(deleted_button_id) & 0x7FFFFFFF
            delete_marker.action = Marker.DELETE
            marker_array_viz.markers.append(delete_marker)

        # Update tracking set
        self.previous_marker_ids = current_marker_ids

        # Publish visualization markers
        self.vis_pub.publish(marker_array_viz)

    def destroy_node(self):
        """Clean up by deleting all markers when node shuts down"""
        # Send delete markers for cleanup
        cleanup_array = MarkerArray()
        for button_id in self.previous_marker_ids:
            delete_marker = Marker()
            delete_marker.header.frame_id = "world"
            delete_marker.ns = "diegetic_buttons"
            delete_marker.id = hash(button_id) & 0x7FFFFFFF
            delete_marker.action = Marker.DELETE
            cleanup_array.markers.append(delete_marker)

        if cleanup_array.markers:
            self.vis_pub.publish(cleanup_array)
            self.get_logger().info("Cleaned up visualization markers")

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DiegeticButtonVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
