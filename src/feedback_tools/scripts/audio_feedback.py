#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32

import threading
import time
import os
import pyttsx3  # For voice feedback
import simpleaudio as sa  # For short beep WAVs

from ament_index_python.packages import get_package_share_directory
import os

class AudioFeedbackNode(Node):
    """
    Provides audio feedback (beeps + voice) based on ROS events.
    """

    def __init__(self):
        super().__init__('audio_feedback_node')
        self.get_logger().info("Audio Feedback Node started 🎧")


        # Get package share path
        pkg_share = get_package_share_directory('feedback_tools')
        self.sound_dir = os.path.join(pkg_share, 'sounds')

        # Beep sounds (replace with your .wav paths)
        # Sounds generated with https://sfxr.me/
        self.sounds = {
            "button": "click.wav",
            "confirm": "blipSelect.wav",
            "warning": "powerUp.wav",
        }
        for key in self.sounds:
            self.sounds[key] = os.path.join(self.sound_dir, self.sounds[key])

        # Voice engine
        self.voice_engine = pyttsx3.init()
        self.voice_engine.setProperty('rate', 180)
        voices = self.voice_engine.getProperty('voices')       # getting details of current voice
        #self.voice_engine.setProperty('voice', voices[0].id)  # changing index, changes voices. 0 for male
        self.voice_engine.setProperty('voice', voices[0].id)   # changing index, changes voices. 1 for female
        self.voice_engine.setProperty('voice', 'english_rp+f3') #my preference


        # State tracking to avoid repeats
        self.last_mode = None
        self.last_played_time = {}
        self.cooldown = 0.5  # seconds

        # Thread-safe audio queue
        self.audio_lock = threading.Lock()

        # Subscribers
        # self.mode_sub = self.create_subscription(String, '/teleop/current_mode', self.mode_callback, 10)

        self.create_subscription(String, '/teleop/current_mode', self.mode_callback, 10)
        self.create_subscription(String, '/controller/action_status', self.action_callback, 10)
        self.create_subscription(String, '/safety/status', self.safety_callback, 10)
        self.create_subscription(Int32, '/button_events', self.button_callback, 10)

    # === Event Handlers ===
    def button_callback(self, msg):
        """Triggered when a gaze button activates."""
        self.play_beep("button")

    def action_callback(self, msg):
        """Triggered when a task or movement completes."""
        text = msg.data.lower()
        if "completed" in text or "done" in text:
            self.play_beep("confirm")

    def safety_callback(self, msg):
        """Triggered for safety or collision warnings."""
        if "collision" in msg.data.lower() or "force" in msg.data.lower():
            self.play_beep("warning")
            self.say("Warning!")

    def mode_callback(self, msg):
        """Announce mode changes."""
        new_mode = msg.data.strip()
        if new_mode != self.last_mode:
            self.last_mode = new_mode
            self.say(f"Switched to {new_mode}. mode")

    # === Playback ===
    def play_beep(self, name):
        """Plays a short WAV file (non-blocking)."""
        if name not in self.sounds:
            self.get_logger().warn(f"No sound for {name}")
            return

        # Debounce
        now = time.time()
        last_time = self.last_played_time.get(name, 0)
        if now - last_time < self.cooldown:
            return
        self.last_played_time[name] = now

        filepath = self.sounds[name]
        if not os.path.exists(filepath):
            self.get_logger().warn(f"Missing sound file: {filepath}")
            return

        # Run sound in separate thread
        threading.Thread(target=lambda: sa.WaveObject.from_wave_file(filepath).play(), daemon=True).start()

    def say(self, text):
        self.get_logger().info(f"Speaking: {text}")
        """Speak text using TTS (non-blocking)."""
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        with self.audio_lock:
            self.voice_engine.say(text)
            self.voice_engine.runAndWait()


def main(args=None):
    rclpy.init(args=args)
    node = AudioFeedbackNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
