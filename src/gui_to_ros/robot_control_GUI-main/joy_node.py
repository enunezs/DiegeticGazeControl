#! /usr/bin/env python3

# Base functions
from abc import ABC, abstractmethod
from controller_publisher_base import ControllerPublisherBase
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
ros_import = True

class ControllerPublisher(ControllerPublisherBase, Node):
    # TODO: Add documentation

    """Sends messages out to ROS Node using a QTiemr. This allows us to send one message with updates from 
    multiple buttons at once.

    Also contains callback logic for each function called by a seperate object within PyQt interface.

    TODO: Find a nicer OOP way of creating a test node instead instead of this wild try/catch logic.<D-s>"""
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


class ControllerPublisher(ControllerPublisherBase, Node):
    # TODO: Add documentation

    """Sends messages out to ROS Node using a QTiemr. This allows us to send one message with updates from 
    multiple buttons at once.

    Also contains callback logic for each function called by a seperate object within PyQt interface.

    TODO: Find a nicer OOP way of creating a test node instead instead of this wild try/catch logic.<D-s>"""
    def __init__(self):
        
        super().__init__("gui_input_to_joy_node")
        
        global FREQUENCY
        # Publishers
        self.publisher_joy = self.create_publisher(Joy, "joy", 1)
        
        self.current_joy_msg = self.reset_joy_msg()
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

        # Set up a joy msg to be published


        self.get_logger().info("Ready to publish joystick messages from GUI.")
        

    def reset_joy_msg(self):
        """Creates a new Joy message to be filled by callback funcs then published."""
        
        current_joy_msg = Joy()
        
        current_joy_msg.header.stamp = self.get_clock().now().to_msg()
        current_joy_msg.header.frame_id = "gui_joy"
        
        current_joy_msg.axes = [0.0] * 8
        current_joy_msg.buttons = [0] * 11

        return current_joy_msg


    def button_translation_callback(self, direction):
        msg = self.current_joy_msg
        if direction == "forward":
            msg.axes[2] = 1.0
        elif direction == "backward":
            msg.axes[2] = -1.0


    def button_rotation_callback(self, direction):
        msg = self.current_joy_msg
        if direction == "clockwise":
            msg.axes[4] = 1000.0
        elif direction == "anticlockwise":
            msg.axes[4] = -1000.0
        else:
            print("Incorrect if statement selected!")


    def window_translation_callback(self, coordinates):
        msg = self.current_joy_msg
        msg.axes[0] = -coordinates[0]
        msg.axes[1] = -coordinates[1]


    def window_rotation_callback(self, coordinates):
        msg = self.current_joy_msg
        msg.axes[4] = coordinates[0] * 10
        msg.axes[3] = coordinates[1] * 10


    def timer_callback(self):
        """Publishes the current state of the joystick to the robot."""
        # Publish

        self.get_logger().info("Sending message")
        self.publisher_joy.publish(self.current_joy_msg)
        print(self.current_joy_msg.axes)

        #Reset message.
        self.current_joy_msg = self.reset_joy_msg()


    def change_frame(self):
        msg = self.current_joy_msg
        msg.buttons[7] = 1

    def gripper_callback(self, direction):
        msg = self.current_joy_msg
        if direction == "open":
            msg.buttons[0] = 1
        elif direction == "close":
            msg.buttons[1] = 1
        else:
            print("Incorrect if statement selected!")

    def send_message(self):
        self.get_logger().info("Sending message")
        self.publisher_joy.publish(self.current_joy_msg)
        print(self.current_joy_msg.axes)

        #Reset message.
        self.current_joy_msg = self.reset_joy_msg()

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


        self.current_joy_msg.header.stamp = self.get_clock().now().to_msg()
        self.current_joy_msg.header.frame_id = "gui_joy"
        self.current_joy_msg.axes = [0.0] * 8
        self.current_joy_msg.buttons = [0] * 11


        self.get_logger().info("Ready to publish joystick messages from GUI.")
        self.current_joy_msg = self.reset_joy_msg()

    def reset_joy_msg(self):
        """Creates a new Joy message to be filled by callback funcs then published."""
        joy_msg = Joy()
        joy_msg.header.stamp = self.get_clock().now().to_msg()
        joy_msg.header.frame_id = "gui_joy"
        
        joy_msg.axes = [0.0] * 8
        joy_msg.buttons = [0] * 11
        
        return joy_msg

    def button_translation_callback(self, direction):
        msg = self.current_joy_msg
        if direction == "forward":
            msg.axes[4] = 1.0
        elif direction == "backward":
            msg.axes[4] = -1.0

    def button_rotation_callback(self, direction):
        msg = self.current_joy_msg
        if direction == "clockwise":
            msg.axes[5] = 1.0
        elif direction == "anticlockwise":
            msg.axes[5] = -1.0
        else:
            print("Incorrect if statement selected!")


    def window_translation_callback(self, x_axis, y_axis):
        """Controls the translation of the robot in the X and Y directions in a continuous manner.
        
        Used within the VideoStreamWindow class in the GUI.
        """

        # Put stuff in message
        # example
        velocity_multiplier = 1
        self.current_joy_msg.axes[0] = x_axis * velocity_multiplier  # Update X Axis
        self.current_joy_msg.axes[1] = y_axis * velocity_multiplier  # Update Y Axis


    def window_rotation_callback(self, x_axis, y_axis):
        """Controls the translation of the robot in the X and Y directions in a continuous manner.
        
        Used within the VideoStreamWindow class in the GUI.
        """

        # Put stuff in message
        # example
        velocity_multiplier = 1
        self.current_joy_msg.axes[0] = x_axis * velocity_multiplier  # Update X Axis
        self.current_joy_msg.axes[1] = y_axis * velocity_multiplier  # Update Y Axis


    def timer_callback(self):
        """Publishes the current state of the joystick to the robot."""
        # Publish

        self.get_logger().info("Sending message")
        self.publisher_joy.publish(self.current_joy_msg)
        print(self.current_joy_msg.axes)

        #Reset message.
        self.current_joy_msg = self.reset_joy_msg()

    def change_frame(self):
        msg = self.current_joy_msg
        msg.buttons[7] = 1


    def send_message(self):
        self.get_logger().info("Sending message")
        self.publisher_joy.publish(self.current_joy_msg)
        print(self.current_joy_msg.axes)

        #Reset message.
        self.current_joy_msg = self.reset_joy_msg()

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
