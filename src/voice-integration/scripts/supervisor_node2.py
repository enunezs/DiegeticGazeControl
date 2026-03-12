#!/usr/bin/env python3


import rclpy

from rclpy.node import Node

from std_msgs.msg import String


class SupervisorNode(Node):

    """

    Supervisor Node

    Responsible for:

    - Maintaining system state (LISTENING / IDLE)

    - Receiving recognized speech from ASR node

    - Interpreting voice commands

    - Publishing robot commands to /voice_commands

    """

    def __init__(self):

        # Initialize ROS2 node

        super().__init__('supervisor_node')

        self.get_logger().info("NEW VERSION OF SUPERVISOR LOADED")

        # Publisher for robot commands

        self.command_pub = self.create_publisher(String, 'voice_commands', 10)

        # System state

        self.system_state = "LISTENING"

        self.get_logger().info("System State: LISTENING")

        self.get_logger().info("Speech ENABLED")

        # Subscriber to ASR output

        self.subscription = self.create_subscription(

            String,

            'recognized_speech',

            self.speech_callback,

            10

        )

    # Callback triggered when ASR publishes speech

    def speech_callback(self, msg):

        text = msg.data.strip().lower()

        self.get_logger().info(f"Received speech: {text}")

        self.process_command(text)


    # Command processing

    def process_command(self, text):

        msg = String()

        # System control commands

        if "stop" in text:

            self.get_logger().info("Stop command received")

            self.system_state = "IDLE"

            self.get_logger().info("System State changed to IDLE")

            msg.data = "stop"

            self.command_pub.publish(msg)

        elif "start" in text:

            self.get_logger().info("Start command received")

            self.system_state = "LISTENING"

            self.get_logger().info("System State changed to LISTENING")

            msg.data = "start"

            self.command_pub.publish(msg)

        elif "status" in text:

            self.get_logger().info(f"Current System State: {self.system_state}")

        # Robot task commands

        elif "tea" in text:

            self.get_logger().info("Command: make tea")

            msg.data = "tea"

            self.command_pub.publish(msg)

        elif "medicine" in text:

            self.get_logger().info("Command: give medicine")

            msg.data = "medicine"

            self.command_pub.publish(msg)

        elif "cup" in text:

            self.get_logger().info("Command: give cup")

            msg.data = "cup"

            self.command_pub.publish(msg)

        elif "towel" in text:

            self.get_logger().info("Command: give towel")

            msg.data = "towel"

            self.command_pub.publish(msg)

        else:

            self.get_logger().info("No valid command detected")

# Main

def main(args=None):

    rclpy.init(args=args)

    node = SupervisorNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        node.get_logger().info("Supervisor Node shutting down")

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':

    main()
 