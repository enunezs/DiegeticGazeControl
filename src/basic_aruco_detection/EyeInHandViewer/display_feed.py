
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import sys
import os

# Add the parent directory to Python path
screendetector_src_path = os.path.join(os.path.dirname(__file__), '..', 'screenDetector', 'src')
sys.path.append(screendetector_src_path)

from screenDetector.src.createAruco import create_aruco_border_tags, add_aruco_tag_to_image
from screenDetector.src.ConfigHelperFunctions import load_aruco_config, load_detector_config

class ImageViewer(Node):
    def __init__(self, 
                 aruco_config_file='/root/ws/DiegeticGazeControl/src/basic Aruco Detection/screenDetector/src/aruco_codes.yaml'
                 ):

        super().__init__('image_viewer')
        aruco_params = load_aruco_config(aruco_config_file)
        # Parameters
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('window_name', 'Image Viewer')
        self.declare_parameter('display_fps', True)
        self.aruco_border_tags = create_aruco_border_tags(**aruco_params)
        image_topic = self.get_parameter('image_topic').value
        self.window_name = "Eye-in-hand view"
        self.display_fps = self.get_parameter('display_fps').value
        
        # Subscriber
        self.subscription = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            10
        )
        
        # OpenCV bridge
        self.bridge = CvBridge()
        
        # FPS calculation
        self.frame_count = 0
        self.start_time = self.get_clock().now()
        
        # Create OpenCV window
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        
        self.get_logger().info(f'Image viewer started, subscribing to: {image_topic}')
        self.get_logger().info('Press "q" in the image window to quit')

    def image_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # Calculate and display FPS if enabled
            cv_image = cv2.resize(cv_image, (640*2, 480*2), cv_image, interpolation=cv2.INTER_LINEAR)
            add_aruco_tag_to_image(cv_image, self.aruco_border_tags)
            
            # Display the image
            cv2.imshow(self.window_name, cv_image)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                self.get_logger().info('Quit key pressed, shutting down...')
                # Use a cleaner shutdown approach
                raise KeyboardInterrupt()
                
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')

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