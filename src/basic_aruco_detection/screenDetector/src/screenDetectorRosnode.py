import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_msgs.msg import Float64MultiArray, MultiArrayDimension, Bool

import cv2
import sys

sys.path.append(
    "DiegeticGazeControl/src/basic_aruco_detection/screenDetector/src"
)

from ConfigHelperFunctions import load_aruco_config, load_detector_config
from screenDetector import ScreenDetector

class RosImageProcessor(Node):
    """This node suscribes to a webcam feed, localises the screen, and returns 
    the transform from the image frame to the screen frame within the image."""
    def __init__(self, 
                 aruco_params_file='/root/ws/DiegeticGazeControl/src/basic_aruco_detection/screenDetector/src/aruco_codes.yaml',
                 detector_params_file='/root/ws/DiegeticGazeControl/src/basic_aruco_detection/screenDetector/src/detectorSettings.yaml'
                 ):

        super().__init__('image_viewer')
        # Parameters
        self.declare_parameter('image_topic', '/pupil_glasses/front_camera/image_color')
        self.declare_parameter('aruco_params_file', aruco_params_file)
        self.declare_parameter('detector_params_file', detector_params_file)
        image_topic = self.get_parameter('image_topic').value
        
        # Subscriber
        self.image_subscription = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            10
        )

        self.screen_corner_publisher = self.create_publisher(
            Float64MultiArray, 
            'screen_corners',
            10
        )

        self.transform_publisher = self.create_publisher(
            Float64MultiArray, 
            'screen_transform', 
            10
        )

        self.screen_detected_publisher = self.create_publisher(
            Bool, 
            'screen_detected', 
            10
        )

        self.gaze_on_screen_publisher = self.create_publisher(
            Bool,
            'gaze_on_screen',
            10
        )

        aruco_params = load_aruco_config(aruco_params_file)
        detector_params = load_detector_config(detector_params_file)
        
        # OpenCV bridge
        self.bridge = CvBridge()
        
        # Set up the screen detector
        aruco_detector = cv2.aruco.ArucoDetector(
            aruco_params['aruco_dict'], 
            detector_params
        )

        self.detector = ScreenDetector(aruco_params['monitor_size'],
                                 aruco_detector,
                                 aruco_params['corner_ids'],
                                 aruco_config=aruco_params
                                 )
        
        self.last_detection = None
        self.last_corner_detection = None
    
    def image_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            resized_frame = cv2.resize(cv_image, self.detector.frame_size)
            corners, ids, rejected = self.detector.detect_arucos(resized_frame)
            corner_detection_dict = self.detector.filter_aruco_detections(corners, ids, rejected)

            if len(corner_detection_dict) == 0:
                print("No aruco detected!")
                output_frame = resized_frame
                self.screen_detected_publisher.publish(Bool(data=False))
            # TODO: Replace this with an actual filter!    
            
            elif len(corner_detection_dict) < 4:
                if self.last_detection is not None:
                    for aruco_id, corners in corner_detection_dict.items():
                        self.last_detection[aruco_id] = corners

                    screen_corners = self.detector.get_screen_corners(self.last_detection)
                    transform = self.detector.get_normalisation_transform(screen_corners)
                    
                    self.publish_transform(transform)
                    if self.last_corner_detection is not None:
                        self.publish_screen_corners(self.last_corner_detection)
                    self.screen_detected_publisher.publish(Bool(data=True))
                                      
            else:
                print("All four corners detected!")
                self.last_corner_detection = self.detector.get_screen_corners(corner_detection_dict)
                self.last_detection = corner_detection_dict
                self.publish_screen_corners(self.last_corner_detection)

                transform = self.detector.get_normalisation_transform(self.last_corner_detection)   
                self.publish_transform(transform)
                self.screen_detected_publisher.publish(Bool(data=True))
        
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')

    def publish_transform(self, transform):
        """
        Publish a 3x3 perspective transform matrix
        
        Args:
            transform: 3x3 numpy array representing the perspective transform
        """
        msg = Float64MultiArray()
        
        # Flatten the 3x3 matrix to a 1D array for publishing
        msg.data = transform.flatten().tolist()
        
        # Optional: Add layout information to describe the matrix structure
        msg.layout.dim.append(MultiArrayDimension())
        msg.layout.dim[0].label = "rows"
        msg.layout.dim[0].size = 3
        msg.layout.dim[0].stride = 9
        
        msg.layout.dim.append(MultiArrayDimension())
        msg.layout.dim[1].label = "cols" 
        msg.layout.dim[1].size = 3
        msg.layout.dim[1].stride = 3
        
        msg.layout.data_offset = 0
        
        # Publish the transform
        self.transform_publisher.publish(msg)
    
    def publish_screen_corners(self, screen_corners):
        """
        Publish the screen corners as a Float64MultiArray message.
        
        Args:
            screen_corners: 4x2 numpy array of screen corner points
        """
        msg = Float64MultiArray()
        print(f"Publishing screen corners: {screen_corners}")
        msg.data = screen_corners.flatten().tolist()
        
        # Optional: Add layout information to describe the structure
        msg.layout.dim.append(MultiArrayDimension())
        msg.layout.dim[0].label = "corners"
        msg.layout.dim[0].size = 4
        msg.layout.dim[0].stride = 8
        
        msg.layout.dim.append(MultiArrayDimension())
        msg.layout.dim[1].label = "coordinates"
        msg.layout.dim[1].size = 2
        msg.layout.dim[1].stride = 2
        
        msg.layout.data_offset = 0
        
        # Publish the screen corners
        self.screen_corner_publisher.publish(msg)

    def destroy_node(self):
        # Clean up OpenCV windows
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    
    image_viewer = RosImageProcessor()
    
    try:
        rclpy.spin(image_viewer)
    except KeyboardInterrupt:
        pass
    finally:
        image_viewer.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

