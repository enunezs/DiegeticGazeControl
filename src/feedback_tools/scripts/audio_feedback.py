#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32

import threading
import time
import os
import pyttsx3
import simpleaudio as sa
from ament_index_python.packages import get_package_share_directory
from gtts import gTTS  # Google TTS
from pydub import AudioSegment
import tempfile
import playsound  # To play MP3 files (install with pip install playsound==1.2.2)


class AudioFeedbackNode(Node):
    """
    Provides audio feedback (beeps + voice) based on ROS events.
    """

    def __init__(self):
        super().__init__('audio_feedback_node')
        self.get_logger().info("Audio Feedback Node started 🎧")

        # === CONFIG ===
        self.tts_engine = "pyttsx3"  # Change to "google" for Google TTS
        # self.tts_engine = "google" 

        # Get package share path
        pkg_share = get_package_share_directory('feedback_tools')
        self.sound_dir = os.path.join(pkg_share, 'sounds')

        # === Beep sounds ===
        self.sounds = {
            "button": "click.wav",
            "confirm": "blipSelect.wav",
            "warning": "powerUp.wav",
        }
        for key in self.sounds:
            self.sounds[key] = os.path.join(self.sound_dir, self.sounds[key])

        # === pyttsx3 setup ===
        self.voice_engine = pyttsx3.init()
        self.voice_engine.setProperty('rate', 180)
        voices = self.voice_engine.getProperty('voices')
        self.voice_engine.setProperty('voice', voices[0].id)
        self.voice_engine.setProperty('voice', 'english_rp+f3')

        # === State tracking ===
        self.last_mode = None
        self.last_played_time = {}
        self.cooldown = 0.5  # seconds

        # === Thread-safe audio ===
        self.audio_lock = threading.Lock()

        # === Subscribers ===
        self.create_subscription(String, '/teleop/current_mode', self.mode_callback, 10)
        self.create_subscription(String, '/controller/controller_status_info', self.robot_info, 10)
        self.create_subscription(String, '/controller/action_status', self.action_callback, 10)
        self.create_subscription(String, '/safety/status', self.safety_callback, 10)
        self.create_subscription(Int32, '/button_events', self.button_callback, 10)

    # === Event Handlers ===
    def button_callback(self, msg):
        self.play_beep("button")

    def action_callback(self, msg):
        text = msg.data.lower()
        if "completed" in text or "done" in text:
            self.play_beep("confirm")

    def safety_callback(self, msg):
        if "collision" in msg.data.lower() or "force" in msg.data.lower():
            self.play_beep("warning")
            self.say("Warning!")

    def mode_callback(self, msg):
        new_mode = msg.data.strip()
        if new_mode != self.last_mode:
            self.last_mode = new_mode
            self.say(f"Switched to {new_mode}")

    def robot_info(self, msg):
        info = msg.data.lower()
        self.play_beep("info")
    

    # === Playback ===
    def play_beep(self, name):
        if name not in self.sounds:
            self.get_logger().warn(f"No sound for {name}")
            return

        now = time.time()
        last_time = self.last_played_time.get(name, 0)
        if now - last_time < self.cooldown:
            return
        self.last_played_time[name] = now

        filepath = self.sounds[name]
        if not os.path.exists(filepath):
            self.get_logger().warn(f"Missing sound file: {filepath}")
            return

        threading.Thread(target=lambda: sa.WaveObject.from_wave_file(filepath).play(), daemon=True).start()

    def say(self, text):
        self.get_logger().info(f"Speaking: {text}")
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        with self.audio_lock:
            if self.tts_engine == "google":
                self._say_google(text)
            else:
                self._say_pyttsx3(text)

    # === TTS Methods ===
    def _say_pyttsx3(self, text):
        self.voice_engine.say(text)
        self.voice_engine.runAndWait()

    def _say_google(self, text):
        try:
            # === Generate Google TTS MP3 ===
            tts = gTTS(text=text, lang='en', tld='co.uk')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                mp3_path = fp.name
                tts.save(mp3_path)

            # === Convert MP3 to WAV (safe format) ===
            sound = AudioSegment.from_mp3(mp3_path)
            sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            wav_path = mp3_path.replace(".mp3", ".wav")
            sound.export(wav_path, format="wav")

            # === Play WAV using simpleaudio ===
            wave_obj = sa.WaveObject.from_wave_file(wav_path)
            play_obj = wave_obj.play()
            play_obj.wait_done()

            # === Clean up ===
            os.remove(mp3_path)
            os.remove(wav_path)

        except Exception as e:
            self.get_logger().error(f"Google TTS failed: {e}")

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
