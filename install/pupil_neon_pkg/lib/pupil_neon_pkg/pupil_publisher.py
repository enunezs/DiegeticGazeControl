#! /usr/bin/env python3

# GNU V3.0
# Copyright: Emanuel Nunez Sardinha
# URL:

# To run:
"""
ros2 run pupil_neon_pkg pupil_publisher.py --ros-args --params-file src/pupil_neon_pkg/config/params.yaml
"""

# TODO
# Benchmark -> test max refresh rate
# change to wired connection (buy adaptor)

# * Core ROS dependencies
import rclpy
from rclpy.node import Node

# * Image messaging and conversion
from cv_bridge import CvBridge

# * Core time dependencies
from datetime import datetime

# * Image messaging and conversion
from cv_bridge import CvBridge
from cv2 import cvtColor, COLOR_BGR2RGB, destroyAllWindows
from cv2 import circle as cv2_circle

# * Base messages
from sensor_msgs.msg import Image
from sensor_msgs.msg import CameraInfo
from geometry_msgs.msg import PointStamped

# * Pupil
from pupil_labs.realtime_api.simple import discover_one_device
from pupil_labs.realtime_api.simple import Device

### Settings ###
# video_resolution = (1920,1080)    # Full HD
# video_resolution = (960, 540)       # (qHD)
# video_resolution = (720, 480)     # Not recommmeded
# video_resolution = (1280, 720)    # plain HD
# video_resolution = (1600, 900)


# Need to undistort here


class pupilPublisher(Node):
    def __init__(self):
        super().__init__("pupil_glasses_node")
        self.get_logger().info("Pupil Neon Glasses Node is Running...")

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
        # self.publisher_internal_camera = self.create_publisher(Image, "pupil_glasses/internal_camera", 1 )

        # Declare and retrieve parameters
        self.publish_freq = self.declare_and_get_parameter("publish_freq", 30)
        self.draw_circle = self.declare_and_get_parameter("draw_circle", False)
        self.camera_depth = self.declare_and_get_parameter("camera_depth", 1.0)
        self.video_resolution = self.declare_and_get_parameter(
            "video_resolution", (1600, 1200)
        )
        self.glasses_ip = self.declare_and_get_parameter("ip", "192.168.1.108")
        self.glasses_port = self.declare_and_get_parameter("port", "8080")
        self.print_performance = self.declare_and_get_parameter(
            "print_performance", False
        )

        # Connect to glasses
        self.get_logger().info("Connecting to Pupil Glasses...")
        self.get_logger().info(f"IP: {self.glasses_ip}")
        self.get_logger().info(f"Port: {self.glasses_port}")
        self.connect_to_glasses(ip=self.glasses_ip, port=self.glasses_port)

        self.timer = self.create_timer(1.0 / self.publish_freq, self.publish_pupil_data)

    def declare_and_get_parameter(self, name, default):
        self.declare_parameter(name, default)
        self.get_logger().info(
            f"Lodaded parameter {name}: {self.get_parameter(name).value}"
        )
        return self.get_parameter(name).value

    def connect_to_glasses(self, ip="192.168.1.108", port="8080"):
        # device = discover_one_device()
        device = Device(address=ip, port=port)

        self.get_logger().info(f"Phone IP address: {device.phone_ip}")
        self.get_logger().info(f"Phone name: {device.phone_name}")
        self.get_logger().info(f"Battery level: {device.battery_level_percent}%")
        self.get_logger().info(
            f"Free storage: {device.memory_num_free_bytes / 1024**3:.1f} GB"
        )
        self.get_logger().info(
            f"Serial number of connected glasses: {device.module_serial}"
        )

        calibration = device.get_calibration()
        self.get_logger().info(f"Camera Calibration Matrix: \n {calibration[0][2]}")
        self.get_logger().info(
            f"Camera Distortion Coefficients: \n {calibration[0][3]}"
        )

        # self.get_logger().info(calibration["scene_camera_matrix"][0])
        # self.get_logger().info(calibration["scene_distortion_coefficients"][0])

        self.device = device

        recording = False
        if recording:
            recording_id = device.recording_start()
            self.get_logger().info(f"Started recording with id {recording_id}")

        self.bridge = CvBridge()
        pass

    def publish_pupil_data(self):
        device = self.device
        start_time = self.get_clock().now()

        ### Get the frame
        # matched_video_and_gaze = device.receive_matched_scene_video_frame_and_gaze()
        front_camera_frame = device.receive_scene_video_frame()

        # matplotlib expects images to be in RGB rather than BGR.
        # front_camera_frame = matched_video_and_gaze.frame.bgr_pixels
        # gaze = matched_video_and_gaze.gaze
        gaze = device.receive_gaze_datum()

        if self.draw_circle and gaze.worn:  # and pupil_glasses_msg.status == 0:
            pass
            # front_camera_frame = self.draw_circle(front_camera_frame, (gaze.x, gaze.y))

        ###  Timestamps
        # timestamp = matched_video_and_gaze.frame.timestamp_unix_seconds
        timestamp = front_camera_frame.timestamp_unix_seconds

        dt = datetime.fromtimestamp(timestamp)

        # * Pack image into message
        img_msg = self.bridge.cv2_to_imgmsg(front_camera_frame.bgr_pixels, "bgr8")
        img_msg.header.stamp = self.get_clock().now().to_msg()
        img_msg.header.frame_id = "pupil_glasses_frame"

        # * Pack gaze position into message
        gaze_msg = PointStamped()

        gaze_msg.point.x = gaze.x / 1600
        gaze_msg.point.y = gaze.y / 1200
        gaze_msg.point.z = self.camera_depth
        gaze_msg.header.stamp = self.get_clock().now().to_msg()
        gaze_msg.header.frame_id = "pupil_glasses_frame"

        # * Pack camera info into message
        camera_info_msg = CameraInfo()
        camera_info_msg.header.stamp = self.get_clock().now().to_msg()
        camera_info_msg.header.frame_id = "pupil_glasses_frame"
        camera_info_msg.height = self.video_resolution[1]
        camera_info_msg.width = self.video_resolution[0]
        camera_info_msg.distortion_model = "plumb_bob"
        # camera_info_msg.D = [0.0, 0.0, 0.0, 0.0, 0.0]
        # camera_info_msg.K = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0, 0, 1.0]
        # camera_info_msg.R = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0, 0, 1.0]
        # camera_info_msg.P = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, video_resolution[0]/2, video_resolution[1]/2, 1.0]
        camera_info_msg.binning_x = 4
        camera_info_msg.binning_y = 4

        # * Publish the message
        self.publisher_front_camera.publish(img_msg)
        self.publisher_gaze_position.publish(gaze_msg)
        self.publisher_camera_info.publish(camera_info_msg)

        # * Print performance
        if self.print_performance:
            self.get_logger().info(
                f"Frame received at {dt.hour}:{dt.minute}:{dt.second}.{dt.microsecond} -> Published at {start_time.hour}:{start_time.minute}:{start_time.second}.{start_time.nanosecond}"
            )

    # ----------------- #

    # Draw circle on image given gaze position
    def draw_circle(self, image, gaze_position):
        image_size = image.shape[:2][::-1]
        # Draw circle at gaze position
        cv2_circle(
            image,
            (
                int(gaze_position[0]),
                int(gaze_position[1]),
            ),
            20,  # radius
            (0, 0, 255),  # BGR
            3,  # thickness
        )
        return image


