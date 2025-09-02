"""threading code taken from: https://www.codepile.net/pile/ey9KAnxn

found something about this being a complex way to implement threading here:
https://mayaposch.wordpress.com/2011/11/01/how-to-really-truly-use-qthreads-the-full-explanation/

but the code uses C++, so I'll have to figure it out later."""

import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import cv2
from itertools import cycle
import numpy as np
from JACOControlUsingGUI import ClickableWindow, ControllerPublisher, Buttons
import rclpy


class WebCamCapture(QThread):
    ImageUpdate = pyqtSignal(QImage)

    def __init__(self, capture_device=2):
        super().__init__()
        print("initialised!")
        self.usb_webcam_capture = cv2.VideoCapture(capture_device)
        # Webcam image initialised at startup
        self.image_size = None

    def run(self):
        self.ThreadActive = True

        while self.ThreadActive:
            ret, frame = self.usb_webcam_capture.read()
            if ret:
                if self.image_size is None:
                    self.image_size = frame.shape

                image = cv2.flip(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 1)

                # print(self.min_x, self.min_y, self.max_x, self.max_y)

                ConvertToQtFormat = QImage(
                    image.data,
                    image.shape[1],
                    image.shape[0],
                    QImage.Format_RGB888,
                )
                pic = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(pic)


class VideoStreamWindow(QWidget):
    def __init__(self, window_click_callback):
        super(VideoStreamWindow, self).__init__()

        self.VBL = QVBoxLayout()

        self.computer_camera_thread = WebCamCapture(1)
        self.usb_camera_thread = WebCamCapture(2)

        self.camera_threads = cycle(
            [self.computer_camera_thread, self.usb_camera_thread]
        )

        self.current_camera_thread = next(self.camera_threads)

        self.FeedLabel = ClickableWindow(window_click_func=window_click_callback)
        self.VBL.addWidget(self.FeedLabel)
        self.FeedLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.usb_camera_thread.start()
        self.computer_camera_thread.start()
        self.current_camera_thread.ImageUpdate.connect(self.ImageUpdateSlot)
        self.setLayout(self.VBL)
        # self.add_arrows()

    def ImageUpdateSlot(self, Image):
        self.FeedLabel.setPixmap(QPixmap.fromImage(Image))

    def CancelFeed(self):
        self.Worker1.stop()

    def swap_cams(self):
        self.current_camera_thread.ImageUpdate.disconnect(self.ImageUpdateSlot)
        self.current_camera_thread = next(self.camera_threads)
        self.current_camera_thread.ImageUpdate.connect(self.ImageUpdateSlot)

    def run(self):
        self.ThreadActive = True
        # Need to abstract this code out so it can be replaced easily.
        while self.ThreadActive:
            ret, frame = self.capture.read()

            if ret:
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                min_x = self.min_x
                max_x = self.min_x + self.x_size
                min_y = self.min_y
                max_y = self.min_y + self.y_size

                image_cropped = image[min_y:max_y, min_x:max_x]
                flipped_image = cv2.flip(image_cropped, 1)

                ConvertToQtFormat = QImage(
                    flipped_image.data,
                    flipped_image.shape[1],
                    flipped_image.shape[0],
                    QImage.Format_RGB888,
                )
                Pic = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(Pic)

    def stop(self):
        self.ThreadActive = False
        self.quit()


class MainWindow(QWidget):
    def __init__(self, window_click_callback):
        super().__init__()

        self.setWindowTitle("Video Stream")
        self.setGeometry(100, 100, 740, 580)

        # Create layout for this widget
        layout = QVBoxLayout(self)

        # Add the video stream to the layout
        self.video_widget = VideoStreamWindow(window_click_callback)
        layout.addWidget(self.video_widget)

        # Add button to the layout
        self.button = QPushButton("Click Me")
        self.button.clicked.connect(self.video_widget.swap_cams)
        layout.addWidget(self.button)

        self.show()


if __name__ == "__main__":
    rclpy.init()
    control_node = ControllerPublisher()
    App = QApplication(sys.argv)
    Root = MainWindow(control_node.callback)
    Root.show()
    sys.exit(App.exec())
