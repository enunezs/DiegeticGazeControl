import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import PoseStamped, Point
from your_package.msg import (
    ArucoMarkerArray,
    ButtonArray,
)  # replace with your custom messages


class VisualizationNode(Node):
    def __init__(self):
        super().__init__("visualization_node")

        # Subscribers
        self.create_subscription(
            PoseStamped, "pupil_glasses/front_gaze", self.gaze_callback, 10
        )
        self.create_subscription(
            ArucoMarkerArray, "aruco_markers", self.aruco_callback, 10
        )
        self.create_subscription(
            ButtonArray, "button_positions", self.button_callback, 10
        )

        # Publisher
        self.marker_pub = self.create_publisher(MarkerArray, "rviz_markers", 10)

        # Stored data
        self.current_gaze = None
        self.current_aruco = []
        self.current_buttons = []

        # Timer to update markers
        self.create_timer(0.1, self.publish_markers)  # 10 Hz

    # ---------- Callbacks ----------
    def gaze_callback(self, msg: PoseStamped):
        self.current_gaze = msg

    def aruco_callback(self, msg: ArucoMarkerArray):
        self.current_aruco = msg.markers

    def button_callback(self, msg: ButtonArray):
        self.current_buttons = msg.buttons

    # ---------- Marker creation helpers ----------
    def create_square_marker(
        self, marker_id, position, frame_id="world", color=(0, 1, 0, 1), size=0.05
    ):
        marker = Marker()
        marker.header.frame_id = frame_id
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "squares"
        marker.id = marker_id
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose.position.x = position[0]
        marker.pose.position.y = position[1]
        marker.pose.position.z = position[2]
        marker.pose.orientation.w = 1.0
        marker.scale.x = size
        marker.scale.y = size
        marker.scale.z = size
        marker.color.r = color[0]
        marker.color.g = color[1]
        marker.color.b = color[2]
        marker.color.a = color[3]
        return marker

    def create_glasses_marker(self, pose, gaze_vector, frame_id="world"):
        markers = []

        # Glasses body
        glasses_marker = Marker()
        glasses_marker.header.frame_id = frame_id
        glasses_marker.header.stamp = self.get_clock().now().to_msg()
        glasses_marker.ns = "glasses"
        glasses_marker.id = 0
        glasses_marker.type = Marker.CUBE
        glasses_marker.action = Marker.ADD
        glasses_marker.pose = pose
        glasses_marker.scale.x = 0.05
        glasses_marker.scale.y = 0.02
        glasses_marker.scale.z = 0.02
        glasses_marker.color.r = 0.0
        glasses_marker.color.g = 0.0
        glasses_marker.color.b = 1.0
        glasses_marker.color.a = 1.0
        markers.append(glasses_marker)

        # Gaze arrow
        arrow_marker = Marker()
        arrow_marker.header.frame_id = frame_id
        arrow_marker.header.stamp = self.get_clock().now().to_msg()
        arrow_marker.ns = "gaze_arrow"
        arrow_marker.id = 1
        arrow_marker.type = Marker.ARROW
        arrow_marker.action = Marker.ADD

        start_point = pose.position
        end_point = Point()
        end_point.x = start_point.x + gaze_vector[0]
        end_point.y = start_point.y + gaze_vector[1]
        end_point.z = start_point.z + gaze_vector[2]
        arrow_marker.points = [start_point, end_point]

        arrow_marker.scale.x = 0.01  # shaft diameter
        arrow_marker.scale.y = 0.02  # head diameter
        arrow_marker.scale.z = 0.04  # head length
        arrow_marker.color.r = 1.0
        arrow_marker.color.g = 0.0
        arrow_marker.color.b = 0.0
        arrow_marker.color.a = 1.0
        markers.append(arrow_marker)

        return markers

    # ---------- Publish combined markers ----------
    def publish_markers(self):
        marker_array = MarkerArray()

        # Add ArUco markers
        for i, m in enumerate(self.current_aruco):
            pos = [m.pose.position.x, m.pose.position.y, m.pose.position.z]
            marker_array.markers.append(self.create_square_marker(i, pos))

        # Add buttons
        for i, b in enumerate(self.current_buttons):
            pos = [b.position.x, b.position.y, b.position.z]
            marker_array.markers.append(
                self.create_square_marker(100 + i, pos, color=(1, 0.5, 0, 1), size=0.03)
            )

        # Add glasses and gaze
        if self.current_gaze is not None:
            # Example: gaze_vector as forward in camera frame
            gaze_vector = [0, 0, 0.2]  # modify if you have real gaze vector
            marker_array.markers.extend(
                self.create_glasses_marker(self.current_gaze.pose, gaze_vector)
            )

        # Publish all
        self.marker_pub.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = VisualizationNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
