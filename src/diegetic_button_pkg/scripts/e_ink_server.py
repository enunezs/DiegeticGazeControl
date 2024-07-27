#! /usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import paho.mqtt.client as mqtt


class JoyButtonMonitor(Node):
    def __init__(self):
        super().__init__("e_ink_server")
        self.get_logger().info("Starting e_ink server")
        self.previous_buttons = [0] * 4  # ABXY四个按钮

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.connect("broker.emqx.io", 1883, 60)
        self.topic = "epd/display"

        self.subscription = self.create_subscription(Joy, "/joy", self.joy_callback, 10)
        self.subscription

    def joy_callback(self, data):
        # ABXY 按钮的索引分别为 0, 1, 2, 3
        buttons = data.buttons[:4]
        for i, button in enumerate(buttons):
            if button != self.previous_buttons[i]:
                if button == 1:
                    msg = (i + 1) * 10  # 按下时发布10, 20, 30, 40
                else:
                    msg = (i + 1) * 10 + 1  # 松开时发布11, 21, 31, 41

                # 发布到MQTT
                self.client.publish(self.topic, msg)
                self.get_logger().info(
                    f"Button {i} state changed to {button}, published {msg} to MQTT"
                )

            self.previous_buttons[i] = button


def main(args=None):
    rclpy.init(args=args)
    joy_button_monitor = JoyButtonMonitor()
    rclpy.spin(joy_button_monitor)
    joy_button_monitor.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
