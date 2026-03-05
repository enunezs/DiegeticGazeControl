
from rclpy.node import Node

from std_msgs.msg import String


class SupervisorNode(Node):

    """

    Supervisor Node

    Responsible for:

    - Maintaining system state (LISTENING / IDLE)

    - Receiving recognized speech from ASR node

    - Interpreting basic voice commands

    """

    def __init__(self):
       #  self.get_logger().info("NEW VERSION OF SUPERVISOR LOADED")
        # Initialize ROS2 node

        super().__init__('supervisor_node')

        # SYSTEM STATE INITIALISATION: The system starts in LISTENING mode

        self.system_state = "LISTENING"

        self.get_logger().info("System State: LISTENING")

        self.get_logger().info("Speech ENABLED")

        # SUBSCRIBER: ASR OUTPUT

        # Subscribes to the topic published by asr_node

        # Topic name matched

        self.subscription = self.create_subscription(

            String,

            'recognized_speech',

            self.speech_callback,

            10

        )

    # CALLBACK FUNCTION – triggered when speech arrives

    def speech_callback(self, msg):

        """

        Called whenever the ASR node publishes text.

        """

        # Clean up the incoming text

        text = msg.data.strip().lower()

        self.get_logger().info(f"Heard: {text}")
       
        # Always allow START
        if "start" in text:
            self.process_command(text)
            return

        # Only process commands if system is LISTENING

        if self.system_state == "LISTENING":

            self.process_command(text)

        else:

            self.get_logger().info("Ignoring speech (System in IDLE state)")

    # COMMAND PROCESSING FUNCTION

    def process_command(self, text):

        """

        Very basic command recognition logic.

        Can be expanded later or moved into a parser node.

        """

        # Stop command

        if "stop" in text:

            self.get_logger().info("Stop command received")

            self.system_state = "IDLE"

            self.get_logger().info("System State changed to IDLE")

        # Start command

        elif "start" in text:

            self.get_logger().info("Start command received")

            self.system_state = "LISTENING"

            self.get_logger().info("System State changed to LISTENING")

        # Status query

        elif "status" in text:

            self.get_logger().info(f"Current System State: {self.system_state}")

        # Unknown speech

        else:

            self.get_logger().info("No valid command detected")

# MAIN 

def main(args=None):

    rclpy.init(args=args)

    node = SupervisorNode()

    try:

        # Keep node running

        rclpy.spin(node)

    except KeyboardInterrupt:

        node.get_logger().info("Supervisor Node shutting down")

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':

    main()
 
