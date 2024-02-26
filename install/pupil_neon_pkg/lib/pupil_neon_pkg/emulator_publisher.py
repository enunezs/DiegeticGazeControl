#! /usr/bin/env python3

# GNU V3.0
# Copyright: Emanuel Nunez Sardinha
# URL:

## TODO: Add buffer to keep stracting frames from webcam

# * Core ROS dependencies
import rclpy
from rclpy.node import Node  #

# * Image messaging and conversion
from cv_bridge import CvBridge
import cv2  # TODO: specify particular modules of cv2
import numpy as np

# * Mouse emulation
import pyautogui

# * Base messages
from sensor_msgs.msg import Image
from sensor_msgs.msg import CameraInfo
from geometry_msgs.msg import PointStamped

### Settings ###
## Video settings
video_resolution = (1920, 1080)  # (full HD) Default for low framerate
publish_freq = 100  # Hz Can be 33Hz, 100Hz or 200Hz
greyscale = False
camera_id = 0


### * DEBUG * ###
draw_circle = True
print_performance = False
camera_depth = 1.00  # z-axis

syncronize_data = False
greyscale = False
print_performance = False


class emulatorPublisher(Node):

    def __init__(self):

        # * Base node init
        super().__init__("glasses_emulator_node")
        self.frame_buffer = None
        global publish_freq

        # * Intialize publishers
        self.publisher_front_camera = self.create_publisher(
            Image, "pupil_glasses/front_camera", 1
        )
        self.publisher_gaze_position = self.create_publisher(
            PointStamped, "pupil_glasses/gaze_position", 1
        )
        self.publisher_camera_info = self.create_publisher(
            CameraInfo, "pupil_glasses/front_camera/camera_info", 1
        )

        self.declare_parameter("camera_id", 0)
        self.declare_parameter("publish_freq", 100)
        # self.declare_parameter( 'print_performance', False )
        self.declare_parameter("draw_circle", True)
        self.declare_parameter("camera_depth", 1.00)
        self.declare_parameter("video_resolution", (1920, 1080))

        global syncronize_data
        global publish_freq
        global greyscale
        global draw_circle
        global camera_depth
        global video_resolution

        camera_id = self.get_parameter("camera_id").get_parameter_value().integer_value
        publish_freq = (
            self.get_parameter("publish_freq").get_parameter_value().integer_value
        )
        # print_performance = self.get_parameter('print_performance').get_parameter_value().bool_value
        draw_circle = self.get_parameter("draw_circle").get_parameter_value().bool_value
        camera_depth = (
            self.get_parameter("camera_depth").get_parameter_value().double_value
        )
        video_resolution = tuple(
            self.get_parameter("video_resolution")
            .get_parameter_value()
            .integer_array_value
        )

        print(f"camera_id: {camera_id}")
        print(f"publish_freq: {publish_freq}")
        # print(f"print_performance: {print_performance}")
        print(f"draw_circle: {draw_circle}")
        print(f"camera_depth: {camera_depth}")
        print(f"video_resolution: {video_resolution}")

        # * Connect to webcam
        print("Emulating glasses")
        self.bridge = CvBridge()
        print("Connecting to webcam 0")
        self.cap = cv2.VideoCapture(camera_id)
        # publish_freq = 25
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # * Check if connection is succesful

        if self.cap == False:
            print("Error opening video stream")
        else:
            print("Video stream opened")

        # * markers
        # self.publisher_marker = self.create_publisher(MarkerArray, "pupil_glasses/visualization_marker", 2)
        # marker_pub = rospy.Publisher("/visualization_marker", Marker, queue_size = 2)

        # self.last_ts = 0
        # * Create publisher
        self.timer = self.create_timer(1.0 / publish_freq, self.publish_emulator_data)

        # * Init debug vars
        self.iterations = 0
        self.total_time = 0
        self.timings = []

        # self.pts_video_to_sensor_offset = 0
        self.stamps = []

    def publish_emulator_data(self):

        start_time = self.get_clock().now()

        # * Get latest data stream
        # Emulated: Webcam + Mouse
        gaze_coordinates = self.emulate_glasses()
        print(gaze_coordinates)

        # * Pack gaze position into message
        gaze_msg = PointStamped()
        gaze_msg.point.x, gaze_msg.point.y = gaze_coordinates
        gaze_msg.point.z = camera_depth
        gaze_msg.header.stamp = self.get_clock().now().to_msg()
        gaze_msg.header.frame_id = "pupil_glasses_frame"

        # * Get latest image frame
        ret, frame = self.cap.read()
        if ret:
            self.frame_buffer = frame
        else:
            if not self.frame_buffer:
                return
            frame = self.frame_buffer

        # * Adjust colour and resize image
        # frame = self.modify_image(frame, greyscale= greyscale , video_resolution = video_resolution)
        if draw_circle:
            # frame = self.draw_circle(frame, gaze_coordinates)
            pass
        # * Pack image into message
        img_msg = self.bridge.cv2_to_imgmsg(frame)
        img_msg.header.stamp = (
            self.get_clock().now().to_msg()
        )  # TODO: Change to glasses, align with pts?
        img_msg.header.frame_id = "pupil_glasses_frame"

        # * Pack camera info into message
        camera_info_msg = CameraInfo()
        camera_info_msg.header.stamp = self.get_clock().now().to_msg()
        camera_info_msg.header.frame_id = "pupil_glasses_frame"
        camera_info_msg.height = video_resolution[1]
        camera_info_msg.width = video_resolution[0]
        camera_info_msg.distortion_model = "plumb_bob"
        camera_info_msg.d = [
            0.10538655,
            -0.45207925,
            0.00821108,
            -0.01366533,
            0.5338796,
        ]
        camera_info_msg.k = [
            1.10354357e03,
            0.00000000e00,
            9.21639123e02,
            0.00000000e00,
            1.16283535e03,
            7.00397423e02,
            0.00000000e00,
            0.00000000e00,
            1.00000000e00,
        ]
        # camera_info_msg.P = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, video_resolution[0]/2, video_resolution[1]/2, 1.0]
        camera_info_msg.binning_x = 4
        camera_info_msg.binning_y = 4

        # * Publish the message
        self.publisher_front_camera.publish(img_msg)
        self.publisher_gaze_position.publish(gaze_msg)
        self.publisher_camera_info.publish(camera_info_msg)

        # * Calculate time difference between iterations and frame rate
        end_time = self.get_clock().now()

        if print_performance:
            self.print_performance_stats(start_time, end_time)

    # Get mouse coordinates as fimctopm of screen size
    def emulate_glasses(self):
        # Get screen size
        screen_res_x, screen_res_y = pyautogui.size()
        cursor_x, cursor_y = pyautogui.position()
        gaze_x, gaze_y = cursor_x / screen_res_x, cursor_y / screen_res_y
        # ros_time = self.get_clock().now().nanoseconds/1e9
        # ts = ros_time + 500000
        # pts = ros_time*0.09

        return (gaze_x, gaze_y)

    def print_performance_stats(self, start_time, end_time):
        self.iterations += 1
        self.total_time += (end_time - start_time).nanoseconds / 1000000000
        if self.iterations % 10 == 0:
            print(f"Average time per iteration: {self.total_time/self.iterations} s")
            self.iterations = 0
            self.total_time = 0

    # TODO: Pending, open parameters
    def modify_image(self, image, greyscale=False, video_resolution=(960, 540)):
        # Resize selected image to given dimension
        if greyscale:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        image = cv2.resize(image, video_resolution)

        # Convert to uint8
        image = image.astype(np.uint8)
        # Apply Gaussian blur to remove noise -> Best left for receiver?
        # image = cv2.GaussianBlur(image, (5, 5), 0)

        return image

    # Draw circle on image given gaze position
    def draw_circle(self, image, gaze_position):
        image_size = image.shape[:2][::-1]
        # Draw circle at gaze position
        cv2.circle(
            image,
            (
                int(gaze_position[0] * image_size[0]),
                int(gaze_position[1] * image_size[1]),
            ),
            10,
            (0, 255, 0),
            -1,
        )
        # Draw circle at center of image
        cv2.circle(
            image, (int(image_size[0] / 2), int(image_size[1] / 2)), 10, (0, 0, 255), -1
        )
        # Draw line from gaze position to center of image
        cv2.line(
            image,
            (
                int(gaze_position[0] * image_size[0]),
                int(gaze_position[1] * image_size[1]),
            ),
            (int(image_size[0] / 2), int(image_size[1] / 2)),
            (0, 0, 255),
            2,
        )
        return image


# * Core
def main(args=None):
    rclpy.init(args=args)  # Initialize ROS DDS
    glasses_emulator_publisher = emulatorPublisher()  # Create instance of function
    print("Glasses emulator publisher node is running...")

    try:
        rclpy.spin(glasses_emulator_publisher)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        glasses_emulator_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
