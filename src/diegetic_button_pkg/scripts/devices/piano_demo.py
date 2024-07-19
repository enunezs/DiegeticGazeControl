#! /usr/bin/env python3

# Base functions
import rclpy
from rclpy.node import Node

from cv2 import destroyAllWindows

# Import messages
from diegetic_button_pkg.msg import InputStatus
from diegetic_button_pkg.msg import InputStatusArray

# Piano stuff
from pysinewave import SineWave

volume = 0


class PianoPublisher(Node):  # Create node inheriting from Node

    def __init__(self):

        # Base node init
        super().__init__("piano_demo_node")

        # Base props
        self.sinewave = SineWave(
            pitch=0, decibels=0, pitch_per_second=50, decibels_per_second=500
        )
        self.sinewave.stop()

        # Subscribers
        self.subscriber_input_listener = self.create_subscription(
            InputStatusArray, "diegetic/inputs", self.update_piano, 1
        )

        self.status = "stop"
        self.pitch = 0

    def update_piano(self, InputStatusArray_msg):

        # Unpack
        inputs = InputStatusArray_msg.inputs
        print(f"inputs: {inputs}")
        active = False
        new_pitch = []  # TODO: change to avg if multiple?

        for new_input in inputs:
            # print(f"status: {new_input.status}")
            if new_input.status == "active" or new_input.status == "hover":
                new_pitch = int(new_input.input_id)
                print("New pitch")
                active = True

            if new_input.status == "inactive":
                pass
            if new_input.status == "hover":
                pass

        if active:
            print("Active")
            # If stopped
            if self.status == "stop":
                self.sinewave.play()
                # volume = 0
                self.sinewave.set_volume(volume)
                self.status = "playing"

            # If playing a different tone
            if new_pitch and new_pitch != self.pitch:
                # volume = 0  # (dB -> 1 amplitude sine)
                # self.sinewave.play()
                self.sinewave.set_pitch(new_pitch)
                self.pitch = new_pitch

            # print(f"Playing pitch {pitch}")
            # self.sinewave.set_pitch(pitch)
            # self.sinewave.set_volume(volume)
            pass
            # self.sinewave.play()
            # TODO: Decrease volume slowly
            # Implement decay

        """
        elif not active:
            # self.sinewave.stop()
            volume = -100
            self.sinewave.set_volume(volume)
            self.status = "stop"
            pass
        """
        # print(f"I think you are looking at {button_id} ")
        # self.sinewave.set_volume(volume)


def main():
    rclpy.init()  # Initialize ROS DDS

    piano_publisher = PianoPublisher()  # Create instance of function
    print("Paper piano demo Publisher Node is Running...")

    try:
        rclpy.spin(piano_publisher)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        piano_publisher.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == "__main__":
    main()
