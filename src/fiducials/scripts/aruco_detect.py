#!/usr/bin/env python3

# To run
"""
ros2 run fiducials aruco_detect.py --ros-args --params-file config/params.yaml
"""

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
)
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image

# Local application imports
from fiducials.msg import (
    Fiducial,
    FiducialArray,
    FiducialTransform,
    FiducialTransformArray,
)


class arucoPublisher(Node):
    def __init__(self):
        super().__init__("aruco_detect")

        ### * Initialize variables
        # to store camera intrinsics
        self.camera_matrix = None
        self.dist_coeffs = None
        # CV Bridge for image conversion
        self.bridge = CvBridge()

        ### * Load parameters
        self.camera_img_topic = self.declare_and_get_parameter(
            "front_camera_image", "pupil_glasses/front_camera/image_color"
        )
        self.camera_info_topic = self.declare_and_get_parameter(
            "front_camera_params", "pupil_glasses/front_camera/camera_info"
        )
        self.publish_drawn_marker = self.declare_and_get_parameter(
            "publish_drawn_marker", True
        )
        self.marker_length = self.declare_and_get_parameter(
            "marker_length", 0.035  # meters
        )

        # Aruco dictionary
        # Use https://chev.me/arucogen/ to make the markers
        aruco_dict = aruco.DICT_4X4_100
        # Other params at https://docs.opencv.org/3.4/d9/d6a/group__aruco.html
        self.aruco_dict = self.declare_and_get_parameter("aruco_dict", aruco_dict)
        self.aruco_dict = aruco_dict

        self.arucoDict = aruco.Dictionary_get(aruco_dict)
        self.arucoParams = aruco.DetectorParameters_create()

        ### * Subscribers
        self.subscriber_camera_images = self.create_subscription(
            Image, self.camera_img_topic, self.detect_aruco_markers, 3
        )
        self.subscriber_camera_info = self.create_subscription(
            CameraInfo,
            self.camera_info_topic,
            self.camera_info_callback,
            10,
        )

        ### * Publishers
        self.publisher_marker_vertices = self.create_publisher(
            FiducialArray, "/fiducial_vertices", 1
        )
        self.publisher_marker_tranforms = self.create_publisher(
            FiducialTransformArray, "/fiducial_transforms", 1
        )
        self.publisher_drawn_markers = self.create_publisher(
            Image, "/fiducial_images", 1
        )

        self.new_camera_matrix = None  ### ! ?????

    def camera_info_callback(self, msg):
        if self.camera_matrix is None:  # Only set once to avoid unnecessary computation
            # Convert camera info into usable format for OpenCV
            self.camera_matrix = np.array(msg.k).reshape(3, 3)
            self.dist_coeffs = np.array(msg.d)
            self.get_logger().info("Camera intrinsics loaded")

    def declare_and_get_parameter(self, name, default):
        self.declare_parameter(name, default)
        self.get_logger().info(
            f"Loaded parameter {name}: {self.get_parameter(name).value}"
        )
        return self.get_parameter(name).value

    def detect_aruco_markers(self, img_msg):

        if self.camera_matrix is None or self.dist_coeffs is None:
            self.get_logger().warn("Camera intrinsics not yet received.")
            return

        # * Unpack message, get image
        img = self.bridge.imgmsg_to_cv2(img_msg)

        # Find new camera matrix
        if self.new_camera_matrix is None:
            self.new_camera_matrix = self.camera_matrix
            self.get_logger().info("New camera matrix: %s" % self.new_camera_matrix)

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

        # TODO: Unoptimized, update to numpy

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
