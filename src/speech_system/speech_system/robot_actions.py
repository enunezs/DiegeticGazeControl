import rclpy

import os

from rclpy.node import Node

from std_msgs.msg import String

from geometry_msgs.msg import Twist

class RobotActions(Node):

    def speak(self, text):
        os.system(f'espeak "{text}"')

    def __init__(self):

        self.robot_pub = self.create_publisher(
            Twist,
            '/j2n6s300_driver/in/cartesian_velocity',
            10
        )

        self.speak("Hello. I am ready to assist you.")

        super().__init__('robot_actions')

        # Subscribe to supervisor commands

        self.subscription = self.create_subscription(

            String,

            'voice_commands',

            self.command_callback,

            10

        )

        self.get_logger().info("Robot Action Node Ready")

    def command_callback(self, msg):

        command = msg.data.lower()

        self.get_logger().info(f"Received command: {command}")

        if command == "tea":

            self.make_tea()

        elif command == "medicine":

            self.give_medicine()

        elif command == "cup":

            self.give_cup()

        elif command == "towel":

            self.give_towel()

        else:

            self.get_logger().info("Unknown command")


    # Robot task functions

    def make_tea(self):

        self.get_logger().info("Robot: preparing tea")
        self.speak("Preparing tea")

        # Example robot sequence

        self.get_logger().info("Picking up jug")
        self.speak("Picking up jug")

        self.get_logger().info("Pouring hot water")
        self.speak("Pouring hot water")

        self.get_logger().info("Tea ready")
        self.speak("Tea is ready")

    def give_medicine(self):

        self.get_logger().info("Robot: retrieving medicine bottle")
        self.speak("Retrieving medicine bottle")

        self.get_logger().info("Moving to medicine shelf")
        self.speak("Moving to medicine shelf")

        self.get_logger().info("Grasping medicine bottle")
        self.speak("Grasping medicine bottle")

        self.get_logger().info("Handing medicine to user")
        self.speak("Here is your medicine")

    def give_cup(self):

        self.get_logger().info("Robot: picking up cup")
        self.speak("Picking up cup")
        self.move_forward()

        self.get_logger().info("Moving to cup location")
        self.speak("Moving to cup location")

        self.get_logger().info("Grasping cup")
        self.speak("Grasping cup")

        self.get_logger().info("Handing cup to user")
        self.speak("Here is your cup")

    def give_towel(self):

        self.get_logger().info("Robot: picking up towel")
        self.speak("Picking up towel")

        self.get_logger().info("Moving to towel rack")
        self.speak("Moving to where towel is")

        self.get_logger().info("Grasping towel")
        self.speak("Grasping towel")

        self.get_logger().info("Handing towel to user")
        self.speak("Here is a towel")

    def move_forward(self):

        msg = Twist

        msg.linear.x = 0.1
        msg.linear.y = 0.0
        msg.linear.z = 0.0

        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = 0.0

        self.robot_pub.publish(msg)

        self.get_logger().info("Robot moving forward")


def main(args=None):

    rclpy.init(args=args)

    node = RobotActions()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()
 
