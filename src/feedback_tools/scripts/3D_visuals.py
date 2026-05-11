#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from diegetic_transform_engine.msg import DiegeticButtonArray
from diegetic_transform_engine.msg import MarkerArray as FiducialMarkerArray
from gaze_interaction_manager.msg import ButtonStatusArray as ButtonStatusArray_msg
import random
import threading


class DiegeticAndArucoVisualizer(Node):
    """
    Combined visualizer for diegetic buttons (with status coloring)
    and ArUco fiducial markers (blue cubes) in RViz.

    Subscribes:
      - /diegetic_buttons_3d : DiegeticButtonArray
      - /dwell_time/input_status : ButtonStatusArray
      - /aruco_markers : diegetic_transform_engine/MarkerArray

    Publishes:
      - /diegetic_buttons_viz : visualization_msgs/MarkerArray
      - /aruco_markers_viz : visualization_msgs/MarkerArray
    """

    def __init__(self):
        super().__init__("diegetic_and_aruco_visualizer")

        # ---- Subscribers ----
        self.create_subscription(
            DiegeticButtonArray,
            "/diegetic_buttons_3d",
            self._buttons_3d_cb,
            10,
        )
        self.create_subscription(
            ButtonStatusArray_msg,
            "/dwell_time/input_status",
            self._button_status_cb,
            10,
        )
        self.create_subscription(
            FiducialMarkerArray,
            "/aruco_markers",
            self._aruco_cb,
            10,
        )

        # ---- Publishers ----
        self.buttons_pub = self.create_publisher(
            MarkerArray, "/visuals/diegetic_buttons", 10
        )
        self.aruco_pub = self.create_publisher(
            MarkerArray, "/visuals/aruco_markers", 10
        )

        # ---- Internal State ----
        self._status_lock = threading.Lock()
        self.button_statuses = {}
        self.previous_button_ids = set()
        self.random_colors = {}
        self.aruco_colors = {}

        # ---- State Colors ----
        self.state_colors = {
            "default": (1.0, 1.0, 0.0, 0.8),  # yellow
            "hover": (0.0, 1.0, 1.0, 0.9),  # cyan
            "active": (0.0, 1.0, 0.0, 0.9),  # green
            "pressed": (1.0, 0.0, 0.0, 0.95),  # red
            "disabled": (0.5, 0.5, 0.5, 0.5),  # gray
        }

        self.get_logger().info("Combined Diegetic & ArUco Visualizer started")

    # ---------------- ButtonStatus callback ----------------
    def _button_status_cb(self, msg: ButtonStatusArray_msg):
        with self._status_lock:
            self.button_statuses = {btn.button_id: btn for btn in msg.inputs}

    # ---------------- Diegetic Buttons callback ----------------
    def _buttons_3d_cb(self, msg: DiegeticButtonArray):
        marker_array = MarkerArray()
        current_ids = set()

        with self._status_lock:
            statuses_copy = dict(self.button_statuses)

        for button in msg.buttons:
            bid = button.button_id
            current_ids.add(bid)

            m = Marker()
            m.header.frame_id = "camera_optical_frame"
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = "diegetic_buttons"
            m.id = hash(bid) & 0x7FFFFFFF
            m.type = Marker.CUBE
            m.action = Marker.ADD

            # Pose
            m.pose.position.x = button.button_transform.translation.x
            m.pose.position.y = button.button_transform.translation.y
            m.pose.position.z = button.button_transform.translation.z
            m.pose.orientation = button.button_transform.rotation

            # Scale
            m.scale.x = abs(button.x1 - button.x0)
            m.scale.y = abs(button.y1 - button.y0)
            m.scale.z = 0.001

            # Color
            color = None
            status = statuses_copy.get(bid)
            if status is not None:
                try:
                    if status.button_status == status.BUTTON_ACTIVE:
                        color = self.state_colors["active"]
                    elif status.button_status == status.BUTTON_HOVER:
                        color = self.state_colors["hover"]
                    elif status.button_status == getattr(
                        status, "BUTTON_PRESSED", None
                    ):
                        color = self.state_colors["pressed"]
                    elif status.button_status == getattr(
                        status, "BUTTON_DISABLED", None
                    ):
                        color = self.state_colors["disabled"]
                    else:
                        color = self.state_colors["default"]
                        percent = getattr(status, "percent", None)
                        if percent is not None:
                            r, g, b, a = color
                            a = min(max(0.2 + 0.8 * float(percent), 0.2), 1.0)
                            color = (r, g, b, a)
                except Exception:
                    color = None

            if color is None:
                if bid not in self.random_colors:
                    self.random_colors[bid] = (
                        random.random(),
                        random.random(),
                        random.random(),
                        0.8,
                    )
                color = self.random_colors[bid]

            m.color.r, m.color.g, m.color.b, m.color.a = color

            try:
                m.lifetime = rclpy.duration.Duration(seconds=1.0).to_msg()
            except Exception:
                pass

            marker_array.markers.append(m)

        # Delete markers that disappeared
        for old in self.previous_button_ids - current_ids:
            dm = Marker()
            dm.header.frame_id = "camera_optical_frame"
            dm.header.stamp = self.get_clock().now().to_msg()
            dm.ns = "diegetic_buttons"
            dm.id = hash(old) & 0x7FFFFFFF
            dm.action = Marker.DELETE
            marker_array.markers.append(dm)

        self.buttons_pub.publish(marker_array)
        self.previous_button_ids = current_ids

    # ---------------- ArUco Markers callback ----------------
    def _aruco_cb(self, msg: FiducialMarkerArray):
        marker_array_viz = MarkerArray()

        for fid_marker in msg.markers:
            mid = fid_marker.id

            # Assign a random shade of blue if unseen
            if mid not in self.aruco_colors:
                blue_shade = random.uniform(0.3, 1.0)
                self.aruco_colors[mid] = (0.0, 0.0, blue_shade, 1.0)

            color = self.aruco_colors[mid]

            vis_marker = Marker()
            # Make new header with ros2 time to ensure RViz updates properly
            vis_marker.header.frame_id = "camera_optical_frame"
            vis_marker.header.stamp = self.get_clock().now().to_msg()

            vis_marker.ns = "aruco_markers"
            vis_marker.id = mid
            vis_marker.type = Marker.CUBE
            vis_marker.action = Marker.ADD

            vis_marker.pose = fid_marker.pose
            size = getattr(fid_marker, "size", 0.044)
            vis_marker.scale.x = size
            vis_marker.scale.y = size
            vis_marker.scale.z = 0.001

            (
                vis_marker.color.r,
                vis_marker.color.g,
                vis_marker.color.b,
                vis_marker.color.a,
            ) = color
            marker_array_viz.markers.append(vis_marker)

        self.aruco_pub.publish(marker_array_viz)

    # ---------------- Cleanup ----------------
    def destroy_node(self):
        cleanup = MarkerArray()
        for button_id in self.previous_button_ids:
            m = Marker()
            m.header.frame_id = "camera_optical_frame"
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = "diegetic_buttons"
            m.id = hash(button_id) & 0x7FFFFFFF
            m.action = Marker.DELETE
            cleanup.markers.append(m)

        if cleanup.markers:
            self.buttons_pub.publish(cleanup)
            self.get_logger().info("Cleaned up button markers on shutdown")

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DiegeticAndArucoVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
