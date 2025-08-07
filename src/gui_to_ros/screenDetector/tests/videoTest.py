import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PointStamped
from cv_bridge import CvBridge
import cv2
import numpy as np
import sys
import os

# Add the src directory to path for custom imports
sys.path.append('../src')

from screenDetector import ScreenDetector, ArucoDetectionError
from ConfigHelperFunctions import load_aruco_config, load_detector_config


class GazeScreenDetectionViewer(Node):
    def __init__(self):
        super().__init__('gaze_screen_detection_viewer')
        
        # Parameters
        self.declare_parameter('image_topic', '/pupil_glasses/front_camera/image_color')
        self.declare_parameter('window_name', 'Gaze + Screen Detection Viewer')
        self.declare_parameter('gaze_position_topic', "/pupil_glasses/gaze_position")
        self.declare_parameter('display_fps', True)
        self.declare_parameter('aruco_config_path', "../src/aruco_codes.yaml")
        self.declare_parameter('detector_config_path', "../src/detectorSettings.yaml")
        self.declare_parameter('scaling_factor', 1.0)
        
        image_topic = self.get_parameter('image_topic').value
        self.window_name = self.get_parameter('window_name').value
        self.display_fps = self.get_parameter('display_fps').value
        gaze_topic = self.get_parameter('gaze_position_topic').value
        self.aruco_config_path = self.get_parameter('aruco_config_path').value
        self.detector_config_path = self.get_parameter('detector_config_path').value
        self.scaling_factor = self.get_parameter('scaling_factor').value
        
        # Image subscriber
        self.subscription = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            10
        )

        # Gaze position subscriber
        self.gaze_subscription = self.create_subscription(
            PointStamped,
            gaze_topic,
            self.gaze_callback,
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
        
        # Gaze visualization parameters
        self.gaze_ring_radius = 10  # 20px diameter = 10px radius
        self.gaze_ring_color = (0, 0, 255)  # Red in BGR format
        self.gaze_ring_thickness = 2
        
        # Screen detection initialization
        self.detector = None
        self.last_detection = None
        self.aruco_params = None
        self.detector_params = None
        
        # Initialize ArUco detection parameters
        self.initialize_screen_detection()
        
        # Create OpenCV window
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        
        self.get_logger().info(f'Gaze + Screen Detection Viewer started')
        self.get_logger().info(f'Image topic: {image_topic}')
        self.get_logger().info(f'Gaze topic: {gaze_topic}')
        self.get_logger().info('Press "q" in the image window to quit')

    def initialize_screen_detection(self):
        """Initialize ArUco detection parameters"""
        try:
            # Load ArUco and detector parameters
            self.aruco_params = load_aruco_config(self.aruco_config_path)
            self.detector_params = load_detector_config(self.detector_config_path)
            
            self.get_logger().info('Screen detection parameters loaded successfully')
            
        except Exception as e:
            self.get_logger().error(f'Failed to load screen detection config: {str(e)}')
            self.get_logger().error('Screen detection will be disabled')

    def setup_detector(self, frame_shape):
        """Setup the screen detector based on frame dimensions"""
        try:
            if self.aruco_params is None or self.detector_params is None:
                return False
                
            # Calculate image size with scaling factor
            image_size_x = frame_shape[1]
            image_size_y = frame_shape[0]
            image_size = [
                int(image_size_x / self.scaling_factor), 
                int(image_size_y / self.scaling_factor)
            ]
            
            # Create ArUco detector
            aruco_detector = cv2.aruco.ArucoDetector(
                self.aruco_params["aruco_dict"], 
                self.detector_params
            )

            # Create screen detector
            self.detector = ScreenDetector(
                image_size, 
                aruco_detector,
                self.aruco_params["corner_ids"],
                aruco_config=self.aruco_params
            )
            
            self.get_logger().info(f'Screen detector initialized for frame size: {image_size}')
            return True
            
        except Exception as e:
            self.get_logger().error(f'Failed to setup detector: {str(e)}')
            return False

    def detect_screen(self, frame):
        """Detect screen in the frame and return annotated frame"""
        try:
            if self.detector is None:
                return frame
                
            # Resize frame according to detector settings
            resized_frame = cv2.resize(frame, self.detector.frame_size)
            
            # Detect ArUco markers
            corners, ids, rejected = self.detector.detect_arucos(resized_frame)
            corner_detection_dict = self.detector.filter_aruco_detections(corners, ids, rejected)
            
            # Process detections
            if len(corner_detection_dict) == 0:
                # No ArUco markers detected
                output_frame = resized_frame
                
            elif len(corner_detection_dict) < 4:
                # Partial detection - use last known good detection if available
                output_frame = resized_frame.copy()
                output_frame = cv2.aruco.drawDetectedMarkers(output_frame, corners, ids)
                
                if self.last_detection is not None:
                    # Update last detection with new corners
                    for aruco_id, corner_coords in corner_detection_dict.items():
                        self.last_detection[aruco_id] = corner_coords
                    
                    # Draw screen using updated detection
                    screen_corners = self.detector.get_screen_corners(self.last_detection)
                    output_frame = self.detector.annotate_screen(output_frame, screen_corners)
                    
            else:
                # All four corners detected
                self.get_logger().info('All four screen corners detected!')
                screen_coords = self.detector.get_screen_corners(corner_detection_dict)
                self.last_detection = corner_detection_dict
                
                # Annotate the frame
                output_frame = self.detector.annotate_screen(resized_frame, screen_coords)
                output_frame = cv2.aruco.drawDetectedMarkers(output_frame, corners, ids)
            
            # Resize back to original frame size for consistent display
            if output_frame.shape[:2] != frame.shape[:2]:
                output_frame = cv2.resize(output_frame, (frame.shape[1], frame.shape[0]))
            cv2.putText(output_frame, f'Detected {len(corner_detection_dict)} markers',
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            return output_frame
            
        except Exception as e:
            self.get_logger().error(f'Error in screen detection: {str(e)}')
            return frame

    def gaze_callback(self, msg):
        """Callback to receive gaze position data"""
        try:
            # Store the latest gaze position (normalized coordinates [0,1])
            self.latest_gaze_x = msg.point.x
            self.latest_gaze_y = msg.point.y
            
        except Exception as e:
            self.get_logger().error(f'Error processing gaze position: {str(e)}')

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
            
            # Draw a small center dot for better visibility
            cv2.circle(image, (pixel_x, pixel_y), 2, self.gaze_ring_color, -1)


    def image_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # Setup detector on first frame
            if self.detector is None and self.aruco_params is not None:
                self.setup_detector(cv_image.shape)
            
            # Perform screen detection
            processed_image = self.detect_screen(cv_image)
            
            # Draw gaze position
            self.draw_gaze_position(processed_image)
            
            # Add information overlay
            self.add_info_overlay(processed_image)
            
            # Display the image
            cv2.imshow(self.window_name, processed_image)
            
            # Check for 'q' key press to quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.get_logger().info('Quit key pressed, shutting down...')
                rclpy.shutdown()
                
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')

    def destroy_node(self):
        # Clean up OpenCV windows
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    viewer = GazeScreenDetectionViewer()
    
    try:
        rclpy.spin(viewer)
    except KeyboardInterrupt:
        pass
    finally:
        viewer.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
