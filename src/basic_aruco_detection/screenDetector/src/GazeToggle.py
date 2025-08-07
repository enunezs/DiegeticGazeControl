import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PointStamped
from std_msgs.msg import Float64MultiArray, Bool
from cv_bridge import CvBridge
import cv2
import numpy as np
from itertools import product
from datetime import datetime
from itertools import cycle

"""This class checks if a given gaze-point is within the screen bounds 
based on gaze position and transformation data."""

class GazeToggle(Node):
    """This node subscribes to gaze position and screen transformation data,
    and checks if the user is looking at the screen. If the user starts looking at the screen"""

    def __init__(self):
        super().__init__('screen_mouse')
        # Set up our ROS node.
        self.get_logger().info("Initialising screen mouse node...")
        self.declare_parameter('gaze_transformation', '/screen_transform')
        self.declare_parameter('gaze_position', '/pupil_glasses/gaze_position')

        self.transform_topic = self.get_parameter('gaze_transformation').value
        self.gaze_position_topic = self.get_parameter('gaze_position').value

        self.get_logger().info("Subscribing to transformation topic")
        # Set up subscriptions
        self.transform_subscription = self.create_subscription(
            Float64MultiArray,
            self.transform_topic,
            self.transform_callback,
            10
        )

        self.get_logger().info("Subscribing to gaze position topic")
        self.gaze_subscription = self.create_subscription(   
            PointStamped,  # Using PointStamped for gaze position with timestamp
            self.gaze_position_topic,
            self.gaze_callback,
            10
        )
        self.get_logger().info("Subscribing to screen corners topic")
        self.corner_position_subscription = self.create_subscription(
            Float64MultiArray,
            '/screen_corners',
            self.screen_corners_callback,
            10
        )
        self.get_logger().info("Subscribing to screen detected topic")
        self.screen_detected_subscriber = self.create_subscription(
            Bool,
            '/screen_detected',
            self.screen_detected_callback,
            10
        )

        # Set up publishers
        self.robot_frame_toggle_publisher = self.create_publisher(
            Bool,
            '/frame_toggle',
            10
        )

        self.time_since_last_toggle = 0

        self.screen_detections_buffer_size = 10
        self.screen_detections = np.zeros((self.screen_detections_buffer_size), dtype=bool)
        self.gaze_on_screen = np.zeros((self.screen_detections_buffer_size), dtype=bool)

        # Store the latest image and gaze position
        self.normalised_corner_points = np.array([
            [0.0, 0.0, 1.0],  # Top-left corner
            [1.0, 0.0, 1.0],  # Top-right corner
            [1.0, 1.0, 1.0],  # Bottom-right corner
            [0.0, 1.0, 1.0],  # Bottom-left corner
        ])

        self.latest_screen_corners = None
        self.latest_transformation = None
        self.latest_gaze_point = None
        self.current_frame = cycle(["Eye on screen", "Eye on Robot"])

    def transform_callback(self, msg: Float64MultiArray):
        """
        Callback for the transformation topic.
        """
        if len(msg.data) == 9:
            self.latest_transformation = np.array(msg.data).reshape(3, 3)
        else:
            self.get_logger().warn("Received invalid transformation data.")
    
    def gaze_callback(self, msg: PointStamped):
        """
        Callback for the gaze position topic.
        """
        self.latest_gaze_point = np.array([msg.point.x, msg.point.y, 1.0]) * [1600, 1200, 1.0]  # Assuming a screen resolution of 1600x1200

        is_gaze_on_screen = self.is_gaze_on_screen()
        print(f"user looking at screen: {is_gaze_on_screen}")
        self.send_toggle_message()

        # print(f"Gaze on screen: {is_gaze_on_screen}")
    
    def screen_detected_callback(self, msg: Bool):
        """
        Callback for the screen detected topic.
        """
        # Update the screen detections buffer
        self.screen_detections = np.roll(self.screen_detections, -1)
        self.screen_detections[-1] = msg.data

        # Check if the screen has been detected consistently

    def send_toggle_message(self):
        """A rolling buffer to detect wheter the users gaze has just looked at the screen."""
        on_screen = self.is_gaze_on_screen()
        self.gaze_on_screen = np.roll(self.gaze_on_screen, -1)
        self.gaze_on_screen[-1] = on_screen
        # print(f"Gaze on screen: {self.gaze_on_screen}")
        debounced_gaze_on_screen = np.all(self.gaze_on_screen[:-2]) != self.gaze_on_screen[-1]
        self.time_since_last_toggle += 1

        if debounced_gaze_on_screen > 1 and self.time_since_last_toggle > 5:
            self.gaze_on_screen[-1] = False # Doesnt process detections that are too close together.
            debounced_gaze_on_screen = False
            

        if debounced_gaze_on_screen and self.time_since_last_toggle > 5:
            print(f"Toggle message sent at {datetime.now()}")
            toggle_msg = Bool()
            self.time_since_last_toggle = 0
            
            if self.gaze_on_screen[-1]:
                self.get_logger().info("Gaze on screen detected, Switching to Eye in Hand frame.")
                self.robot_frame_toggle_publisher.publish(Bool(data=True))

            else:
                self.get_logger().info("Gaze on screen detected, Switching to Robot base frame.")
                self.robot_frame_toggle_publisher.publish(Bool(data=False))

        else:
            pass

    def screen_corners_callback(self, msg: Float64MultiArray):
        """
        Callback for the screen corners topic.
        """

        self.latest_screen_corners = np.array(msg.data).reshape((4, 2))
        # Convert corners to homogeneous coordinates

    def is_gaze_on_screen(self) -> bool:#
        """Checks if point is on screen using raycasting method implemented in OpenCV."""

        if self.latest_transformation is None or self.latest_screen_corners is None:
            return False
       
        point_in_polygon = cv2.pointPolygonTest(
            self.latest_screen_corners.astype(np.float32), 
            self.latest_gaze_point[:2].astype(np.float32), 
            True
        )

        print(f"Gaze distance from screen edges: {point_in_polygon}")
        
        if point_in_polygon >= 0 and np.mean(self.screen_detections) > 0.5:
            # print(f"Point {self.latest_gaze_point[:2]} is inside the screen polygon")
            return True
        else:
            return False
        
        # print(f"Point on  screen: {on_screen}")


def main(args=None):
    rclpy.init(args=args)
    
    screen_mouse = GazeToggle()
    
    try:
        rclpy.spin(screen_mouse)
    except KeyboardInterrupt:
        pass
    finally:
        screen_mouse.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()