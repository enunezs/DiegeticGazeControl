#!/usr/bin/env python3

# To run
"""
ros2 run fiducials aruco_detect.py --ros-args --params-file config/params.yaml
"""

# ! IMPORTANT: CHANGED FROM RODRIGUES TO QUATERNIONS

# Core ROS dependencies
import rclpy
from rclpy.node import Node

# Standard library imports
from math import sqrt
import numpy as np

# Third-party imports
from cv2 import (
    aruco,
    destroyAllWindows,
    drawFrameAxes,
    Rodrigues,
    undistort,
    fisheye,
    remap,
)
import cv2
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image
from tf_transformations import quaternion_from_matrix

# from scipy.spatial.transform import Rotation

# Local application imports
from fiducials.msg import (
    Fiducial,
    FiducialArray,
    FiducialTransform,
    FiducialTransformArray,
)
from geometry_msgs.msg import Transform

# Initialize constants
PUBLISH_DRAWN_MARKER = True
MARKER_LENGTH = 0.035  # meters


class arucoPublisher(Node):
    def __init__(self):
        super().__init__("aruco_detect")

        # Aruco parameters
        # Use https://chev.me/arucogen/ to make the markers
        aruco_dict = aruco.DICT_4X4_250  # TODO: Restrict dictionary number later
        self.arucoDict = aruco.Dictionary_get(aruco_dict)
        self.arucoParams = aruco.DetectorParameters_create()

        # CV Bridge for image conversion
        self.bridge = CvBridge()

        # Load camera intrinsics
        self.load_camera_intrinsics()

        # Load other parameters
        self.camera_topic = self.declare_and_get_parameter(
            "front_camera_subscription", "pupil_glasses/front_camera"
        )
        self.publish_drawn_marker = self.declare_and_get_parameter(
            "publish_drawn_marker", PUBLISH_DRAWN_MARKER
        )
        self.marker_length = self.declare_and_get_parameter(
            "marker_length", MARKER_LENGTH
        )
        self.aruco_dict = self.declare_and_get_parameter("aruco_dict", aruco_dict)

        # Subscribers
        self.subscriber_camera_images = self.create_subscription(
            Image, self.camera_topic, self.detect_aruco_markers, 3
        )

        # Publishers
        self.publisher_marker_vertices = self.create_publisher(
            FiducialArray, "/fiducial_vertices", 1
        )
        self.publisher_marker_tranforms = self.create_publisher(
            FiducialTransformArray, "/fiducial_transforms", 1
        )
        self.publisher_drawn_markers = self.create_publisher(
            Image, "/fiducial_images", 1
        )

        self.new_camera_matrix = None

    def load_camera_intrinsics(self):
        self.get_logger().info("Loading camera intrinsics...")

        # Camera matrix
        camera_matrix_default = [
            887.79147665,
            0.0,
            809.32877594,
            0.0,
            887.14056667,
            614.39688332,
            0.0,
            0.0,
            1.0,
        ]
        self.declare_parameter("camera_matrix", camera_matrix_default)
        self.camera_matrix = np.array(
            self.get_parameter("camera_matrix").get_parameter_value().double_array_value
        ).reshape(3, 3)

        self.get_logger().info("Camera Matrix: %s" % self.camera_matrix)

        # Distortion coefficients
        dist_coeffs_default = [
            -1.28152845e-01,
            1.06973881e-01,
            -1.50877076e-05,
            -9.10823342e-04,
            2.62431778e-03,
            1.69108143e-01,
            5.02584562e-02,
            2.94127262e-02,
        ]

        self.declare_parameter("dist_coeffs", dist_coeffs_default)
        self.dist_coeffs = np.array(
            self.get_parameter("dist_coeffs").get_parameter_value().double_array_value
        ).reshape((8, 1))

        self.declare_parameter("camera_alpha", 0.5)
        self.camera_alpha = (
            self.get_parameter("camera_alpha").get_parameter_value().double_value
        )

        self.get_logger().info("Distortion Coefficients: %s" % self.dist_coeffs)

        self.get_logger().info("Camera intrinsics loaded")

    def declare_and_get_parameter(self, name, default):
        self.declare_parameter(name, default)
        self.get_logger().info(
            f"Loaded parameter {name}: {self.get_parameter(name).value}"
        )
        return self.get_parameter(name).value

    def detect_aruco_markers(self, img_msg):
        # * Unpack message, get image
        img = self.bridge.imgmsg_to_cv2(img_msg)

        # Find new camera matrix
        if self.new_camera_matrix is None:
            """self.new_camera_matrix, self.roi = cv2.getOptimalNewCameraMatrix(
                self.camera_matrix,
                self.dist_coeffs,
                (img.shape[1], img.shape[0]),
                self.camera_alpha,
                (img.shape[1], img.shape[0]),
                centerPrincipalPoint=1,
            )"""
            self.new_camera_matrix = self.camera_matrix
            self.get_logger().info("New camera matrix: %s" % self.new_camera_matrix)

        # self.get_logger().info(f"Min: {np.min(img)}, Max: {np.max(img)}")

        ### ! Undistort image with base cv2 method
        # self.get_logger().info("Undistorting image")

        """img = undistort(
            img, self.camera_matrix, self.dist_coeffs, None, self.new_camera_matrix
        )"""

        # x, y, w, h = self.roi
        # img = img[y : y + h, x : x + w]

        ### * 2D * ###
        # Perform marker detection
        (corners, ids, rejected) = aruco.detectMarkers(
            img,
            self.arucoDict,
            parameters=self.arucoParams,
            cameraMatrix=self.new_camera_matrix,
        )

        # Pack fiducial data into messages
        fiducialArrayMsg = self.pack_fiducial_array_msg(corners, ids)
        fiducialArrayMsg.header.stamp = self.get_clock().now().to_msg()
        self.publisher_marker_vertices.publish(fiducialArrayMsg)

        ### * 3D * ###
        # Pose estimation
        (rvecs, tvecs, _objPoints) = aruco.estimatePoseSingleMarkers(
            corners, self.marker_length, self.new_camera_matrix, self.dist_coeffs
        )

        # Pack message
        fiducialTransformArrayMsg = self.pack_fiducial_transform_array_msg(
            ids, rvecs, tvecs
        )
        fiducialTransformArrayMsg.header.stamp = self.get_clock().now().to_msg()
        self.publisher_marker_tranforms.publish(fiducialTransformArrayMsg)

        # Draw markers and send
        draw_and_send_markers = (
            self.get_parameter("publish_drawn_marker").get_parameter_value().bool_value
        )
        if draw_and_send_markers:
            if ids is not None:
                # Draw borders
                img = aruco.drawDetectedMarkers(
                    img, corners, ids, borderColor=(255, 0, 0)
                )
                for i in range(len(rvecs)):
                    img = drawFrameAxes(
                        img,
                        self.new_camera_matrix,
                        self.dist_coeffs,
                        rvecs[i],
                        tvecs[i],
                        self.marker_length / 2,
                    )
            # Pack and send
            imgmsg = self.bridge.cv2_to_imgmsg(img, encoding="bgr8")
            imgmsg.header.stamp = self.get_clock().now().to_msg()
            imgmsg.header.frame_id = "markers detected"

            self.publisher_drawn_markers.publish(imgmsg)  # Publish the message
            # self.get_logger().info("Drawn markers published")

        end_time = self.get_clock().now()
        # self.get_logger().info( f"Aruco processing time is {(end_time - start_time).nanoseconds*0.000000001}")

    def pack_fiducial_array_msg(self, corners, ids):
        # Make instance of message with fiducials
        fiducialArrayMsg = FiducialArray()
        fiducialArrayMsg.header.stamp = self.get_clock().now().to_msg()
        fiducialArrayMsg.header.frame_id = "fiducial_detection"

        if ids is not None:
            for i in range(len(ids)):
                fiducialMsg = Fiducial()
                fiducialMsg.fiducial_id = int(ids[i, 0])

                # corner 0
                fiducialMsg.x0 = float(corners[i][0, 0, 0])
                fiducialMsg.y0 = float(corners[i][0, 0, 1])
                # corner 1
                fiducialMsg.x1 = float(corners[i][0, 1, 0])
                fiducialMsg.y1 = float(corners[i][0, 1, 1])
                # corner 2
                fiducialMsg.x2 = float(corners[i][0, 2, 0])
                fiducialMsg.y2 = float(corners[i][0, 2, 1])
                # corner 3
                fiducialMsg.x3 = float(corners[i][0, 3, 0])
                fiducialMsg.y3 = float(corners[i][0, 3, 1])

                fiducialArrayMsg.fiducials.append(fiducialMsg)

            # self.get_logger().info("%i markers found, sending message" % len(ids))
        else:
            pass
            # self.get_logger().info("No markers found, sending empty message")

        return fiducialArrayMsg

    def pack_fiducial_transform_array_msg(self, ids, rvecs, tvecs):
        def rotation_matrix_to_quaternion(m):
            tr = m[0][0] + m[1][1] + m[2][2]
            if tr > 0:
                S = sqrt(tr + 1.0) * 2
                qw = 0.25 * S
                qx = (m[2][1] - m[1][2]) / S
                qy = (m[0][2] - m[2][0]) / S
                qz = (m[1][0] - m[0][1]) / S
            elif (m[0][0] > m[1][1]) and (m[0][0] > m[2][2]):
                S = sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
                qw = (m[2][1] - m[1][2]) / S
                qx = 0.25 * S
                qy = (m[0][1] + m[1][0]) / S
                qz = (m[0][2] + m[2][0]) / S
            elif m[1][1] > m[2][2]:
                S = sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
                qw = (m[0][2] - m[2][0]) / S
                qx = (m[0][1] + m[1][0]) / S
                qy = 0.25 * S
                qz = (m[1][2] + m[2][1]) / S
            else:
                S = sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
                qw = (m[1][0] - m[0][1]) / S
                qx = (m[0][2] + m[2][0]) / S
                qy = (m[1][2] + m[2][1]) / S
                qz = 0.25 * S
            return [qx, qy, qz, qw]

        # Make instance of message with fiducial array
        fiducialTransformArrayMsg = FiducialTransformArray()
        fiducialTransformArrayMsg.header.stamp = self.get_clock().now().to_msg()
        fiducialTransformArrayMsg.header.frame_id = "fiducial_transform"

        # TODO: Unoptimized, change as much as possible with numpy stuff
        # Likely the problem then

        # TODO to function
        if rvecs is not None:
            for i in range(len(rvecs)):
                fiducialTransformMsg = FiducialTransform()
                # ID ...
                fiducialTransformMsg.fiducial_id = int(ids[i, 0])

                # Transform
                fiducialTransformMsg.transform.translation.x = tvecs[i, 0, 0]
                fiducialTransformMsg.transform.translation.y = tvecs[i, 0, 1]
                fiducialTransformMsg.transform.translation.z = tvecs[i, 0, 2]

                # Cv2 returns Rodrigues, convert to matrix
                rmat, _ = Rodrigues(rvecs[i, 0])

                # Convert the rotation matrix to a quaternion
                q = rotation_matrix_to_quaternion(rmat)
                # TODO: Replace by library implementation
                # q = quaternion_from_matrix(rmat)

                fiducialTransformMsg.transform.rotation.x = q[0]
                fiducialTransformMsg.transform.rotation.y = q[1]
                fiducialTransformMsg.transform.rotation.z = q[2]
                fiducialTransformMsg.transform.rotation.w = q[3]

                fiducialTransformArrayMsg.transforms.append(fiducialTransformMsg)
                # self.get_logger().info("Fiducial transform message sent")
                """
                q = quaternion_from_matrix(mat)
                #q = quaternion_from_euler(rvecs[i, 0, 0], rvecs[i, 0, 1], rvecs[i, 0, 2], axes='sxyz')
                fiducialTransformMsg.transform.rotation.x = q[0]
                fiducialTransformMsg.transform.rotation.y = q[1]
                fiducialTransformMsg.transform.rotation.z = q[2]
                fiducialTransformMsg.transform.rotation.w = q[3]
                """

                # Just for now, sending rodrigues
                """
                fiducialTransformMsg.transform.rotation.x = rvecs[i, 0][0]
                fiducialTransformMsg.transform.rotation.y = rvecs[i, 0][1]
                fiducialTransformMsg.transform.rotation.z = rvecs[i, 0][2]
                fiducialTransformMsg.transform.rotation.w = 1234.0
                """

        return fiducialTransformArrayMsg


def main():
    rclpy.init()  # Initialize ROS DDS
    aruco_publisher = arucoPublisher()
    print("Aruco Detection Publisher Node is Running...")

    try:
        rclpy.spin(aruco_publisher)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        destroyAllWindows()
        aruco_publisher.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == "__main__":
    main()
