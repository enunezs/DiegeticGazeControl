#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from diegetic_transform_engine.msg import MarkerArray as FiducialMarkerArray
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import Header
import random


class ArucoVisualizer(Node):
    def __init__(self):
        super().__init__("aruco_visualizer")

        # Subscribe to the marker topic
        self.subscription = self.create_subscription(
            FiducialMarkerArray,
            "aruco_markers",
            self.aruco_callback,
            10,
        )

        # Publisher for visualization markers
        self.vis_pub = self.create_publisher(MarkerArray, "aruco_markers_viz", 10)

        # Keep track of marker colors
        self.marker_colors = {}

        self.get_logger().info("Aruco Visualizer Node initialized")

    def aruco_callback(self, msg: FiducialMarkerArray):
        # self.get_logger().info("Received")
        marker_array_viz = MarkerArray()
        header = msg.header

        for fid_marker in msg.markers:
            marker_id = fid_marker.id

            # Assign a random shade of blue if we haven't seen this marker before
            if marker_id not in self.marker_colors:
                blue_shade = random.uniform(0.3, 1.0)  # avoid too dark
                self.marker_colors[marker_id] = (0.0, 0.0, blue_shade, 1.0)

            color = self.marker_colors[marker_id]

            vis_marker = Marker()
            vis_marker.header = header
            vis_marker.ns = "aruco_markers"
            vis_marker.id = marker_id
            vis_marker.type = Marker.CUBE
            vis_marker.action = Marker.ADD

            # Set the pose from the fiducial marker
            vis_marker.pose = fid_marker.pose

            # Set the scale: width and height = marker size, depth = 1mm
            size = getattr(fid_marker, "size", 0.044)  # default 44 mm
            vis_marker.scale.x = size
            vis_marker.scale.y = size
            vis_marker.scale.z = 0.001  # 1 mm thickness

            # Set the color
            vis_marker.color.r = color[0]
            vis_marker.color.g = color[1]
            vis_marker.color.b = color[2]
            vis_marker.color.a = color[3]

            marker_array_viz.markers.append(vis_marker)

        # Publish visualization markers
        # self.get_logger().info("Publishing")
        self.vis_pub.publish(marker_array_viz)


def main(args=None):
    rclpy.init(args=args)
    node = ArucoVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
