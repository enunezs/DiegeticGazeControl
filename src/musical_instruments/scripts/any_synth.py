#! /usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import fluidsynth


class SoundPlayerNode(Node):  # Create node inheriting from Node

    def __init__(self):
        super().__init__("sound_player_node")

        # Initialize FluidSynth
        self.synth = fluidsynth.Synth()
        self.synth.start(
            driver="alsa"
        )  # Use 'alsa' for Linux, change for other platforms

        # Load a SoundFont file (adjust path as necessary)
        soundfont_file = "/root/ws/musical_instruments/scripts/The_Ultimate_Megadrive_Soundfont/The_Ultimate Megadrive_Soundfont.sf2"
        soundfont_file = "/root/ws/musical_instruments/scripts/8bitsf.SF2"

        sfid = self.synth.sfload(soundfont_file)
        track = 0
        banknum = 0
        presetnum = 0
        self.synth.program_select(track, sfid, banknum, presetnum)

        # Subscriber
        self.subscriber_note_listener = self.create_subscription(
            Int32, "piano_topic", self.play_note, 1
        )

    def play_note(self, msg: Int32):
        note = msg.data + 60
        self.synth.noteon(0, note, 100)

    def close(self):
        # Clean up resources
        self.synth.delete()


def main():
    rclpy.init()  # Initialize ROS DDS

    sound_player = SoundPlayerNode()  # Create instance of function

    print("Sound Player Node is Running...")

    try:
        rclpy.spin(sound_player)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        sound_player.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !
    sound_player.close()


if __name__ == "__main__":
    main()