def main(args=None):
    # Initialize ROS DDS
    rclpy.init(args=args)
    glasses_publisher = pupilPublisher()
    try:
        rclpy.spin(glasses_publisher)
    except KeyboardInterrupt:
        destroyAllWindows()
        glasses_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

# Pupil calibration parameters
"""
[[890.58737517   0.         843.03517309]
 [  0.         904.24555983 646.32207425]
 [  0.           0.           1.        ]]
[[-2.42124213e-01 -1.08320751e+00 -3.75766513e-03  8.55747541e-04
   4.68416642e+00]]
"""


"""

Calibration: 
[(1, b'821546', 

    [[887.79147665,   0.        , 809.32877594], 
    [  0.        , 887.14056667, 614.39688332], 
    [  0.        ,   0.        ,   1.        ]], 
    
    [-1.28152845e-01,  1.06973881e-01, -1.50877076e-05, 
    -9.10823342e-04,  2.62431778e-03,  1.69108143e-01,  
    5.02584562e-02,  2.94127262e-02], 

    [[1., 0., 0., 0.], 
    [0., 1., 0., 0.], 
    [0., 0., 1., 0.], 
    [0., 0., 0., 1.]], 


    
[[139.21307811,   0.        ,  98.34768529], 
[  0.        , 139.19281492,  95.7478684 ], 
[  0.        ,   0.        ,   1.        ]], 

[ 5.21496132e-02, -1.35983149e-01, 
 1.19676075e-03,  5.06738988e-04, 
 -6.13448783e-01, -4.67963347e-02,  
 4.09095931e-02, -6.96636544e-01], 

[[-0.83207315,  0.14689586,  0.53486061, 16.62257957], 
[ 0.05270876,  0.98087019, -0.18739128, 19.6763382 ], 
[-0.55215579, -0.12773143, -0.82389843, -6.62390137], 
[ 0.        ,  0.        ,  0.        ,  1.        ]], 



[[137.5413228 ,   0.        ,  95.06940499], 
[  0.        , 137.51291239,  93.00063722], 
[  0.        ,   0.        ,   1.        ]], 

[ 5.09164252e-02, -1.21666216e-01, 
-4.42373885e-04,  1.77331707e-04, 
-6.25567833e-01, -5.24739619e-02,  
1.46057213e-02, -6.59231378e-01], 

[[ -0.82623208,  -0.15142182,  -0.54259747, -16.69137573], 
[ -0.06029632,   0.9814347 ,  -0.18207213,  19.34751129], 
[  0.5600937 ,  -0.11771721,  -0.820023  ,  -7.13819885], 
[  0.        ,   0.        ,   0.        ,   1.        ]], 


2373075397)]



"""
