import rclpy

from rclpy.node import Node

from std_msgs.msg import String

import sounddevice as sd

import queue

import json

from vosk import Model, KaldiRecognizer


class ASRNode(Node):

    def __init__(self):

        super().__init__('asr_node')

        # ROS publisher

        self.publisher_ = self.create_publisher(String, 'recognized_speech', 10)

        self.get_logger().info("ASR Node Started")

        # Queue for audio data

        self.q = queue.Queue()

        # Load speech recognition model

        self.model = Model("/root/ws/DiegeticGazeControl/vosk-model-small-en-us-0.15")

        self.rec = KaldiRecognizer(self.model, 16000)

        # Start microphone stream

        self.stream = sd.InputStream(

            samplerate=16000,

            blocksize=8000,

            dtype='int16',

            channels=1,

            callback=self.audio_callback,

            device=7  # Webcam microphone

        )

        self.stream.start()

        # Timer to process audio regularly

        self.timer = self.create_timer(0.1, self.process_audio)

    def audio_callback(self, indata, frames, time, status):

        """Called when microphone captures audio"""

        self.q.put(bytes(indata))

    def process_audio(self):

        """Process microphone audio and perform speech recognition"""

        while not self.q.empty():

            data = self.q.get()

            if self.rec.AcceptWaveform(data):

                result = json.loads(self.rec.Result())

                text = result.get("text", "")

                if text != "":

                    self.publish_text(text)

    def publish_text(self, text):

        """Publish recognized speech to ROS"""

        msg = String()

        msg.data = text

        self.get_logger().info(f"Recognized speech: {text}")

        self.publisher_.publish(msg)


def main(args=None):

    rclpy.init(args=args)

    node = ASRNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()
 
