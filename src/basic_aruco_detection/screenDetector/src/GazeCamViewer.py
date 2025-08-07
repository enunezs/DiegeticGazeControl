import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PointStamped
from std_msgs.msg import Float64MultiArray
from cv_bridge import CvBridge
import cv2
import numpy as np
from itertools import product


class ImageViewer(Node):
    def __init__(self):
        super().__init__('image_viewer')
        
        # Parameters
        self.declare_parameter('image_topic', '/pupil_glasses/front_camera/image_color')
        self.declare_parameter('window_name', 'Image Viewer')
        self.declare_parameter('gaze_position_topic', "/pupil_glasses/gaze_position")
        self.declare_parameter('display_fps', True)
        self.declare_parameter('screen_detected_topic', '/screen_detected')
        self.declare_parameter('transform_topic', '/screen_transform')
        self.declare_parameter('screen_corners_topic', '/screen_corners')

        self.image_topic = self.get_parameter('image_topic').value
        self.window_name = self.get_parameter('window_name').value
        self.display_fps = self.get_parameter('display_fps').value
        self.gaze_topic = self.get_parameter('gaze_position_topic').value
        self.transform_topic = self.get_parameter('transform_topic').value
        self.screen_corners_topic = self.get_parameter('screen_corners_topic').value
    
        self.normalised_corner_points = np.array([
            [0.0, 0.0, 1.0],  # Top-left corner
            [1.0, 0.0, 1.0],  # Top-right corner
            [1.0, 1.0, 1.0], # Bottom-right corner
            [0.0, 1.0, 1.0],  # Bottom-left corner
        ])  # Normalization points for gaze position

        # Image subscriber
        self.image_subscription = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10
        )

        # Gaze position subscriber
        self.gaze_subscription = self.create_subscription(
            PointStamped,  # Using PointStamped for gaze position with timestamp
            self.gaze_topic,
            self.gaze_callback,
            10
        )

        # Transform subscriber
        self.transform_subscription = self.create_subscription(
            Float64MultiArray,
            self.transform_topic,
            self.transform_callback,
            10
        )

        # Screen corners subscriber
        self.screen_corner_subscription = self.create_subscription(
            Float64MultiArray,  # Using Float64MultiArray for screen corners
            self.screen_corners_topic,
            self.screen_corners_callback,
            10
        )
        
        # OpenCV bridge
        self.bridge = CvBridge()
        
        # FPS calculation
        self.frame_count = 0
        self.start_time = self.get_clock().now()
        
        # Gaze position storage
        self.latest_gaze_x = None
        self.latest_gaze_y = None
        self.image_width = None
        self.image_height = None
        
        self.latest_gaze_on_screen = None
        
        # Gaze visualization parameters
        self.gaze_ring_radius = 10  # 20px diameter = 10px radius
        self.gaze_ring_color = (0, 0, 255)  # Red in BGR format
        self.gaze_ring_thickness = 2
        
        # Create OpenCV window
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        
        self.get_logger().info(f'Image viewer started, subscribing to: {self.image_topic}')
        self.get_logger().info(f'Gaze tracking enabled, subscribing to: {self.gaze_topic}')
        self.get_logger().info('Press "q" in the image window to quit')

    def gaze_callback(self, msg):
        """Callback to receive gaze position data"""
        try:
            # Store the latest gaze position (normalized coordinates [0,1])
            self.latest_gaze_x = msg.point.x
            self.latest_gaze_y = msg.point.y
            
            # Optional: Log gaze position for debugging
            # self.get_logger().info(f'Gaze position: ({msg.point.x:.3f}, {msg.point.y:.3f})')
            
        except Exception as e:
            self.get_logger().error(f'Error processing gaze position: {str(e)}')

    def image_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            self.draw_screen_edges_from_transform(cv_image)
            
            # Store image dimensions for gaze coordinate conversion
            self.image_height, self.image_width = cv_image.shape[:2]
            
            # Draw gaze position if available
            
            # Calculate and display FPS if enabled
        
            # Display gaze coordinates on screen for debugging
            if self.latest_gaze_x is not None and self.latest_gaze_y is not None:
                gaze_text = f'Gaze: ({self.latest_gaze_x:.3f}, {self.latest_gaze_y:.3f})'
                # cv2.putText(cv_image, gaze_text, (10, 60), 
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
            
            # Display the image
            self.draw_gaze_position(cv_image)

            cv2.imshow(self.window_name, cv_image)
            
            # Check for 'q' key press to quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.get_logger().info('Quit key pressed, shutting down...')
                rclpy.shutdown()
                
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')

    def transform_callback(self, msg):
        """Callback to receive screen transform data"""
        transform_matrix = np.array(msg.data).reshape((3, 3))
        self.latest_transform = transform_matrix
        
        if self.latest_gaze_x is not None and self.latest_gaze_y is not None:
            gaze_position = np.array([self.latest_gaze_x, self.latest_gaze_y, 1.0]) * [1600, 1200, 1]
            
            transformed_gaze = transform_matrix @ gaze_position
            scale_factor = transformed_gaze[2]
            transformed_gaze = transformed_gaze / scale_factor
            self.latest_gaze_on_screen = transformed_gaze[:2]
    
    def screen_corners_callback(self, msg):
        corners = np.array(msg.data).reshape((4, 2))
        self.last_corner_detection = corners # Store the last corner detection.
            
        
    def draw_screen_edges_from_transform(self, image):
        screen_transform = self.latest_transform if hasattr(self, 'latest_transform') else None
        
        if screen_transform is not None:
            # Convert the screen transform to a 2D array
            normalised_screen_to_image = np.linalg.inv(screen_transform) #This will map points back from the screen to the image
            # Convert normalized coordinates [0,1] to pixel coordinates
            screen_edges = self.normalised_corner_points @ normalised_screen_to_image.T

            # Draw the screen edges
            print(f"screen_edges:\n{screen_edges}\n")
            print(f"last_corner_detection:\n{self.last_corner_detection}\n")


            screen_edges = screen_edges[:, :2].astype(np.int32)  # Keep only x, y coordinates
            
            # Draw the reconstructed screen edges on the image
            cv2.polylines(
                image, 
                [screen_edges], 
                isClosed=True, 
                color=(0, 100, 255), 
                thickness=2)
        
            # Draw the last detected corners if available
            cv2.polylines(
                image, 
                [self.last_corner_detection.astype(np.int32)], 
                isClosed=True, 
                color=(0, 255, 100), 
                thickness=2)

        return image

    def draw_gaze_position(self, image):
        """Draw the gaze position as a red ring on the image"""
        if self.latest_gaze_x is not None and self.latest_gaze_y is not None:
            # Get image dimensions
            height, width = image.shape[:2]
            
            # Convert normalized coordinates [0,1] to pixel coordinates
            pixel_x = int(self.latest_gaze_x * width)
            pixel_y = int(self.latest_gaze_y * height)
            
            # Ensure coordinates are within image bounds
            pixel_x = max(0, min(pixel_x, width - 1))
            pixel_y = max(0, min(pixel_y, height - 1))
            
            # Draw the red ring
            cv2.circle(image, (pixel_x, pixel_y), self.gaze_ring_radius, 
                      self.gaze_ring_color, self.gaze_ring_thickness)
            
            # Optional: Draw a small center dot for better visibility
            cv2.circle(image, (pixel_x, pixel_y), 2, self.gaze_ring_color, -1)

            cv2.putText(image, f'image_shape: {image.shape}',
                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
  
    def destroy_node(self):
        # Clean up OpenCV windows
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    image_viewer = ImageViewer()
    
    try:
        rclpy.spin(image_viewer)
    except KeyboardInterrupt:
        pass
    finally:
        image_viewer.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()