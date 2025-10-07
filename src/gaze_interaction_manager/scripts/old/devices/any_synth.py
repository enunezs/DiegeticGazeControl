#! /usr/bin/env python3

# Base functions
import rclpy
from rclpy.node import Node

from cv2 import destroyAllWindows

# Import messages
from diegetic_button_pkg.msg import InputStatus
from diegetic_button_pkg.msg import InputStatusArray
from std_msgs.msg import Int32


# Piano stuff
# from pysinewave import SineWave
import fluidsynth

volume = 0

from functools import reduce


class SoundPlayerNode(Node):  # Create node inheriting from Node

    def __init__(self):

        #Base node initsoundfont_file = (
        #    "/root/ws/origami/src/diegetic_button_pkg/scripts/devices/8bitsf.SF2"
        #)
        super().__init__("sound_player_node")

        # Initialize FluidSynth
        self.synth = fluidsynth.Synth()
        self.synth.start(
            driver="alsa"
        )  # Use 'alsa' for Linux, change for other platforms
        "/root/ws/origami/src/diegetic_button_pkg/scripts/devices/8bitsf.SF2"

        # Load a SoundFont file (adjust path as necessary)
        soundfont_file = "/root/ws/origami/src/diegetic_button_pkg/scripts/devices/The_Ultimate_Megadrive_Soundfont/The_Ultimate Megadrive_Soundfont.sf2"
        """"""

        sfid = self.synth.sfload(soundfont_file)
        track = 0
        banknum = 0
        presetnum = 0
        self.synth.program_select(track, sfid, banknum, presetnum)

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

        # play = reduce(lambda i,j: int(i) ^ int(j),play )

        # edge = set(play) ^ set(self.prev_play)
        # rising_edge = edge & set(play)
        # for i,j in enumerate(rising_edge):
        for i in range(0, len(play)):
            # for i in range(0, len(rising_edge)):
            if play[i] == 1:
                self.synth.noteon(
                    0, (key[i]), 100
                )  # Channel 0, key MIDI note, velocity

                octave_chord = False
                if octave_chord:
                    self.synth.noteon(
                        0, (key[i] + 12), 60
                    )  # Channel 0, key MIDI note, velocity

                print(key[i] - 60)
                msg = Int32()
                msg.data = key[i] - 60
                self.publisher_note_simple.publish(msg)

            elif play[i] == 0:
                pass
                # self.synth.noteoff(0, (key[i]))

    def note_to_midi(self, note: str):
        try:
            res = int(note) + 60
            # print("pass")
            return res  # 0 is C4
        except ValueError:
            # print("Rejected")
            return 0

    def close(self):
        # Clean up resources
        self.synth.delete()


def main():
    rclpy.init()  # Initialize ROS DDS

    music_publisher = SoundPlayerNode()  # Create instance of function

    print("Paper piano demo Publisher Node is Running...")

    try:
        rclpy.spin(music_publisher)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        music_publisher.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !
    music_publisher.close()


if __name__ == "__main__":
    main()
