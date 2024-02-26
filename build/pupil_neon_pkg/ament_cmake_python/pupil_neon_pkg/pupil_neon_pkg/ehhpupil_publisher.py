#! /usr/bin/env python3

# GNU V3.0
# Copyright: Emanuel Nunez Sardinha
# URL:


# Pending
# Make sure it compiles!
# Benchmark -> test max refresh rate
# Development mode
# Camera calibration -> aruco?
# repo
# gif w video
# expose properties for customization -> good exercise

# * Core ROS dependencies
import rclpy
from rclpy.node import Node

# * Core time dependencies
import time
from datetime import datetime

# * Image messaging and conversion
from cv_bridge import CvBridge
import cv2
from cv2 import cvtColor  # TODO: specify particular modules of cv2
from cv2 import COLOR_BGR2RGB

# * Base messages
from sensor_msgs.msg import Image
from sensor_msgs.msg import CameraInfo
from geometry_msgs.msg import PointStamped

#from std_msgs.msg import String
#from builtin_interfaces.msg import Time as TimeMsg
# * Pupil
from pupil_labs.realtime_api.simple import discover_one_device
from pupil_labs.realtime_api.simple import Device

### Settings ###
## Video settings
# ! Confirm settings
# Sample resolutions
# video_resolution = (960, 540)       # (qHD)
# video_resolution = (720, 480)     # Not recommmeded
# video_resolution = (1280, 720)    # plain HD
# video_resolution = (1600, 900)
video_resolution = (1920,1080)    # (full HD) Default for low framerate
publish_freq = 100  # Hz Can be 33Hz, 100Hz or 200Hz
greyscale = False

### * DEBUG * ###
draw_circle = True
print_performance = False
camera_depth = 1.00 # z-axis  

class pupilPublisher(Node):

    def __init__(self):
        super().__init__("pupil_glasses_node")

        # * Intialize publishers
        """
        self.publisher_glasses = self.create_publisher(
            PupilGlassesMsg, "pupil_glasses", 1
        )
        """

        self.publisher_front_camera = self.create_publisher(Image, "pupil_glasses/front_camera", 1 )
        #self.publisher_internal_camera = self.create_publisher(Image, "pupil_glasses/internal_camera", 1 )
        self.publisher_gaze_position = self.create_publisher(PointStamped, "pupil_glasses/gaze_position", 1 ) # ! Change to point
        self.publisher_camera_info = self.create_publisher(CameraInfo, "pupil_glasses/front_camera/camera_info", 1 )

        # Connect to glasses
        print("Connecting to Pupil Glasses...")
        device = discover_one_device()

        ip = "192.168.1.110"
        port="8080"
        device = Device(address=ip, port=port)

        print(f"Phone IP address: {device.phone_ip}")
        print(f"Phone name: {device.phone_name}")
        print(f"Battery level: {device.battery_level_percent}%")
        print(f"Free storage: {device.memory_num_free_bytes / 1024**3:.1f} GB")
        print(f"Serial number of connected glasses: {device.module_serial}")

        self.device = device

        recording = False
        if recording:
            recording_id = device.recording_start()
            print(f"Started recording with id {recording_id}")

        self.bridge = CvBridge()

        self.timer = self.create_timer(1.0 / publish_freq, self.publish_pupil_data)


    def publish_pupil_data(self):

        device = self.device
        start_time = self.get_clock().now()
        
        ### Get the frame
        # ! WARNING: This is the blocking call -> Check frequency before switching to non-blocking
        matched_video_and_gaze = device.receive_matched_scene_video_frame_and_gaze()

        # matplotlib expects images to be in RGB rather than BGR.
        front_camera_frame = matched_video_and_gaze.frame.bgr_pixels
        gaze = matched_video_and_gaze.gaze

        ###  Adjust colour and resize image
        
        # frame = self.modify_image(frame, greyscale=greyscale)

        if draw_circle and gaze.worn:  # and tobii_glasses_msg.status == 0:
            front_camera_frame = self.draw_circle(front_camera_frame, (gaze.x, gaze.y))

        ###  Timestamps
        timestamp = matched_video_and_gaze.frame.timestamp_unix_seconds
        dt = datetime.fromtimestamp(timestamp)

        # * Pack image into message
        img_msg = self.bridge.cv2_to_imgmsg(front_camera_frame)
        img_msg.header.stamp = self.get_clock().now().to_msg()
        img_msg.header.frame_id = "pupil_glasses_frame"

        # * Pack gaze position into message
        gaze_msg = PointStamped()

        gaze_msg.point.x = gaze.x * 0.001
        gaze_msg.point.y = gaze.y * 0.001
        gaze_msg.point.z = camera_depth
        gaze_msg.header.stamp = self.get_clock().now().to_msg()
        gaze_msg.header.frame_id = "pupil_glasses_frame"
        
        # * Pack camera info into message
        camera_info_msg = CameraInfo()
        camera_info_msg.header.stamp = self.get_clock().now().to_msg()
        camera_info_msg.header.frame_id = "pupil_glasses_frame"
        camera_info_msg.height = video_resolution[1]
        camera_info_msg.width = video_resolution[0]
        camera_info_msg.distortion_model = "plumb_bob"
        #camera_info_msg.D = [0.0, 0.0, 0.0, 0.0, 0.0]
        #camera_info_msg.K = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0, 0, 1.0]
        #camera_info_msg.R = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0, 0, 1.0]
        #camera_info_msg.P = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, video_resolution[0]/2, video_resolution[1]/2, 1.0]
        camera_info_msg.binning_x = 4
        camera_info_msg.binning_y = 4
        

        # * Publish the message
        self.publisher_front_camera.publish(img_msg)
        self.publisher_gaze_position.publish(gaze_msg)
        self.publisher_camera_info.publish(camera_info_msg)

        # * Print performance
        if print_performance:
            print(
                f"Frame received at {dt.hour}:{dt.minute}:{dt.second}.{dt.microsecond} -> Published at {start_time.hour}:{start_time.minute}:{start_time.second}.{start_time.nanosecond}"
            )


# ----------------- #

    # Draw circle on image given gaze position
    def draw_circle(self, image, gaze_position):
        image_size = image.shape[:2][::-1]
        # Draw circle at gaze position
        cv2.circle(
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
    print("Pupil Neon Glasses Node is Running...")
    try:
        rclpy.spin(glasses_publisher)
    except KeyboardInterrupt:
        # cv2.destroyAllWindows()
        glasses_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
