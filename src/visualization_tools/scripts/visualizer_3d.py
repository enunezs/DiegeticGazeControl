#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from visualization_msgs.msg import Marker, MarkerArray
from pupil_neon_ros.msg import GazeData
from diegetic_transform_engine.msg import MarkerArray as FiducialMarkerArray
from diegetic_transform_engine.msg import DiegeticButtonArray
import random

class Visualizer3D(Node):
    def __init__(self):
        super().__init__("visualizer_3d")

        # Publishers
        self.gaze_vector_pub = self.create_publisher(Marker, "visuals/gaze_vector_marker", 50)
        self.eye_pub = self.create_publisher(MarkerArray, "visuals/eye_markers", 50)
        self.aruco_pub = self.create_publisher(MarkerArray, "aruco_markers_viz", 10)
        self.button_pub = self.create_publisher(MarkerArray, "/diegetic_buttons_viz", 10)

        # Subscriptions
        self.create_subscription(GazeData, "pupil_glasses/gaze_data", self.gaze_callback, 100)
        self.create_subscription(FiducialMarkerArray, "aruco_markers", self.aruco_callback, 10)
        self.create_subscription(DiegeticButtonArray, "/diegetic_buttons_3d", self.button_callback, 10)

        # State
        self.counter = 0
        self.marker_colors = {}
        self.previous_button_ids = set()

        self.get_logger().info("Visualizer3D Node started")

    # -------- GAZE ----------
    def gaze_callback(self, msg: GazeData):
        self.counter += 1
        if self.counter % 20 != 0:  # ~30Hz throttle if input ~600Hz
            return

        # Publish gaze vector
        self.gaze_vector_pub.publish(self.make_gaze_vector(msg))

        # Publish eyes + axes
        markers = MarkerArray()
        markers.markers.append(self.make_eye_marker(msg.left_eye, msg.header, 0, (0.0,0.0,1.0)))
        markers.markers.append(self.make_eye_marker(msg.right_eye, msg.header, 1, (1.0,0.0,0.0)))
        markers.markers.append(self.make_axis_marker(msg.left_eye, msg.header, 2, (0.0,1.0,1.0)))
        markers.markers.append(self.make_axis_marker(msg.right_eye, msg.header, 3, (1.0,0.0,1.0)))
        self.eye_pub.publish(markers)

    def make_gaze_vector(self, gaze_msg: GazeData, scale=0.1):
        marker = Marker()
        marker.header = gaze_msg.header
        marker.ns = "gaze_vector"
        marker.id = 11
        marker.type = Marker.ARROW
        marker.action = Marker.ADD
        marker.points = [Point(x=0.0,y=0.0,z=0.0),
                         Point(x=gaze_msg.x*scale, y=gaze_msg.y*scale, z=0.0)]
        marker.scale.x, marker.scale.y, marker.scale.z = (0.005, 0.01, 0.02)
        marker.color.g, marker.color.a = 1.0, 1.0
        return marker

    def make_eye_marker(self, eye, header, eye_id, color, scale=0.0242):
        marker = Marker()
        marker.header = header
        marker.ns = "eyes"
        marker.id = eye_id
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose.position.x = eye.eyeball_center_x / 1000
        marker.pose.position.y = eye.eyeball_center_y / 1000
        marker.pose.position.z = eye.eyeball_center_z / 1000
        marker.pose.orientation.w = 1.0
        marker.scale.x = marker.scale.y = marker.scale.z = scale
        marker.color.r, marker.color.g, marker.color.b = color
        marker.color.a = 1.0
        return marker

    def make_axis_marker(self, eye, header, eye_id, color, scale=1.0):
        marker = Marker()
        marker.header = header
        marker.ns = "eye_axes"
        marker.id = eye_id
        marker.type = Marker.ARROW
        marker.action = Marker.ADD
        start = Point(x=eye.eyeball_center_x/1000, y=eye.eyeball_center_y/1000, z=eye.eyeball_center_z/1000)
        end = Point(x=(eye.eyeball_center_x/1000 + eye.optical_axis_x)*scale,
                    y=(eye.eyeball_center_y/1000 + eye.optical_axis_y)*scale,
                    z=(eye.eyeball_center_z/1000 + eye.optical_axis_z)*scale)
        marker.points = [start, end]
        marker.scale.x = marker.scale.y = 0.01
        marker.color.r, marker.color.g, marker.color.b = color
        marker.color.a = 1.0
        return marker

    # -------- ARUCO ----------
    def aruco_callback(self, msg: FiducialMarkerArray):
        marker_array = MarkerArray()
        header = msg.header
        for fid in msg.markers:
            marker_id = fid.id
            if marker_id not in self.marker_colors:
                self.marker_colors[marker_id] = (0.0, 0.0, random.uniform(0.3,1.0), 1.0)
            color = self.marker_colors[marker_id]
            marker = Marker()
            marker.header = header
            marker.ns = "aruco_markers"
            marker.id = marker_id
            marker.type = Marker.CUBE
            marker.action = Marker.ADD
            marker.pose = fid.pose
            size = getattr(fid, "size", 0.044)
            marker.scale.x = marker.scale.y = size
            marker.scale.z = 0.001
            marker.color.r, marker.color.g, marker.color.b, marker.color.a = color
            marker_array.markers.append(marker)
        self.aruco_pub.publish(marker_array)

    # -------- BUTTONS ----------
    def button_callback(self, msg: DiegeticButtonArray):
        marker_array = MarkerArray()
        current_ids = set()
        for button in msg.buttons:
            bid = button.button_id
            current_ids.add(bid)
            marker = Marker()
            marker.header = msg.header
            marker.header.frame_id = "world"
            marker.ns = "diegetic_buttons"
            marker.id = hash(bid) & 0x7FFFFFFF
            marker.type = Marker.CUBE
            marker.action = Marker.ADD
            marker.pose.position.x = button.button_transform.translation.x
            marker.pose.position.y = button.button_transform.translation.y
            marker.pose.position.z = button.button_transform.translation.z
            marker.pose.orientation = button.button_transform.rotation
            marker.scale.x = abs(button.x1 - button.x0)
            marker.scale.y = abs(button.y1 - button.y0)
            marker.scale.z = 0.001
            marker.color.r, marker.color.g, marker.color.b, marker.color.a = (1.0,1.0,0.0,0.8)
            marker_array.markers.append(marker)

        # cleanup deleted buttons
        for old in self.previous_button_ids - current_ids:
            m = Marker()
            m.header.frame_id = "world"
            m.ns = "diegetic_buttons"
            m.id = hash(old) & 0x7FFFFFFF
            m.action = Marker.DELETE
            marker_array.markers.append(m)

        self.previous_button_ids = current_ids
        self.button_pub.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = Visualizer3D()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
