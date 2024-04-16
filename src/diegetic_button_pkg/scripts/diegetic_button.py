#! /usr/bin/env python3

# Base functions
import rclpy
from rclpy.node import Node

# Import/Publish Fiducial messages
from fiducials.msg import Fiducial
from fiducials.msg import FiducialArray
from fiducials.msg import FiducialTransform
from fiducials.msg import FiducialTransformArray

from geometry_msgs.msg import Transform
from geometry_msgs.msg import PoseArray, Pose

# Publish messages
from diegetic_button_pkg.msg import DiegeticButton
from diegetic_button_pkg.msg import DiegeticButtonArray

# Aruco
from cv2 import aruco
from cv2 import drawFrameAxes
from cv2 import projectPoints
from cv2 import Rodrigues

import tf_transformations as tf

import numpy as np

# Button calculation mode
# TODO: To enumerator
button_center_finding_mode = "inverse_quintic"
# average, inverse_square, inverse_cubic, first_found, closest

# TODO: Expose and move to launch file
button_map_path = "src/diegetic_button_pkg/button_maps/ButtonMap - O-Joy V2.csv"
# button_map_path = "src/diegetic_button_pkg/button_maps/AxiomMap - AxiomMap.csv"
# button_map_path = "src/diegetic_button_pkg/button_maps/ButtonMap - A3Piano.csv"


# Class for diegetic buttons. #
# It defines the 3D bounding box of a button relative to one or more markers
class diegeticButton:  # Inherits from FiducialTransformArray?
    def __init__(self, id, bounding_box, size=140):
        self.id = id  # UNIQUE id for button
        # Array with 4 corners from center [x0,y0,x1,y1]
        self.bounding_box = bounding_box
        # Dictionary of parent ID and their relative Transforms {"id",[x,y,z,q1,q2,q3,q4]}
        self.marker_parents = {}
        self.active_parents = []
        self.parent_pos = Transform()
        self.pos_2d = [0, 0]

    def __str__(self):
        self.get_logger().info("ID: %s." % self.id)
        self.get_logger().info("Bounding Box: {}.".format(self.bounding_box))
        self.get_logger().info("Marker parents: {}.".format(self.marker_parents))


