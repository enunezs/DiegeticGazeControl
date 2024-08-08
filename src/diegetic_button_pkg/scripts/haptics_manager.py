import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32 as int_msg
from std_msgs.msg import String as string_msg
from std_msgs.msg import Float32 as float_msg

from time import sleep

import numpy as np


# HAPTIC MODES
# VS = Vibration SkinStretch
# V = Viration
# S = Skin Stretch

haptic_mode = "V"

REFRESH_RATE = 10

sleep_time = 0.2


class HapticsNode(Node):
    def __init__(self):
        super().__init__("haptic_feedback_node")
        self.get_logger().info("Haptic Feedback Node is Running...")

        # PUBLISHERS
        self.publisher_haptic_feedback = self.create_publisher(
            int_msg, "/haptic_feedback_uros", 1
        )
        """self.publisher_haptic_feedback_position = self.create_publisher(
            float_msg, "/haptic_feedback_fposition", 1
        )"""

        # SUBSCRIBERS
        self.subscriber_robot_strings = self.create_subscription(
            string_msg, "/haptic_feedback_robot_string", self.process_action_robot, 1
        )

        self.subscriber_input_strings = self.create_subscription(
            string_msg, "/haptic_feedback_input_string", self.process_action_input, 1
        )

        """self.subscriber_position_x = self.create_subscription(
            float_msg, "/haptic_feedback_position_x", self.process_position, 1
        )"""

        #Variables to keep track of current feedback
        self.vibration_1 = 0 # TODO rename to forward / left/ whatever
        self.vibration_2 = 0
        self.vibration_3 = 0
        
        # Now buzz twice to show that we have activated
        #self.haptic_feedback(1, 1, 1)
        #sleep(0.2)
        #self.haptic_feedback(0, 0, 0)

        self.update = self.create_timer(1.0/REFRESH_RATE, self.update_haptics)


    pass

    def update_haptics(self):
        self.haptic_feedback(self.vibration_1, self.vibration_2, self.vibration_3)
        self.vibration_1 = 0
        self.vibration_2 = 0
        self.vibration_3 = 0

    def process_action_robot(self, msg):

        data = str(msg.data).lower()
        self.get_logger().info(f"Processing action: {data}")
        match data:
            case "crash":
                # SET ALL TO ON
                self.vibration_1 = 1
                self.vibration_2 = 1
                self.vibration_3 = 1
            case "grasping":
            # SETS LEFT AND RIGHT VIBRATIONS ON
                self.vibration_1 = 1
                self.vibration_3 = 1
            case "off":
            # SETS LEFT AND RIGHT VIBRATIONS  OFF
                self.vibration_1 = 0
                self.vibration_3 = 0
            case _:
                self.get_logger().info("Haptic Feedback action msg invalid.")
            
    def process_action_input(self, msg):

        data = str(msg.data).lower()
        self.get_logger().info(f"Processing action: {data}")
        match data:
            case "button_press":
                vibration_2 = 1
                # Do something
            case "off":
                self.vibration_2 = 0
            case _:
                self.get_logger().info("Haptic Feedback action msg invalid.")
            
        pass

    def process_position(self, msg):
        self.get_logger().log("position feedback sent")

        # Need to figure out if we need to do the maths on this end
        min = -1.0
        max = 1.0
        f_msg = float_msg()
        f_msg.data = np.interp(min, max, msg.data)
        #self.publisher_haptic_feedback_position(f_msg)
        pass

    def haptic_feedback(self, v1, v2, v3):
        # send an integer message
        #self.get_logger().info("haptic_feedback")

        # publish messageshould
        haptic_feedback_msg = int_msg()
        haptic_feedback_msg.data = int(f"3{v1}{v2}{v3}")
        self.publisher_haptic_feedback.publish(haptic_feedback_msg)

        pass

    def turn_off_feedback(self):
        self.get_logger().info("haptic_feedback")

        haptic_feedback_msg = int_msg()
        haptic_feedback_msg.data = 3000
        #self.publisher_haptic_feedback.publish(haptic_feedback_msg)

        pass

    def tap_single_v(self, v_index, val):
        self.get_logger().info("haptic_feedback")

        haptic_feedback_msg = int_msg()
        haptic_feedback_msg.data = int(f"2{v_index}{val}")
        #self.publisher_haptic_feedback.publish(haptic_feedback_msg)

        pass

    def positional_feedback(self, x_max, x_min, x_val):
        self.get_logger().info("haptic_feedback_positional")
        value = int_msg()
        value.data = ((x_val - x_min) * 100) / (x_max - x_min)
        #self.publisher_haptic_feedback_position.publish(value)

        pass

    def pulse_feedback(self, t, v1, v2, v3):
        haptic_feedback_msg = int_msg()
        haptic_feedback_msg.data = int(f"3{v1}{v2}{v3}")
        #self.publisher_haptic_feedback.publish(haptic_feedback_msg)
        sleep(t)
        haptic_feedback_msg.data = int(f"3{0}{0}{0}")
        #self.publisher_haptic_feedback.publish(haptic_feedback_msg)


def main(args=None):
    rclpy.init()
    publisher = HapticsNode()
    print("Haptics Node is Running...")

    try:
        rclpy.spin(publisher)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        publisher.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == "__main__":
    main()
