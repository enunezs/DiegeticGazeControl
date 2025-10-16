#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from diegetic_transform_engine.msg import DiegeticButtonArray
from gaze_interaction_manager.msg import ButtonStatusArray as ButtonStatusArray_msg
import random
import threading


class DiegeticButtonVisualizer(Node):
    """
    Visualize diegetic buttons in RViz and update colours based on ButtonStatusArray.

    Subscribes:
      - /diegetic_buttons_3d : DiegeticButtonArray
      - /dwell_time/input_status : ButtonStatusArray (gaze_interaction_manager.msg)

    Publishes:
      - /diegetic_buttons_viz : visualization_msgs/MarkerArray
    """

    def __init__(self):
        super().__init__("diegetic_button_visualizer_with_status")

        # Subscribers
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

        # Publisher
        self.vis_pub = self.create_publisher(MarkerArray, "/diegetic_buttons_viz", 10)

        # Internal state
        self._status_lock = threading.Lock()
        # button_statuses: mapping button_id -> ButtonStatus (message type inside ButtonStatusArray)
        self.button_statuses = {}

        # Keep track of previously published button ids to delete removed ones
        self.previous_button_ids = set()

        # Per-button random colors fallback for unknown states (keeps consistent per-id)
        self.random_colors = {}

        # state -> (r,g,b,a)
        self.state_colors = {
            "default": (1.0, 1.0, 0.0, 0.8),   # yellow
            "hover": (0.0, 1.0, 1.0, 0.9),     # cyan-like for hover
            "active": (0.0, 1.0, 0.0, 0.9),    # green
            "pressed": (1.0, 0.0, 0.0, 0.95),  # red
            "disabled": (0.5, 0.5, 0.5, 0.5),  # gray
        }

        self.get_logger().info("DiegeticButtonVisualizerWithStatus started")

    # ----------------- ButtonStatusArray callback -----------------
    def _button_status_cb(self, msg: ButtonStatusArray_msg):
        """Update the internal map of button statuses (called whenever new status message arrives)."""
        with self._status_lock:
            # `msg.inputs` assumed to be a list of button status messages with fields:
            #   - button_id (string)
            #   - button_status (int enum)
            #   - percent (float 0..1)
            #   - button (DiegeticButton2D or similar) accessible for 2D visualization if needed
            self.button_statuses = {btn.button_id: btn for btn in msg.inputs}

    # ----------------- Diegetic buttons 3D callback -----------------
    def _buttons_3d_cb(self, msg: DiegeticButtonArray):
        """Receive 3D button geometry and publish coloured markers using latest statuses."""
        marker_array = MarkerArray()
        current_ids = set()

        # Work on a local copy of statuses for thread-safety
        with self._status_lock:
            statuses_copy = dict(self.button_statuses)

        for button in msg.buttons:
            bid = button.button_id
            current_ids.add(bid)

            m = Marker()
            m.header = msg.header
            m.header.frame_id = "world"
            m.ns = "diegetic_buttons"
            m.id = hash(bid) & 0x7FFFFFFF
            m.type = Marker.CUBE
            m.action = Marker.ADD

            # Pose
            m.pose.position.x = button.button_transform.translation.x
            m.pose.position.y = button.button_transform.translation.y
            m.pose.position.z = button.button_transform.translation.z
            # rotation
            m.pose.orientation = button.button_transform.rotation

            # Scale (width, height from bounding box; small thickness)
            m.scale.x = abs(button.x1 - button.x0)
            m.scale.y = abs(button.y1 - button.y0)
            m.scale.z = 0.001

            # Decide colour based on status if available
            color = None
            status = statuses_copy.get(bid)
            if status is not None:
                # We attempt to use the status.enum constants available on the status instance
                try:
                    # Example enums used in your Visualizer2D: BUTTON_ACTIVE, BUTTON_HOVER, etc.
                    if status.button_status == status.BUTTON_ACTIVE:
                        color = self.state_colors.get("active")
                    elif status.button_status == status.BUTTON_HOVER:
                        color = self.state_colors.get("hover")
                    elif status.button_status == getattr(status, "BUTTON_PRESSED", None):
                        # If a pressed enum exists
                        color = self.state_colors.get("pressed")
                    elif status.button_status == getattr(status, "BUTTON_DISABLED", None):
                        color = self.state_colors.get("disabled")
                    else:
                        # Other / unknown numeric status -> treat as default but use percent to modulate alpha
                        color = self.state_colors.get("default")
                        # If there's a percent field, slightly increase alpha when percent larger
                        percent = getattr(status, "percent", None)
                        if percent is not None:
                            r, g, b, a = color
                            # clamp alpha to [0.2, 1.0]
                            a = min(max(0.2 + 0.8 * float(percent), 0.2), 1.0)
                            color = (r, g, b, a)
                except Exception:
                    color = None

            # If no status info or something failed, fallback to a consistent random colour per button
            if color is None:
                if bid not in self.random_colors:
                    self.random_colors[bid] = (random.random(), random.random(), random.random(), 0.8)
                color = self.random_colors[bid]

            m.color.r, m.color.g, m.color.b, m.color.a = color

            # Short lifetime so RViz auto-removes if publisher dies (keeps markers reasonably fresh)
            try:
                m.lifetime = rclpy.duration.Duration(seconds=1.0).to_msg()
            except Exception:
                # if rclpy.duration isn't available / different API, ignore lifetime
                pass

            marker_array.markers.append(m)

        # Add delete markers for buttons that disappeared
        for old in self.previous_button_ids - current_ids:
            dm = Marker()
            dm.header.frame_id = "world"
            dm.ns = "diegetic_buttons"
            dm.id = hash(old) & 0x7FFFFFFF
            dm.action = Marker.DELETE
            marker_array.markers.append(dm)

        # Publish and update previous ids
        self.vis_pub.publish(marker_array)
        self.previous_button_ids = current_ids

    # ----------------- cleanup on shutdown -----------------
    def destroy_node(self):
        # publish deletes for any remaining markers
        cleanup = MarkerArray()
        for button_id in self.previous_button_ids:
            m = Marker()
            m.header.frame_id = "world"
            m.ns = "diegetic_buttons"
            m.id = hash(button_id) & 0x7FFFFFFF
            m.action = Marker.DELETE
            cleanup.markers.append(m)

        if cleanup.markers:
            self.vis_pub.publish(cleanup)
            self.get_logger().info("Cleaned up visualization markers on shutdown")

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