class diegeticButtonPublisher(Node):
    ##### Init function #####
    def __init__(self):
        # Base node init
        super().__init__("diegetic_button_pubsub_node")
        self.get_logger().info("Diegetic Button Node is Running...")

        # Load button data
        self.button_dictionary = self.load_diegetic_button_data()

        # Subscribe to 3D position of markers
        self.subscriber_fiducial_transform = self.create_subscription(
            FiducialTransformArray,
            "/fiducial_transforms",
            self.get_diegetic_button_frames,
            1,
        )

        # Publishers
        self.publisher_button_transforms = self.create_publisher(
            DiegeticButtonArray, "/button_transforms", 1
        )

        # Publish information of found diegetic buttons

    ##### Loading function #####
    # Every  fiducial marker (or collection of markers) will have the coordinates of a button associated with it
    # loaded from an external file. Load into its class and store in a dictionary

    def load_diegetic_button_data(self):
        button_dictionary = {}  # key is the button id
        self.get_logger().info("Loading marker to button map...")

        with open(button_map_path) as file:
            lines = file.readlines()
            for line in lines[1:]:
                parts = line.split(",")

                b_id = str((parts[0]))

                # Create a new button with bounding box, then add to dictionary
                if b_id not in button_dictionary:
                    bounding_box = [
                        float(parts[1]) / 1000,
                        float(parts[2]) / 1000,
                        float(parts[3]) / 1000,
                        float(parts[4]) / 1000,
                    ]
                    button = diegeticButton(b_id, bounding_box)
                    button_dictionary[b_id] = button

                    self.get_logger().info("Creating new button with ID: " + str(b_id))

                # Add marker transform relative to button
                parent_id = int(parts[5])
                parent_transform = [-float(i) / 1000 for i in parts[6:12]]  # mm
                button_dictionary[b_id].marker_parents[parent_id] = parent_transform

        self.get_logger().info(
            "Loaded data for " + str(len(button_dictionary)) + " Buttons"
        )
        self.get_logger().info(str(button_dictionary.keys()))
        return button_dictionary

    ##### Callback function #####
    def get_diegetic_button_frames(self, fiducial_transform_array_msg):
        start_time = self.get_clock().now()

        # Unpack message
        # self.get_logger().info("Recieved ",  len(fiducial_transform_array_msg.transforms), "markers")

        # TODO: Clear button parents beforehand??

        # Build list of recognized buttons, and set active parents on buttons
        # TODO: replace by dictionary?
        active_button_list = []
        active_button_list_ids = []

        # TODO: to function

        ## ? Unpack message into buttons lists
        # Return filled lists -> should be a dict

        for (
            fiducial_transform
        ) in fiducial_transform_array_msg.transforms:  # transform = Fiducial transform
            # self.get_logger().info(" This id ", fiducial_transform.fiducial_id)

            # If the marker has an associated button...
            for b_id, button in self.button_dictionary.items():
                if fiducial_transform.fiducial_id in button.marker_parents.keys():
                    # self.get_logger().info(f"Marker has ID of {fiducial_transform.fiducial_id} and button of {button.marker_parents.keys()}")

                    # ...Add as active for this iteration...
                    button.active_parents.append(fiducial_transform)

                    # ... and if its not yet on the button list, append
                    if button.id not in active_button_list_ids:
                        # self.get_logger().info(f"Button has id of {button.id} and list has {active_button_list_ids}")
                        active_button_list.append(button)
                        active_button_list_ids.append(button.id)

        # self.get_logger().info(f"Found buttons with ids {active_button_list_ids}")

        ### Find candidate positions for each button ###
        # TODO: Wrap into function, allow different solving modes
        # List has been built and buttons have array with their active parents
        # Iterate through parents and get avg position for transform

        DiegeticButtonArrayMsg = DiegeticButtonArray()
        DiegeticButtonArrayMsg.header.stamp = self.get_clock().now().to_msg()
        DiegeticButtonArrayMsg.header.frame_id = "button_transform"

        for button in active_button_list:
            # Init message
            diegetic_button_msg = DiegeticButton()
            DiegeticButtonArrayMsg.buttons.append(diegetic_button_msg)
            diegetic_button_msg.button_id = button.id

            # Set bounding box
            diegetic_button_msg.x0 = button.bounding_box[0]
            diegetic_button_msg.y0 = button.bounding_box[1]
            diegetic_button_msg.x1 = button.bounding_box[2]
            diegetic_button_msg.y1 = button.bounding_box[3]

            # Initialize pos/rot candidates
            pos_candidates = []
            rot_candidates = []
            total_weight = 0

            # Get the button position respect to each parent transform
            for parent_marker in button.active_parents:
                # Compose from relative to parent to relative to camera

                # Position of button respect from parent.
                local_transform = button.marker_parents[parent_marker.fiducial_id][0:3]
                # skipping rotation for now
                # TODO: implement local rotation
                local_mat = tf.translation_matrix(local_transform)
                # self.get_logger().info("Local matrix: \n" + str(local_mat))

                # Position of parent respect from camera.
                parent_transform = [
                    parent_marker.transform.translation.x,
                    parent_marker.transform.translation.y,
                    parent_marker.transform.translation.z,
                ]
                parent_rot = [
                    parent_marker.transform.rotation.x,
                    parent_marker.transform.rotation.y,
                    parent_marker.transform.rotation.z,
                    parent_marker.transform.rotation.w,
                ]
                parent_rot = tf.quaternion_matrix(parent_rot)

                # Get matrix of parent to camera
                parent_mat = np.matmul(
                    tf.translation_matrix(parent_transform), parent_rot
                )
                # log the matrix with 2 decimals

                # self.get_logger().info("Marker matrix: \n" + str(parent_mat))

                # Final matrix with complete transformation from camera
                button_to_camera = np.matmul(parent_mat, local_mat)
                """
                self.get_logger().info(
                    "Final button matrix: \n"
                    + str(np.around(button_to_camera, decimals=2))
                )
                """
                # Send message
                quat = tf.quaternion_from_matrix(button_to_camera)

                # diegetic_button_msg.button_transform = parent_marker.transform
                # ...append here and then avg and cast?

                pos_candidates.append(
                    [
                        button_to_camera[0, 3],
                        button_to_camera[1, 3],
                        button_to_camera[2, 3],
                    ]
                )

                # Weight calculation mode
                if button_center_finding_mode == "inverse_square":
                    # local_transform = button.marker_parents[parent_marker.fiducial_id][0:3]

                    weight = np.linalg.norm(local_transform) ** -2
                elif button_center_finding_mode == "inverse_cubic":
                    # local_transform = button.marker_parents[parent_marker.fiducial_id][0:3]

                    weight = np.linalg.norm(local_transform) ** -3
                elif button_center_finding_mode == "inverse_quintic":
                    # local_transform = button.marker_parents[parent_marker.fiducial_id][0:3]

                    weight = np.linalg.norm(local_transform) ** -5

                elif button_center_finding_mode == "first_found":
                    if total_weight == 0:
                        weight = 1
                    else:
                        weight = 0
                elif button_center_finding_mode == "average":
                    weight = 1
                else:
                    weight = 1
                # self.get_logger().info(f"Pos candidates {pos_candidates[-1]}")

                # pos_candidates[-1] = pos_candidates[-1]*weight
                pos_candidates[-1] = [
                    element * weight for element in pos_candidates[-1]
                ]

                total_weight += weight

                if quat[0] < 0:
                    rot_candidates.append([-quat[0], -quat[1], -quat[2], -quat[3]])
                else:
                    rot_candidates.append([quat[0], quat[1], quat[2], quat[3]])

                # TODO: Leaving multiple parents for later
                # break

            # Simply average candidates to get a more accurate answer
            final_pos = np.sum(pos_candidates, axis=0) / total_weight

            # Lowish accuracy fast method
            # self.get_logger().info(f"rot candidates: {rot_candidates}")
            final_rot = np.average(rot_candidates, axis=0)
            final_rot = final_rot / np.linalg.norm(final_rot)
            # self.get_logger().info(f"Final rot: {final_rot}")

            diegetic_button_msg.button_transform.translation.x = final_pos[0]
            diegetic_button_msg.button_transform.translation.y = final_pos[1]
            diegetic_button_msg.button_transform.translation.z = final_pos[2]
            diegetic_button_msg.button_transform.rotation.x = final_rot[0]
            diegetic_button_msg.button_transform.rotation.y = final_rot[1]
            diegetic_button_msg.button_transform.rotation.z = final_rot[2]
            diegetic_button_msg.button_transform.rotation.w = final_rot[3]

            # convert to matrix and log
            final_mat = tf.quaternion_matrix(final_rot)
            final_mat[0, 3] = final_pos[0]
            final_mat[1, 3] = final_pos[1]
            final_mat[2, 3] = final_pos[2]

            """self.get_logger().info(
                "Final button matrix for button "
                + str(button.id)
                + ": \n"
                + str(np.around(final_mat, decimals=5))
            )"""

        # ? Sends message
        # DiegeticButtonArrayMsg.header.stamp = fiducial_transform_array_msg.header.stamp

        # self.get_logger().info(f"Sending message with {len(active_button_list)} buttons")
        self.publisher_button_transforms.publish(DiegeticButtonArrayMsg)

        end_time = self.get_clock().now()

        # Clear active markers
        for b_id, button in self.button_dictionary.items():
            button.active_parents = []

        pass


def main():
    rclpy.init()  # Initialize ROS DDS
    diegetic_button_publisher = diegeticButtonPublisher()  # Create instance of function

    try:
        # prevents closure. Run until interrupt
        rclpy.spin(diegetic_button_publisher)
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        diegetic_button_publisher.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == "__main__":
    main()
