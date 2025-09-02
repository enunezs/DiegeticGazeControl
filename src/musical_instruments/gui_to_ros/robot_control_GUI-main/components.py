"""This file houses all basic components that are used in the GUI.

This includes buttons, labels, and other widgets that are used without any specific functionality.
"""

from itertools import cycle
import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import numpy as np

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget, 
    QVBoxLayout,
    QWidget,
    QApplication
)


class ContinousButton(QPushButton):
    """ContinousButton is a QPushButton that sends a signal when pressed and held.

    Used for any control that requires a continuous signal to be sent.
    """

    def __init__(self, name, callback):
        super().__init__(name)
        self.setMouseTracking(True)
        self.mouse_pressed = False
        self.callback = callback
        self.timer = QTimer()
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.callback)

    def mousePressEvent(self, event):
        self.mouse_pressed = True
        self.timer.start()

    def mouseReleaseEvent(self, event):
        self.mouse_pressed = False
        self.timer.stop()


class ClickableLabel(QLabel):
    def __init__(self, translation_callback, rotation_callback):
        super().__init__()
        self.setMouseTracking(True)
        self.mouse_pressed = False
        self.current_mouse_position = None

        # Store the callback functions for each mode.
        self.translation_mode_callback = translation_callback
        self.rotation_mode_callback = rotation_callback

        # Create threads for each camera
        # Create timer for continuous press
        self.timer = QTimer()
        self.timer.timeout.connect(self.translation_mode_click)
        self.timer.setInterval(20)

    def get_current_mouse_position(self):
        print(f"mouse_pos: {self.current_mouse_position}")

    def translation_mode_click(self):
        """Handle clicks in position control mode"""
        self.translation_mode_callback(self.current_mouse_position)
    
    def rotation_mode_click(self):
        self.rotation_mode_callback(self.current_mouse_position)
    
    def find_mouse_position_from_event(self, event):
        position = np.array((event.pos().x(), event.pos().y()))
        size = np.array((self.width(), self.height()))
        normalised_position = position * 2 / size - 1
        limited_position = np.clip(normalised_position, -1, 1)
        self.current_mouse_position = limited_position.tolist()
        return normalised_position, position

    def mousePressEvent(self, event):
        self.mouse_pressed = True
        self.get_current_mouse_position()
        self.timer.start()

    def mouseMoveEvent(self, event, QMouseEvent=None):
        normalised_position, position = self.find_mouse_position_from_event(event)

    def mouseReleaseEvent(self, event, QMouseEvent=None):
        self.mouse_pressed = False
        self.timer.stop()


class ControlViewPage(QWidget):
    """Generates a simple Control View Page: This is a single page that will be passed into the ControlView Widget.

    initial inputs: button_func_dict: type: Dict[str, function]

    The button func dict is a dictionary containing button names and callback functions.
    These will be presented in a horizontal fashion.


    """

    def __init__(self, button_func_dict=None, name=None):
        super().__init__()
        self.VBL = QVBoxLayout()
        self.HBL = QHBoxLayout()
        self.buttons = []
        self.timers = []

        for button_name, func in button_func_dict.items():
            button = ContinousButton(button_name, func)

            self.buttons.append(button)
            self.HBL.addWidget(button)

        if name is not None:
            self.name = QLabel(name, self)
            self.name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.name.setAlignment(Qt.AlignCenter)
            self.VBL.addWidget(self.name)

        self.VBL.addLayout(self.HBL)
        self.setLayout(self.VBL)


class ControlView(QStackedWidget):
    """A stacked widget view of ControlViewPage widgets.
    This enables all widgets to be grouped together and switched between using Tab.

    Inputs:
    rotation funcs: These are the functions that will be tied to a clockwise or anticlockwise rotation.
    translate funcs

    """

    def __init__(self, pages):
        super().__init__()
        self.pages = [ControlViewPage(page_dict, name) for name, page_dict in pages.items()]

        for page in self.pages:
            self.addWidget(page)

        self.widget_list = cycle(range(len(self.pages)))
        # Add Widgets here.
        self.current_button = next(self.widget_list)

        self.setCurrentIndex(self.current_button)

    def setCurrentIndex(self, index):
        self.current_button = index
        super().setCurrentIndex(index)

if __name__ == "__main__":
    App = QApplication(sys.argv)
    
    pages = {
        "translation": 
            {"forward": lambda: print("Translating forward"), 
            "backward": lambda: print("Translating backward")},
        
        "rotation":
            {"clockwise": lambda: print("Rotating left"),
            "anticlockwise": lambda: print("Rotating right")}
            }

    Root = ControlView(pages)
    Root.show()
    sys.exit(App.exec())