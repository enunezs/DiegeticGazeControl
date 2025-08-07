from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from components import ClickableLabel

import cv2
from itertools import cycle
import numpy as np

class ImageThread(QThread):
    ImageUpdate = pyqtSignal(QImage)

    def __init__(self, video_source=0):
        super().__init__()
        print("initialising Thread!")
        self.capture = cv2.VideoCapture(video_source)

        # Webcam image initialised at startup
        self.image_size = None

    def run(self):
        self.ThreadActive = True

        while self.ThreadActive:
            ret, frame = self.capture.read()
            if not ret:
                raise ValueError("Theres an issue with the webcam!")
            if ret:
                if self.image_size is None:
                    self.image_size = frame.shape

                image = image = cv2.flip(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 1)

                # print(self.min_x, self.min_y, self.max_x, self.max_y)

                ConvertToQtFormat = QImage(
                    image.data,
                    image.shape[1],
                    image.shape[0],
                    QImage.Format_RGB888,
                )
                pic = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(pic)

    def rotation_mode_click(self):
        self.rotation_mode_callback(self.current_mouse_position)
        print(f"ROT msg : {self.current_mouse_position}")
        """Handle clicks in hand pose control mode"""

    def window_rotation_callback(self, x_axis, y_axis):
        print("Window Rotation func called!")

    def window_translation_callback(self, x_axis, y_axis):
        print("Window Rotation func called!")

    def find_mouse_position_from_event(self, event):
        position = np.array((event.pos().x(), event.pos().y()))
        size = np.array((self.width(), self.height()))
        normalised_position = position * 2 / size - 1
        self.current_mouse_position = normalised_position
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


class VideoStreamWindow(QWidget):
    def __init__(self, translation_callback, rotation_callback, camera_threads):
        super().__init__()
        self.setMouseTracking(True)
        self.VBL = QVBoxLayout()
        self.mouse_pressed = False
        
        # Create the clickable feed label with the callback
        self.video_feed = ClickableLabel(translation_callback, rotation_callback)

        self.video_feed.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.VBL.addWidget(self.video_feed)
        
        # Store camera threads and create an iterator
        self.camera_threads = camera_threads
        self.camera_thread_iterator = cycle(self.camera_threads)
        
        # Start with the first camera thread
        self.current_camera_thread = next(self.camera_thread_iterator)
        self.current_camera_thread.start()
        self.current_camera_thread.ImageUpdate.connect(self.image_update_slot)
        
        self.setLayout(self.VBL)
    
    def image_update_slot(self, image):
        """Update the video feed with the new image"""
        pixmap = QPixmap.fromImage(image)
        self.video_feed.setPixmap(pixmap)
    
    def switch_camera(self):
        """Switch to the next camera in the iterator"""
        # Disconnect the current camera thread
        self.current_camera_thread.disconnect()
        
        # Get the next camera thread from the iterator
        self.current_camera_thread = next(self.camera_thread_iterator)
        
        # Connect the new thread to the image update slot
        self.current_camera_thread.ImageUpdate.connect(self.image_update_slot)
        
        # Start the new camera thread
        self.current_camera_thread.start()
    
    def add_camera_thread(self, camera_thread):
        """Add a new camera thread to the list"""
        self.camera_threads.append(camera_thread)
        # Recreate the iterator with the updated list
        self.camera_thread_iterator = cycle(self.camera_threads)
    
    def update_image_click_func(self, mode):
        """Update the video feed's click behavior based on current mode"""
        video_window_timer = self.video_feed.timer
        
        try:
            video_window_timer.timeout.disconnect()
        except TypeError:
            pass
        
        if mode == 0:  # Position control mode
            video_window_timer.timeout.connect(self.video_feed.translation_mode_click)
        elif mode == 1:  # Hand pose control mode
            video_window_timer.timeout.connect(self.video_feed.rotation_mode_click)
    
    def cancel_feed(self):
        """Stop all camera threads"""
        for thread in self.camera_threads:
            thread.stop()


if __name__ == "__main__":
    app = QApplication([])
    thread_2 = ImageThread("/dev/video2")
    window = VideoStreamWindow(lambda x: None, lambda x: None, [thread_2])
    window.show()
    app.exec_()