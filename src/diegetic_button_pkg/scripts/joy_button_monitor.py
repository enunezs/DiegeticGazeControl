#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import time

class JoyTest(Node):
    def __init__(self):
        super().__init__('joy_test')
        self.publisher_joy = self.create_publisher(Joy, 'joy', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 Hz
        self.state = 0
        self.start_time = time.time()

    def timer_callback(self):
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        if self.state == 0 and elapsed_time >= 2:
            self.state = 1
            self.start_time = current_time
        elif self.state == 1 and elapsed_time >= 4:
            self.state = 2
            self.start_time = current_time
        elif self.state == 2 and elapsed_time >= 2:
            self.state = 3
            self.start_time = current_time
        elif self.state == 3 and elapsed_time >= 4:
            self.state = 4
            self.start_time = current_time
        elif self.state == 4 and elapsed_time >= 2:
            self.state = 5
            self.start_time = current_time

        joy_msg = Joy()
        joy_msg.header.stamp = self.get_clock().now().to_msg()
        joy_msg.header.frame_id = 'joy'
        joy_msg.axes = [0.0] * 8
        joy_msg.buttons = [0] * 11

        if self.state == 1:
            joy_msg.buttons[0] = 1  # A 按钮按下
        elif self.state == 2:
            joy_msg.buttons[1] = 1  # B 按钮按下
        elif self.state == 3:
            joy_msg.buttons[2] = 1  # X 按钮按下
        elif self.state == 4:
            joy_msg.buttons[3] = 1  # Y 按钮按下

        self.publisher_joy.publish(joy_msg)
        self.get_logger().info(f'Published joy message with state {self.state}')

def main(args=None):
    rclpy.init(args=args)
    joy_test = JoyTest()
    rclpy.spin(joy_test)
    joy_test.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

