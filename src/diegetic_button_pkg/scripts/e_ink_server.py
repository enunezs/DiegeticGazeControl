#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from diegetic_button_pkg.msg import InputStatusArray
import paho.mqtt.client as mqtt
import time


class ButtonStateMonitor(Node):
    def __init__(self):
        super().__init__("e_ink_server")
        self.get_logger().info("Starting e_ink server")

        self.subscription = self.create_subscription(
            InputStatusArray, "diegetic/inputs", self.listener_callback, 10
        )
        self.subscription  # prevent unused variable warning

        # 初始化MQTT客户端
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        # self.client.connect("192.168.0.4", 1883, 60)
        self.client.connect("broker.emqx.io", 1883, 60)
        self.topic = "epd/display"

        # 初始化状态字典，存储每个按钮的当前状态
        self.button_states = {
            "S1Y_+1": "inactive",
            "S1Y_-1": "inactive",
            "S1X_-1": "inactive",
            "S1X_+1": "inactive",
            "TR": "inactive",
            "TL": "inactive",
            "A": "inactive",
            "B": "inactive",
            "X": "inactive",
        }

        # 初始化时间戳字典，存储每个按钮的最后消息发送时间
        self.last_publish_time = {key: 0 for key in self.button_states}

        self.button_mapping = {
            "S1Y_+1": "up",
            "S1Y_-1": "down",
            "S1X_-1": "right",
            "S1X_+1": "left",
            "TR": "forward",
            "TL": "backward",
            "A": "open",
            "B": "close",
            "X": "switch",
        }

    def listener_callback(self, msg):
        current_time = time.time()
        debounce_interval = 0.3  # 去抖动时间间隔，单位：秒

        for input_status in msg.inputs:
            button_id = input_status.input_id
            status = input_status.status

            # 仅处理我们关心的8个按钮
            if button_id in self.button_states:
                previous_status = self.button_states[button_id]

                if status != previous_status:
                    action = self.button_mapping[button_id]
                    if status == "active":
                        message = f"{action}_press"
                    elif status == "inactive":
                        message = f"{action}_release"

                    # 检查是否符合去抖动时间间隔
                    if (
                        current_time - self.last_publish_time[button_id]
                        > debounce_interval
                    ):
                        self.get_logger().info(message)
                        self.client.publish(self.topic, message)
                        self.last_publish_time[button_id] = current_time

                    # 更新按钮状态
                    self.button_states[button_id] = status


def main(args=None):
    rclpy.init(args=args)
    button_state_monitor = ButtonStateMonitor()
    rclpy.spin(button_state_monitor)

    button_state_monitor.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
