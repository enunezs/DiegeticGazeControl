#! /usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32  # Import message types as needed
from geometry_msgs.msg import PointStamped
from sensor_msgs.msg import Joy

from diegetic_button_pkg.msg import InputStatus
from diegetic_button_pkg.msg import InputStatusArray


# from fiducial_msgs.msg import FiducialTransformArray
# from button_msgs.msg import ButtonTransformArray

import csv
import os
from datetime import datetime

FREQUENCY = 50  # Frequency of recording in Hz
SUB_DIR = "recordings/test1"

# DIRECTORY = os.path.dirname(os.path.realpath(__file__))


class MultiTopicRecorder(Node):
    def __init__(self):
        super().__init__("multi_topic_recorder")
        self.get_logger().info("Recording node is Running...")

        # * Declare and retrieve parameters
        self.frequency = FREQUENCY
        self.topics = [
            "/diegetic/inputs",
            "/pupil_glasses/gaze_position",
            "/joy",
        ]  # ,"/joy"] , "/fiducial_transforms", "/button_transforms", "/diegetic/inputs"]

        # joy button names
        self.button_names = [
            "A",
            "B",
            "X",
            "Y",
            "LB",
            "RB",
            "LT",
            "RT",
            "BACK",
            "START",
            "LS",
            "RS",
            "UP",
            "DOWN",
            "LEFT",
            "RIGHT",
        ]
        self.button_status = ["RELEASED", "PRESSED", "HELD"]
        self.axis_names = ["LX", "LY", "RX", "RY", "LT", "RT", "DPAD_X", "DPAD_Y"]

        # /fiducial_transforms
        """self.subscriber = self.create_subscription(
            FiducialTransformArray, "/fiducial_transforms", self.callback, 10
        )
	    # /button_transforms
        self.subscriber = self.create_subscription(
            ButtonTransformArray, "/button_transforms", self.callback, 10
        )
	    # /joy
        self.subscriber = self.create_subscription(
            Joy, "/joy", self.callback, 10
        )
		"""

        # Initialize subfolders and csv files and writers
        os.makedirs(SUB_DIR, exist_ok=True)
        # Initialize subscribers and buffers
        self.buffers = {topic: [] for topic in self.topics}

        self.csv_files = {
            topic: open(
                SUB_DIR + "/" + f'{topic.replace("/", "_")}.csv', "w", newline=""
            )
            for topic in self.topics
        }

        self.csv_writers = {
            topic: csv.writer(file) for topic, file in self.csv_files.items()
        }

        # Write headers to the csv files
        for topic, file in self.csv_files.items():
            self.get_logger().info(f"Recording data for topic: {topic}")
            if topic == "/pupil_glasses/gaze_position":
                csv.writer(file).writerow(["timestamp", "x", "y", "z"])
                self.buffers["/pupil_glasses/gaze_position"].append(
                    ["timestamp", "x", "y", "z"]
                )
            if topic == "/diegetic/inputs":
                csv.writer(file).writerow(
                    ["timestamp", "input_id", "status", "button_status", "percent"]
                )
                self.buffers["/diegetic/inputs"].append(
                    ["timestamp", "input_id", "status", "button_status", "percent"]
                )
            if topic == "/joy":
                csv.writer(file).writerow(
                    ["timestamp"]
                    + [f"{axis}" for axis in self.axis_names]
                    + [f"{button}" for button in self.button_names]
                )
                self.buffers["/joy"].append(
                    ["timestamp"]
                    + [f"{axis}" for axis in self.axis_names]
                    + [f"{button}" for button in self.button_names]
                )

        ### Subscribe to the topics
        # /pupil_glasses/gaze_position
        self.subscriber = self.create_subscription(
            PointStamped,
            "/pupil_glasses/gaze_position",
            self.gaze_position_callback,
            10,
        )
        # /diegetic/inputs
        self.subscriber = self.create_subscription(
            InputStatusArray, "/diegetic/inputs", self.input_status_array_callback, 10
        )
        self.subscriber = self.create_subscription(Joy, "/joy", self.joy_callback, 10)

        # Timer to save buffered data
        self.timer = self.create_timer(1.0 / self.frequency, self.save_buffered_data)
        self.get_logger().info(f"Recording data to: {self.csv_writers}")

    def gaze_position_callback(self, msg):
        self.get_logger().info(
            f"Received gaze position: {msg.point.x}, {msg.point.y}, {msg.point.z}"
        )
        # Save the data to a buffer
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        data = [timestamp, msg.point.x, msg.point.y, msg.point.z]
        self.csv_writers["/pupil_glasses/gaze_position"].writerow(data)
        self.buffers["/pupil_glasses/gaze_position"].append(data)

    def input_status_array_callback(self, msg):
        self.get_logger().info(f"Received input status array: {msg}")
        # Save the data to a buffer
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        for input_status in msg.inputs:
            data = [
                timestamp,
                input_status.input_id,
                input_status.status,
                input_status.button_status,
                input_status.percent,
            ]
            self.csv_writers["/diegetic/inputs"].writerow(data)
            self.buffers["/diegetic/inputs"].append(data)
        if len(msg.inputs) == 0:
            data = [timestamp, 0, 0, 0, 0]
            self.csv_writers["/diegetic/inputs"].writerow(data)
            self.buffers["/diegetic/inputs"].append(data)

        ## If one of the buttons is pressed, print the button and timestamp into a new csv file
        for input_status in msg.inputs:
            if input_status.status == 1:
                with open(
                    SUB_DIR + "/" + "pressed_buttons.csv", "a", newline=""
                ) as pressed_buttons_file:
                    pressed_buttons_writer = csv.writer(pressed_buttons_file)
                    pressed_buttons_writer.writerow(
                        [
                            timestamp,
                            input_status.input_id,
                            input_status.percent,
                        ]  # , input_status.button_status]
                    )

    def joy_callback(self, msg):
        self.get_logger().info(f"Received joy: {msg}")
        # Save the data to a buffer
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        data = [timestamp] + list(msg.axes) + list(msg.buttons)
        self.csv_writers["/joy"].writerow(data)
        self.buffers["/joy"].append(data)

    def save_buffered_data(self):
        combined_data = []
        for topic, buffer in self.buffers.items():
            combined_data.extend(buffer)
            self.buffers[topic] = []

        if combined_data:
            with open(
                SUB_DIR + "/" + "combined_data.csv", "a", newline=""
            ) as combined_file:
                combined_writer = csv.writer(combined_file)
                for data in combined_data:
                    combined_writer.writerow(data)

    def __del__(self):
        for file in self.csv_files.values():
            file.close()


def main(args=None):
    rclpy.init(args=args)
    multi_recorder_publisher = MultiTopicRecorder()
    try:
        rclpy.spin(multi_recorder_publisher)
    except KeyboardInterrupt:
        multi_recorder_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
