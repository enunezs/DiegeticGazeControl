#! /usr/bin/env python3

"""
ros2 run diegetic_button_pkg input_check.py --ros-args --params-file config/params.yaml
"""

import rclpy
from rclpy.node import Node

# Messages
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from diegetic_button_pkg.msg import DiegeticButtonArray
from diegetic_button_pkg.msg import InputStatus
from diegetic_button_pkg.msg import InputStatusArray

from std_msgs.msg import Float32
from geometry_msgs.msg import PointStamped

# Maths
import tf_transformations as tf
import cv2
import numpy as np
import matplotlib.path as mpltPath  # For finding gaze and button overlap. Apparently very fast

# Aruco
from cv2 import drawFrameAxes
from cv2 import projectPoints
from cv2 import Rodrigues

# For handling inputs
from pynput import keyboard  # import Listener, Key
from sensor_msgs.msg import Joy

### * PARAMETERS * ###  Debug optionsrosbag_to_csv
# Input interaction parameters
# TODO: Expose these later
# Dwell time settings
cycle_duration_seconds = (
    0.30  # 3 seconds for complete transition #slope, we can split this later
)
active_threshold_percent = 0.40  # Close to 0 start quickly
inactive_threshold_percent = 0.60  # Close to 1 stop quickly


### Input modes
input_trigger_mode = "keyboard_trigger"
# input_trigger_mode = "sloppy"
# input_trigger_mode = "dwell_time"
# keyboard_trigger
# "Dwell Time"

from enum import Enum


class InputTriggerMode(Enum):
    DWELL_TIME = 0
    SLOPPY = 1
    KEYBOARD_TRIGGER = 2
    GAMEPAD_TRIGGER = 3


# "Keyboard Trigger"
button_ids = ["????"]  # How to point to button? # By moving it to a different node
# "Other triggers?"

### * DEBUG * ###  Debug options
publish_image = True
draw_on_fiducials = True
serial_com = False
send_serial = False


### TODO ###
# Add config files
# Fix multiple marker bug
# CLEAN
# Piano fix
# PID
# Separate keyboard processing onto its own node


class input_status:
    def __init__(self, id, status="inactive", percent=0.0):
        self.id = id  # UNIQUE id for button
        # Array with 4 corners from center [x0,y0,x1,y1]
        self.status = status  # string, can be active, inactive, hover
        self.percent = percent

    def __str__(self):
        print("Input ID: %s." % self.id)
        print("status {}.".format(self.status))
        print("percent {}.".format(self.percent))


# Node receives list of inputs and tobii glasses information, and performs the main trigger check
# Node publishes the list of debounced pressed buttons


