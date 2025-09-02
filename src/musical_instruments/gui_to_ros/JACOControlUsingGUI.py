# from diegetic_button_pkg.scripts import joy
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
import joy_node
from pprint import pprint
import rclpy
import sys
import os
import numpy as np
from PyQt5.QtCore import QTimer


sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "..", "diegetic_button_pkg", "scripts", "devices"
    )
)

from joy_node import ControllerPublisher
from sensor_msgs.msg import Joy

# controller = joy.ControllerPublisher()


class Buttons(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the button
        self.speed_up_button = QPushButton("move left faster")
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)
        self.speed_up_button.clicked.connect(self.move_left)

        self.joystick_outs = [0, 0, 0, 0, 0, 0]
        self.button_outs = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        self.speed = 0
        self.stopped = False

        self.size_array = np.array((self.size().width(), self.size().height()))

        # Set up the layout
        layout = QVBoxLayout()
        layout.self.addLabel(self.gripper_title)
        addWidget(self.speed_up_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)

        # Set up the window
        self.setWindowTitle("Hello World Widget")
        self.setGeometry(100, 100, 200, 100)

    def stop(self):
        print("Stop!")
        self.speed = 0
        self.stopped = True

    def move_left(self):
        # move the robot left by some degree.
        print("Move left!")
        print(os.getcwd())
        if self.joystick_outs[1] != 0 and self.joystick_outs < 0.001:
            self.joystick_outs[1] = self.joystick_outs[1] * 1.6
        else:
            self.joystick_outs[1] = 0.0000001

        print(self.joystick_outs[1])


class ClickableWindow(QLabel):
    def __init__(self, button_click_func=None, window_click_func=None):
        super().__init__()

        # Set up the label to display cself.size().width(), self.size().height())lick coordinates
        self.label = QLabel("Click anywhere in the window", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.speed = np.array((0, 0))
        self.size_np_array = np.array((self.size().width(), self.size().height()))
        self.button_click_func = button_click_func
        self.window_click_func = window_click_func
        self.publish_timer = QTimer(self)
        self.publish_timer.timeout.connect(
            lambda: self.window_click_func(self.speed[0], self.speed[1])
        )
        self.publish_timer.start(20)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Set u        self.addLabel(self.gripper_title)p the window
        self.setWindowTitle("Clickable Window")
        self.setGeometry(100, 100, 400, 300)

    def update_mouse_position(self, event):
        pos = np.array((event.x(), event.y()))
        speed = pos / self.size_array * 2 - 1
        self.speed = np.clip(speed, -1, 1) * np.array((1, -1))
        self.label.setText(
            f"Clicked at: {pos}\n total window size: {self.size_array}\nnormed output: {self.speed}"
        )

    def mousePressEvent(self, event):
        # Get the position of the click
        self.update_mouse_position(event)

    def mouseReleaseEvent(self, event):
        self.speed = np.array((0, 0))
        self.label.setText(f"Window size: {self.size_array}")
        return super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        self.update_mouse_position(event)
        return super().mouseMoveEvent(event)

    def resizeEvent(self, event):
        # Get the new size of the window
        size = self.size()
        width = size.width()
        height = size.height()

        self.size_array = np.array((width, height))

        self.label.setText(f"Window size: {self.size_array}")
        super().resizeEvent(event)


class Window(QWidget):
    def __init__(self, ros_node_publisher):
        super().__init__()
        self.clickable_window = ClickableWindow(
            window_click_func=controller_publisher.callback
        )
        self.buttons = Buttons()
        self.setGeometry(100, 100, 700, 700)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.clickable_window)
        # self.layout.addStretch()
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)


if __name__ == "__main__":
    np.set_printoptions(precision=3)
    rclpy.init()  # Initialize ROS DDS
    controller_publisher = ControllerPublisher()
    app = QApplication(sys.argv)
    widget = Window(controller_publisher)
    widget.show()
    sys.exit(app.exec_())
