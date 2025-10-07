#! /usr/bin/env python3

import rclpy
from rclpy.node import Node
from diegetic_button_pkg.msg import InputStatusArray
from std_msgs.msg import Int32


class InputParserNode(Node):  # Create node inheriting from Node

    def __init__(self):
        super().__init__("input_parser_node")

        # Subscribers
        self.subscriber_input_listener = self.create_subscription(
            InputStatusArray, "diegetic/inputs", self.update_piano, 1
        )

        # Publisher
        self.publisher_note_simple = self.create_publisher(Int32, "piano_topic", 1)

        self.prev_play = []

    def update_piano(self, InputStatusArray_msg):
        # Process inputs. Turn into two arrays, one for buttons and one for status
        key = []
        play = []
        for input in InputStatusArray_msg.inputs:
            key.append(self.note_to_midi(input.input_id))
            if input.status == "active":
                play.append(1)
            else:
                play.append(0)

        if self.prev_play is None:
            self.prev_play = play.copy()

        for i in range(0, len(play)):
            if play[i] == 1:
                msg = Int32()
                msg.data = key[i] - 60
                self.publisher_note_simple.publish(msg)

    def note_to_midi(self, note: str):
        try:
            res = int(note) + 60
            return res  # 0 is C4
        except ValueError:
            return 0


def main():
    rclpy.init()  # Initialize ROS DDS

    input_parser = InputParserNode()  # Create instance of function

    print("Input Parser Node is Running...")

    try:
        rclpy.spin(input_parser)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        input_parser.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == "__main__":
    main()