class ProcessInputs(Node):
    def __init__(self):
        super().__init__("process_inputs_node")
        self.get_logger().info("Process Inputs Node is Running...")

        # Initialize vars
        self.buttons = []
        self.gaze_position = [0.5, 0.5]  # Default to center

        # Load camera intrinsics
        self.load_camera_intrinsics()  # ! Why?

        #  Open bridge for editting
        self.bridge = CvBridge()

        # Initialize core button status list
        self.button_status = []
        self.prev_time = self.get_clock().now()

        # Must be same resolution as camera
        self.frame = np.zeros([1200, 1600, 3], dtype=np.uint8)
        self.frame.fill(0)  # or img[:] = 255
        self.height, self.width = [1200, 1600]

        # TODO:
        # screen_res_x,screen_res_y = pyautogui.size()

        # TODO: Clunky!
        def on_press(key):
            self.key_pressed = True
            # self.get_logger().info('alphanumeric key {0} pressed'.format(key.char))

        def on_release(key):
            self.key_pressed = False

        # * Input parameter init
        if input_trigger_mode == "keyboard_trigger":
            cycle_duration_seconds = 0.05
            active_threshold_percent = 0.10  # percent
            inactive_threshold_percent = 0.90

            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
        self.key_pressed = False

        if input_trigger_mode == "gamepad_trigger":
            cycle_duration_seconds = 0.05
            active_threshold_percent = 0.10  # percent
            inactive_threshold_percent = 0.90
            self.subscriber_controller = self.create_subscription(
                Joy, "/joy", self.update_controller, 1
            )

        # Subscribers
        self.subscriber_eye_info = self.create_subscription(
            PointStamped, "pupil_glasses/gaze_position", self.update_gaze_pos, 1
        )
        self.subscriber_diegetic_buttons = self.create_subscription(
            DiegeticButtonArray, "/button_transforms", self.update_buttons, 1
        )

        # if draw_on_fiducials:
        self.subscriber_front_camera = self.create_subscription(
            Image, "/fiducial_images", self.update_frame, 1
        )

        # Publishers
        # Send modified image for debugging
        self.pub = self.create_publisher(Image, "/inputs_image", 10)

        self.publisher_input_array = self.create_publisher(
            InputStatusArray, "diegetic/inputs", 1
        )

        self.publisher_simple_output = self.create_publisher(
            Float32, "/simple_output", 1
        )

    # TODO: Add image to button list?

    def load_camera_intrinsics(self):
        self.get_logger().info("Loading camera intrinsics...")

        # Camera matrix
        camera_matrix_default = [
            887.79147665,
            0.0,
            809.32877594,
            0.0,
            887.14056667,
            614.39688332,
            0.0,
            0.0,
            1.0,
        ]
        self.declare_parameter("camera_matrix", camera_matrix_default)
        self.camera_matrix = np.array(
            self.get_parameter("camera_matrix").get_parameter_value().double_array_value
        ).reshape(3, 3)
        self.get_logger().info("Camera Matrix: \n %s" % self.camera_matrix)

        # Distortion coefficients
        dist_coeffs_default = [
            -1.28152845e-01,
            1.06973881e-01,
            -1.50877076e-05,
            -9.10823342e-04,
            2.62431778e-03,
            1.69108143e-01,
            5.02584562e-02,
            2.94127262e-02,
        ]

        self.declare_parameter("dist_coeffs", dist_coeffs_default)
        self.dist_coeffs = np.array(
            self.get_parameter("dist_coeffs").get_parameter_value().double_array_value
        )
        self.get_logger().info("Distortion Coefficients: \n %s" % self.dist_coeffs)

        self.get_logger().info("Camera intrinsics loaded")

    def update_controller(self, Joy_msg):
        a_button = Joy_msg.buttons[0]
        self.key_pressed = bool(a_button)
        # self.get_logger().info(f"From XBOX got {a_button}")

        pass

    # Buffers
    def update_gaze_pos(self, gaze_msg):
        # self.gaze_position = [float(x) for x in gaze_msg.data.split(",")]
        self.gaze_position = [gaze_msg.point.x, gaze_msg.point.y]
        # self.get_logger().info(f"Received gaze of {self.gaze_position}")

    def update_frame(self, img_msg):
        # Unpack message, get image
        img = self.bridge.imgmsg_to_cv2(img_msg)
        # self.get_logger().info("Camera image updated!")
        # img = self.bridge.compressed_imgmsg_to_cv2(img_msg)
        self.frame = img

    # Callback
    def update_buttons(self, DiegeticButtonArray_msg):
        self.buttons = DiegeticButtonArray_msg.buttons
        visible_buttons = self.buttons
        gaze_pos = self.gaze_position

        # self.get_logger().info(f"HUHH?? {visible_buttons} ")

        # start_time = self.get_clock().now()

        ### Intersection
        # Check for intersection between gaze and area for each button
        # Receive a list of the buttons that are currently "pressed"
        input_list = self.get_active_inputs(
            visible_buttons, gaze_pos, publish_image=True
        )
        # self.get_logger().info inputs
        # self.get_logger().info(f"Found {input_list} inputs")

        ### Combine current button list with prev timesteps
        # Receives an array of the active button's ids, uses it to update the master list of buttons as they appear
        # If button is in list, it is active. If input is not in the list, add it
        self.button_status = self.update_button_status(input_list, self.button_status)
        # self.get_logger().info(f"Updated to {input_list} inputs")

        ### Filtering
        delta_time = (self.get_clock().now() - self.prev_time).nanoseconds * 0.000000001
        self.prev_time = self.get_clock().now()
        self.button_status = self.filter_buttons(
            self.button_status,
            input_list,
            delta_time,
            input_trigger_mode=input_trigger_mode,
        )
        # self.get_logger().info(f"Filtered to {input_list} inputs")

        ### Pack and publish
        InputStatusArrayMsg = InputStatusArray()
        InputStatusArrayMsg.header.stamp = self.get_clock().now().to_msg()
        InputStatusArrayMsg.header.frame_id = "input_list"

        for button in self.button_status:
            InputStatusMsg = InputStatus()
            InputStatusMsg.input_id = button.id
            InputStatusMsg.status = button.status
            # InputStatusMsg.button_status =
            # self.get_logger().info(InputStatusMsg.input_id, InputStatusMsg.status)
            InputStatusMsg.percent = float(button.percent)

            InputStatusArrayMsg.inputs.append(InputStatusMsg)

            if send_serial:
                message = (
                    str(button.id)
                    + ","
                    + str(button.status)
                    + ","
                    + str(button.percent)
                )

                message = "a,b,0.9"

                encoded_message = bytes(message, "utf-8")

                # self.get_logger().info(f"Sending to arduino: {encoded_message}")
                # self.sendSerial.write(bytes(message, 'utf-8'))
                self.sendSerial.write((encoded_message))
                # self.get_logger().info("Sent")

                # time.sleep(0.05)
                data = self.sendSerial.readline()
                # self.get_logger().info(f"received {data}")

            # self.get_logger().info(f"Sending simple outputs {str(self.button_status)}")

            """
            SimpleOutputMsg = Float32MultiArray()
            SimpleOutputMsg.data = [float(button.id), float(button.percent)]
            self.publisher_simple_output.publish(SimpleOutputMsg)
            """
            SimpleOutputMsg = Float32()
            SimpleOutputMsg.data = float(button.percent)  # +float(button.id))
            self.publisher_simple_output.publish(SimpleOutputMsg)

            # TODO: Remove!
            # break
            pass

        # InputStatusArrayMsg.header.stamp = DiegeticButtonArray_msg.header.stamp

        # Publish
        # self.get_logger().info(f"Sending list of inputs {str(self.button_status)}")
        self.publisher_input_array.publish(InputStatusArrayMsg)
        # self.get_logger().info(InputStatusArrayMsg)

        # TODO: Check actual processing time

    # Updates the button list according to the input information, delta_time and mode
    # "sloppy"
    # "dwell_time"
    # keyboard_trigger
    # "Dwell Time"

    def get_active_inputs(self, visible_buttons, gaze_pos, publish_image=False):
        # Drawing stuff is all over the place, take out
        # TODO Reorganize
        if publish_image and self.frame is not None:
            # Get frame
            frame = self.frame.copy()
            self.height, self.width = frame.shape[:2]
            # self.get_logger().info(f"frame stuff {frame.shape[: 2]}")

            # Add eye markers
            draw_circle = True
            if draw_circle:
                frame = cv2.circle(
                    frame,
                    (int(gaze_pos[0] * self.width), int(gaze_pos[1] * self.height)),
                    5,
                    (0, 0, 255),
                    2,
                )

        input_list = []
        for button in visible_buttons:
            # Get data
            rot_mat = tf.quaternion_matrix(
                [
                    button.button_transform.rotation.x,
                    button.button_transform.rotation.y,
                    button.button_transform.rotation.z,
                    button.button_transform.rotation.w,
                ]
            )
            rvec, _ = Rodrigues(rot_mat[0:3, 0:3])
            tvec = np.float32(
                [
                    button.button_transform.translation.x,
                    button.button_transform.translation.y,
                    button.button_transform.translation.z,
                ]
            )
            """self.get_logger().info(
                f"Button  {button.button_id} at {str(np.around(tvec, decimals=5))}"
            )"""

            # Plot boundary
            # +  Check overlaps
            objectPoints = np.float32(
                [
                    [button.x0, button.y0, 0],
                    [button.x0, button.y1, 0],
                    [button.x1, button.y1, 0],
                    [button.x1, button.y0, 0],
                ]
            )
            img_points, _ = projectPoints(
                objectPoints,
                rvec,
                tvec,
                self.camera_matrix,
                self.dist_coeffs,
                rvec,
                tvec,
            )

            points = np.int32(np.squeeze(img_points, axis=1))
            path = mpltPath.Path(np.squeeze(img_points, axis=1))
            # self.get_logger().info(f"This is the path {path}")
            # height, width = frame.shape[: 2]
            inside = path.contains_points(
                [[gaze_pos[0] * self.width, gaze_pos[1] * self.height]]
            )

            # Add to list
            if inside:
                input_list.append(button.button_id)

            # Drawing
            if draw_on_fiducials and self.frame is not None:
                drawFrameAxes(
                    frame, self.camera_matrix, self.dist_coeffs, rvec, tvec, 0.05
                )

                # self.get_logger().info(f"This is the path {path}")
                # height, width = frame.shape[: 2]
                key_color = (0, 255, 0)

                if inside:
                    key_color = (255, 0, 0)

                cv2.polylines(
                    frame,
                    np.int32([np.squeeze(img_points, axis=1)]),
                    True,
                    key_color,
                    5,
                )

        # Publish image if set

        if publish_image and self.frame is not None:
            # Send image
            imgmsg = self.bridge.cv2_to_imgmsg(frame)
            imgmsg.header.stamp = self.get_clock().now().to_msg()
            imgmsg.header.frame_id = "buttons_visual_frame"

            # TODO: Call other stuff
            # self.button_pressed(input_list)

            # self.get_logger().info("Sending Image")
            self.pub.publish(imgmsg)  # Publish the message

        return input_list

    def update_button_status(self, input_list, button_status_a):
        button_status = button_status_a[:]

        if not input_list:
            return button_status

        for active_input in input_list:
            ids = [b.id for b in button_status]
            if active_input not in ids:
                # Create class and pack
                button = input_status(active_input, status="inactive", percent=0.0)
                # self.get_logger().info(f"creating button {active_input}")
                button_status.append(button)

        return button_status

    # TODO: Remove buttons from main list if they have a zero val
    def filter_buttons(
        self, button_status, input_list, delta_time, input_trigger_mode="dwell_time"
    ):
        if input_trigger_mode == "sloppy":
            for button in button_status:
                if button.id in input_list:
                    button.status = "active"
                else:
                    button.status = "inactive"

        if (
            input_trigger_mode == "keyboard_trigger"
            or input_trigger_mode == "gamepad_trigger"
        ):
            for button in button_status:
                if button.id in input_list:
                    if self.key_pressed:
                        # self.get_logger().info(f"Pressed  {button.id }!")
                        button.status = "active"
                    else:
                        button.status = "hover"
                else:
                    button.status = "inactive"

        for button in button_status:
            if button.id in input_list:
                # Dwell_time stuff
                # increment
                button.percent += delta_time / cycle_duration_seconds
                button.percent = min(button.percent, 1)

                if button.percent > active_threshold_percent:
                    """
                    if input_trigger_mode == "keyboard_trigger":
                        button.status = "hover"

                        if self.key_pressed:
                            # self.get_logger().info(f"Pressed  {button.id }!")
                            button.status = "active"
                    """
                    if input_trigger_mode == "dwell_time":
                        button.status = "active"
                    # TODO: Hover status

                # self.get_logger().info(f"Button {button.id} is at {100*button.percent:.2f}%, status {button.status}")

            else:
                # decrease
                button.percent -= delta_time / cycle_duration_seconds
                button.percent = max(button.percent, 0)

                if button.percent < inactive_threshold_percent:
                    button.status = "inactive"
                    # optional ish?
                    # self.input_list.remove(button)
        return button_status


def main():
    rclpy.init()  # Initialize ROS DDS

    publisher = ProcessInputs()  # Create instance of function

    print("Visual buttons Pub/Sub Node is Running...")

    try:
        rclpy.spin(publisher)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        publisher.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == "__main__":
    main()
