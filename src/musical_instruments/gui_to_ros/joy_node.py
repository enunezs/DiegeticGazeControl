#! /usr/bin/env python3

# Base functions
import rclpy
from rclpy.node import Node
from cv2 import destroyAllWindows

# Import messages
from sensor_msgs.msg import Joy


# CONSTANTS
FREQUENCY = 50  # Hz


class ControllerPublisher(Node):

    # Init function
    def __init__(self):

        super().__init__("gui_input_to_joy_node")

        global FREQUENCY
        # Publishers
        self.publisher_joy = self.create_publisher(Joy, "joy", 1)

        # Dictionary for mapping inputs to axes
        self.axis_list = {
            "S1X": 0,
            "S1Y": 1,
            "TL": 2,
            "S2X": 3,
            "S2Y": 4,
            "TR": 5,
            "DX": 6,
            "DY": 7,
        }

        self.velocity_multipliers = {
            axis: 0.001 for axis in self.axis_list.keys()
        }  # Creates multipliers to control max speed of each joint.

        self.button = {
            "A": 0,
            "B": 1,
            "X": 2,
            "Y": 3,
            "LB": 4,
            "RB": 5,
            "Select": 6,
            "Start": 7,
            "Xbox": 8,
            "LJ": 9,
            "RJ": 10,
        }

        self.get_logger().info("Ready to publish joystick messages from GUI.")

    def callback(self, x_axis, y_axis):
        # Initialize message
        joy_msg = Joy()
        joy_msg.header.stamp = self.get_clock().now().to_msg()
        joy_msg.header.frame_id = "gui_joy"

        joy_msg.axes = [0.0] * 8
        joy_msg.buttons = [0] * 11

        # Put stuff in message
        # example
        velocity_multiplier = 1
        joy_msg.axes[0] = x_axis * velocity_multiplier  # Update X Axis
        joy_msg.axes[1] = y_axis * velocity_multiplier  # Update Y Axis

        # Publish

        self.get_logger().info("Sending message")
        self.publisher_joy.publish(joy_msg)
        print(joy_msg.axes)

        return


def main():
    rclpy.init()  # Initialize ROS DDS
    controller_publisher = ControllerPublisher()  # Create instance of function

    print("Jack Joy Publisher Node is Running...")

    try:
        rclpy.spin(controller_publisher)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        destroyAllWindows()
        controller_publisher.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == "__main__":
    main()


"""
header:
stamp:
    sec: 1665419855
    nanosec: 220658939
frame_id: joy
axes:
- -0.0  L X (Left pos)
- -0.007923568598926067 L Y
- 1.0 L Trigger
- -0.020677093416452408 R X
- -0.037381961941719055 R Y
- 1.0 R T
- 0.0 Dpad X
- 0.0 Dpad Y
buttons:
- 0 A
- 0 B
- 0 X
- 0 Y
- 0 LB
- 0 RB
- 0 Select
- 0 Start
- 0 Xbox
- 0 LP
- 0 RP
---

"""

"""Python msg structure:
{
    msgs: List[float], 
    buttons: List[int]
}
"""
