#!/usr/bin/env python3

import os
# Remove OpenCV's Qt plugin path to avoid conflicts
if 'QT_QPA_PLATFORM_PLUGIN_PATH' in os.environ:
    del os.environ['QT_QPA_PLATFORM_PLUGIN_PATH']

import sys
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

from createAruco import create_aruco_border_tags, add_aruco_tag_to_image
from ConfigHelperFunctions import load_aruco_config, load_detector_config

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


class CameraViewer(QMainWindow):
    image_updated = pyqtSignal(object)  # Signal to update image display
    
    def __init__(self):
        super().__init__()
        self.aruco_params = load_aruco_config("/root/ws/DiegeticGazeControl/src/basic_aruco_detection/screenDetector/src/aruco_codes.yaml")
        self.aruco_tags = create_aruco_border_tags(**self.aruco_params)
        self.setWindowTitle("Camera Feed Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize ROS
        rclpy.init()
        self.node = Node('camera_viewer')
        self.bridge = CvBridge()
        
        # Setup UI
        self.setup_ui()
        
        # Setup ROS subscriber
        self.image_subscriber = self.node.create_subscription(
            Image,
            'camera/image_raw',
            self.image_callback,
            10
        )
        
        # Setup ROS timer
        self.ros_timer = QTimer()
        self.ros_timer.timeout.connect(self.spin_ros)
        self.ros_timer.start(10)  # 100 Hz
        
        # Connect signal to slot
        self.image_updated.connect(self.update_display)
        
        self.node.get_logger().info('Camera Viewer started - waiting for images on /camera/image_raw')
        
    def setup_ui(self):
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create image display label
        self.image_label = QLabel()
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setStyleSheet("background-color: #f5f5f5; border: 1px solid #d0d0d0;")
        self.image_label.setText("Waiting for camera feed...")
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # Set the main window background to match
        self.setStyleSheet("QMainWindow { background-color: #f5f5f5; }")
        central_widget.setStyleSheet("background-color: #f5f5f5;")
        
        layout.addWidget(self.image_label)
        central_widget.setLayout(layout)
        
    def image_callback(self, msg):
        try:
            # Convert ROS Image to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # Emit signal to update display (thread-safe)
            self.image_updated.emit(cv_image)
            
        except Exception as e:
            self.node.get_logger().error(f'Error processing image: {str(e)}')
    
    def update_display(self, cv_image):
        """Update the QLabel with the new image"""
        try:
            # Convert BGR to RGB for Qt
            cv_image = add_aruco_tag_to_image(cv_image, self.aruco_tags)
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            # Get image dimensions
            height, width, channel = rgb_image.shape
            bytes_per_line = 3 * width
            
            # Create QImage
            q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Scale image to fit label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(self.image_label.size(), 
                                        Qt.KeepAspectRatio,
                                        Qt.SmoothTransformation)
            
            # Update label
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.node.get_logger().error(f'Error updating display: {str(e)}')
    
    def spin_ros(self):
        """Spin ROS node to process callbacks"""
        try:
            rclpy.spin_once(self.node, timeout_sec=0.001)
        except Exception as e:
            self.node.get_logger().error(f'Error spinning ROS: {str(e)}')
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.ros_timer.stop()
        self.node.destroy_node()
        rclpy.shutdown()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    viewer = CameraViewer()
    viewer.show()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
