#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
import numpy as np
import cv2
from enum import Enum
from typing import Dict, List, Tuple, Optional
import tf_transformations as tf


from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped, Transform, Point, Quaternion
from tf2_ros import Buffer, TransformListener
from tf2_ros import StaticTransformBroadcaster
import tf_transformations


from sensor_msgs.msg import CameraInfo
from cv_bridge import CvBridge

# Import ArUco detector messages (adjust import path as needed)
from diegetic_transform_engine.msg import (
    MarkerArray,
    Marker,
)  # Adjust based on your actual message types

# Custom message imports (adjust paths as needed)
from diegetic_transform_engine.msg import DiegeticButton, DiegeticButtonArray
from diegetic_transform_engine.msg import DiegeticButton2D, DiegeticButton2DArray

# TODO:
# Haptics
from std_msgs.msg import String


class ButtonCenterStrategy(Enum):
    """Strategies for combining multiple marker observations of the same button"""

    AVERAGE = "average"
    INVERSE_SQUARE = "inverse_square"
    INVERSE_CUBIC = "inverse_cubic"
    INVERSE_QUINTIC = "inverse_quintic"
    FIRST_FOUND = "first_found"
    CLOSEST = "closest"


class ButtonDefinition:
    """Defines a button's properties and its relationship to markers"""

    def __init__(self, button_id: str, bounding_box: List[float]):
        self.id = button_id
        self.bounding_box = bounding_box  # [x0, y0, x1, y1] in meters
        self.marker_parents: Dict[int, List[float]] = (
            {}
        )  # marker_id -> [x, y, z, rx, ry, rz]

    def add_marker_parent(self, marker_id: int, transform: List[float]):
        """Add a marker parent with its relative transform to this button"""
        self.marker_parents[marker_id] = transform


class ScreenDefinition:
    def __init__(
        self,
        width_m: float = 45 + 7.7,
        height_m: float = 29.7,
        resolution: Tuple[int, int] = (1920, 1080),
        marker_length: float = 0.044,
    ):

        self.dimensions = (width_m, height_m)
        self.resolution = resolution

        self.PX_TO_M = width_m / self.resolution[0]

        self.marker_length = marker_length

        self.marker_ids = [70, 71, 72, 73]  # IDs of the 4 ArUco markers on the screen

        self.marker_names = [
            "SCREEN_TOP_LEFT",
            "SCREEN_TOP_RIGHT",
            "SCREEN_BOTTOM_RIGHT",
            "SCREEN_BOTTOM_LEFT",
        ]
        self.marker_corners = (
            [  # Defined from top-left, clockwise. each has [x,y,z] in meters and id
                [0 - self.marker_length, 0 - self.marker_length, 0],
                [width_m + self.marker_length, 0 - self.marker_length, 0],
                [width_m - self.marker_length, height_m - self.marker_length, 0],
                [0 - self.marker_length, height_m - self.marker_length, 0],
            ]
        )
        # self.marker_corners = {
        #     name: corner for name, corner in zip(self.marker_names, self.marker_corners)
        # }


class DiegeticButtonPublisher(Node):
    """
    ROS2 node that tracks diegetic buttons relative to ArUco markers.

    Subscribes to:
    - /aruco_markers (MarkerArray): Detected ArUco markers
    - /pupil_glasses/front_camera/camera_info (CameraInfo): Camera calibration

    Publishes:
    - /diegetic_buttons_3d (DiegeticButtonArray): 3D button transforms
    - /diegetic_buttons_2d (DiegeticButton2DArray): 2D projected button positions
    - /haptic_feedback_input_string (String): Haptic feedback triggers

    Broadcasts TF transforms for each button
    """

    def __init__(self):
        super().__init__("diegetic_button_publisher")

        # Initialize parameters
        self._declare_parameters()

        # Load button definitions
        self.button_definitions = self._load_button_definitions()
        # Screen
        self.screen_active_buttons: List[DiegeticButton2D] = []
        self.screen_3d_buttons: List[ButtonDefinition] = []

        # Camera calibration data
        self.camera_matrix = None
        self.dist_coeffs = None
        self.camera_info_received = False

        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.static_broadcaster = StaticTransformBroadcaster(self)
        self._publish_static_button_link()

        # CV Bridge for image operations
        self.cv_bridge = CvBridge()

        # Initialize subscribers
        self._setup_subscribers()

        # Initialize publishers
        self._setup_publishers()

        self.get_logger().info("Diegetic Button Publisher initialized")

    def _declare_parameters(self):
        """Declare and retrieve ROS parameters"""
        # Button center finding strategy
        self.declare_parameter("button_center_strategy", "inverse_square")
        strategy_str = self.get_parameter("button_center_strategy").value
        try:
            self.center_strategy = ButtonCenterStrategy(strategy_str)
        except ValueError:
            self.get_logger().warning(
                f"Unknown strategy {strategy_str}, using INVERSE_SQUARE"
            )
            self.center_strategy = ButtonCenterStrategy.INVERSE_SQUARE

        # Button map file path
        self.declare_parameter(
            "button_map_path",
            "src/diegetic_transform_engine/button_maps/ButtonMap - O-Joy V3.csv",
        )
        self.button_map_path = self.get_parameter("button_map_path").value

        # Frame IDs
        self.declare_parameter("camera_frame_id", "camera_optical_frame")
        self.camera_frame_id = self.get_parameter("camera_frame_id").value

        self.declare_parameter("button_frame_id", "button_frame")
        self.button_frame_id = self.get_parameter("button_frame_id").value

        self.get_logger().info(f"Using strategy: {self.center_strategy.value}")
        self.get_logger().info(f"Button map: {self.button_map_path}")

    def _setup_subscribers(self):
        """Setup ROS subscribers"""
        self.marker_subscriber = self.create_subscription(
            MarkerArray, "/aruco_markers", self._marker_callback, 10
        )

        self.camera_info_subscriber = self.create_subscription(
            CameraInfo,
            "/pupil_glasses/front_camera/camera_info",
            self._camera_info_callback,
            10,
        )

        self.screen_button_subscriber = self.create_subscription(
            DiegeticButton2DArray,
            "/screen_buttons",
            self._screen_button_callback,
            10,
        )

    def _setup_publishers(self):
        """Setup ROS publishers"""
        self.button_3d_publisher = self.create_publisher(
            DiegeticButtonArray, "/diegetic_buttons_3d", 10
        )

        self.button_2d_publisher = self.create_publisher(
            DiegeticButton2DArray, "/diegetic_buttons_2d", 10
        )

        self.haptic_publisher = self.create_publisher(
            String, "/haptic_feedback_input_string", 10
        )

    def _load_button_definitions(self) -> Dict[str, ButtonDefinition]:
        """Load button definitions from CSV file"""
        button_definitions = {}

        try:
            with open(self.button_map_path, "r") as file:
                lines = file.readlines()

            for line in lines[1:]:  # Skip header
                parts = [part.strip() for part in line.split(",")]
                if len(parts) < 12:
                    continue

                button_id = str(parts[0])

                # Create button if it doesn't exist
                if button_id not in button_definitions:
                    bounding_box = [
                        float(parts[1]) / 1000,  # Convert mm to m
                        float(parts[2]) / 1000,
                        float(parts[3]) / 1000,
                        float(parts[4]) / 1000,
                    ]
                    button_definitions[button_id] = ButtonDefinition(
                        button_id, bounding_box
                    )

                # Add marker parent relationship
                marker_id = int(parts[5])
                transform = [
                    -float(parts[i]) / 1000 for i in range(6, 12)
                ]  # Convert mm to m, negate
                button_definitions[button_id].add_marker_parent(marker_id, transform)

            self.get_logger().info(
                f"Loaded {len(button_definitions)} button definitions"
            )

        except Exception as e:
            self.get_logger().error(f"Failed to load button map: {e}")

        return button_definitions

    def _camera_info_callback(self, msg: CameraInfo):
        """Process camera calibration info"""
        self.camera_matrix = np.array(msg.k).reshape(3, 3)
        self.dist_coeffs = np.array(msg.d)
        self.camera_info_received = True
        self.image_width = msg.width
        self.image_height = msg.height

        if not hasattr(self, "_camera_info_logged"):
            self.get_logger().info("Camera calibration received", once=True)
            self._camera_info_logged = True

    def _screen_button_callback(self, msg: DiegeticButton2DArray):
        # TODO: Once received, the screen buttons position relative to the screen center will be inmmediately calculated (2D px to 3D m)
        # self.get_logger().info(
        #     f"Received {len(self.screen_active_buttons)} screen buttons"
        # )

        # Save
        self.screen_active_buttons = msg.buttons

        # Now we convert to the new format and 3D, relative to each marker
        self.screen_3d_buttons = []

        # TODO Load from settings
        self.screen = ScreenDefinition(1600, 900)

        for button in self.screen_active_buttons:
            # Define button properties (internal units in meters)
            screen_button = ButtonDefinition(
                button.button_id,
                [  # bounding box [x0, y0, x1, y1] in meters
                    button.x_points[0] * self.screen.PX_TO_M,
                    button.y_points[0] * self.screen.PX_TO_M,
                    button.x_points[2] * self.screen.PX_TO_M,
                    button.y_points[2] * self.screen.PX_TO_M,
                ],
            )

            # Define marker parents (all 4 screen corners)
            for corner_number in range(4):
                marker_id = self.screen.marker_ids[corner_number]

                # Load marker position
                marker_pos = self.screen.marker_corners[corner_number]

                # Compute button center relative to screen top-left in meters
                button_center_x = button.center_x * self.screen.PX_TO_M
                button_center_y = button.center_y * self.screen.PX_TO_M

                # # Offset from marker to button center
                # offset_x = button_center_x - marker_pos[0]
                # offset_y = button_center_y - marker_pos[1]
                # offset_z = 0 - marker_pos[2]  # Assuming screen is at z=0

                # # No rotation offset for now
                # transform = [offset_x, offset_y, offset_z, 0, 0, 0]
                transform = [
                    button_center_x,
                    button_center_y,
                    0,
                    0,
                    0,
                    0,
                ]
                screen_button.add_marker_parent(marker_id, transform)
            self.screen_3d_buttons.append(screen_button)

    ################
    ### Main code ##
    ################
    def _marker_callback(self, msg: MarkerArray):
        """Process detected ArUco markers and compute button positions"""

        if not self.camera_info_received:
            self.get_logger().warn("Camera calibration not yet received, skipping")
            return  # <--- ADD THIS RETURN STATEMENT

        # 1. Capture the EXACT timestamp of the markers (derived from the camera frame)
        # We must use this stamp for everything in this cycle.
        current_frame_stamp = msg.header.stamp

        # 2. Find active buttons based on visible markers
        active_buttons = self._find_active_buttons(msg.markers)

        # 3. Compute 3D positions for CSV-defined buttons
        button_3d_array = self._compute_3d_positions(active_buttons, msg.header)

        ### --- Screen buttons --- ###
        # TODO: If the screen is visible, we load our active markers and append it to the active_buttons list
        # If one of the 4 aruco markers is found, screen is visible
        # if any(marker.id in self.screen_marker_ids for marker in msg.markers):
        #     self.get_logger().debug("Screen is visible")
        #     active_buttons.update(self._find_active_buttons(msg.markers))

        # TODO: Compute the 3D position for the *screen* buttons
        # for button in self.screen_buttons:
        #     button_3d = self._compute_screen_button_3d_position(button)
        #     if button_3d is not None:
        #         self.screen_3d_buttons.append(button_3d)
        # Using the screen buffer, find the 3D positions of buttons on the screen
        ### --- Screen buttons --- ###

        #    # --- INTEGRATION OF SCREEN BUTTONS ---
        #     # 4. If any screen markers are visible, compute 3D positions for buttons currently on screen
        #     # Note: We use the same frame_stamp so gaze-matching works for screen buttons too
        #     visible_marker_ids = [m.id for m in msg.markers]
        #     for screen_btn_def in self.screen_3d_buttons:
        #         # Check if at least one parent marker for this screen button is visible
        #         if any(mid in visible_marker_ids for mid in screen_btn_def.marker_parents.keys()):
        #             # Filter msg.markers to only include parents of this specific screen button
        #             relevant_markers = [m for m in msg.markers if m.id in screen_btn_def.marker_parents]

        #             pos, orient = self._compute_button_pose(screen_btn_def, relevant_markers)

        #             if pos is not None:
        #                 s_btn = DiegeticButton()
        #                 s_btn.button_id = screen_btn_def.id
        #                 s_btn.x0, s_btn.y0 = screen_btn_def.bounding_box[0], screen_btn_def.bounding_box[1]
        #                 s_btn.x1, s_btn.y1 = screen_btn_def.bounding_box[2], screen_btn_def.bounding_box[3]
        #                 s_btn.button_transform.translation.x, s_btn.button_transform.translation.y, s_btn.button_transform.translation.z = pos
        #                 s_btn.button_transform.rotation.x, s_btn.button_transform.rotation.y, s_btn.button_transform.rotation.z, s_btn.button_transform.rotation.w = orient
        #                 button_3d_array.buttons.append(s_btn)

        #     if not button_3d_array.buttons:
        #         return

        # if not active_buttons:
        #     return

        # 5. Project to 2D using the camera matrix
        # This function will now preserve the stamp internally
        button_2d_array = self._project_to_2d(button_3d_array)

        # 6. Publish results
        self.button_3d_publisher.publish(button_3d_array)
        self.button_2d_publisher.publish(button_2d_array)

        # 7. Broadcast TF transforms
        self._broadcast_transforms(button_3d_array)

        # self.get_logger().info(
        #     f"Found {len(button_3d_array.buttons)} buttons", throttle_duration_sec=10
        # )

        # 8. Trigger haptic feedback if needed
        # self._trigger_haptic_feedback(active_buttons)

    # From the visible/available markers, find the associated buttons,
    # Return a mapping as a dictionary of button_id -> List[Marker]
    def _find_active_buttons(self, markers: List[Marker]) -> Dict[str, List[Marker]]:
        """Find which buttons are active based on visible markers"""
        active_buttons = {}

        for marker in markers:
            marker_id = marker.id

            # Find buttons that use this marker
            for button_id, button_def in self.button_definitions.items():
                if marker_id in button_def.marker_parents:
                    if button_id not in active_buttons:
                        active_buttons[button_id] = []
                    active_buttons[button_id].append(marker)

        return active_buttons

    def _compute_3d_positions(
        self, active_buttons: Dict[str, List[Marker]], header
    ) -> DiegeticButtonArray:
        """Compute 3D positions for active buttons using the selected strategy"""
        button_array = DiegeticButtonArray()

        button_array.header = header
        button_array.header.frame_id = self.camera_frame_id

        for button_id, markers in active_buttons.items():
            button_def = self.button_definitions[button_id]

            # Compute button position from multiple marker observations
            position, orientation = self._compute_button_pose(button_def, markers)

            if position is not None and orientation is not None:
                # Create button message
                button_msg = DiegeticButton()
                button_msg.button_id = button_id

                # Set bounding box
                button_msg.x0 = button_def.bounding_box[0]
                button_msg.y0 = button_def.bounding_box[1]
                button_msg.x1 = button_def.bounding_box[2]
                button_msg.y1 = button_def.bounding_box[3]

                # Set transform
                button_msg.button_transform.translation.x = position[0]
                button_msg.button_transform.translation.y = position[1]
                button_msg.button_transform.translation.z = position[2]

                button_msg.button_transform.rotation.x = orientation[0]
                button_msg.button_transform.rotation.y = orientation[1]
                button_msg.button_transform.rotation.z = orientation[2]
                button_msg.button_transform.rotation.w = orientation[3]

                button_array.buttons.append(button_msg)

        return button_array

    def _compute_button_pose(
        self, button_def: ButtonDefinition, markers: List[Marker]
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Compute button pose from multiple marker observations"""
        position_candidates = []
        rotation_candidates = []
        weights = []

        for marker in markers:
            if marker.id not in button_def.marker_parents:
                continue

            # Get marker pose
            marker_pos = np.array(
                [marker.pose.position.x, marker.pose.position.y, marker.pose.position.z]
            )

            marker_quat = np.array(
                [
                    marker.pose.orientation.x,
                    marker.pose.orientation.y,
                    marker.pose.orientation.z,
                    marker.pose.orientation.w,
                ]
            )

            # Get button offset relative to this marker
            button_offset = np.array(button_def.marker_parents[marker.id][:3])

            # Transform button offset to world coordinates
            marker_rotation_matrix = tf.quaternion_matrix(marker_quat)[:3, :3]
            button_pos = marker_pos + marker_rotation_matrix @ button_offset

            # Compute weight based on strategy
            weight = self._compute_weight(button_offset, marker)

            position_candidates.append(button_pos)
            rotation_candidates.append(marker_quat)
            weights.append(weight)

        if not position_candidates:
            return None, None

        # Combine candidates based on strategy
        final_position = self._combine_positions(position_candidates, weights)
        final_orientation = self._combine_orientations(rotation_candidates, weights)

        return final_position, final_orientation

    def _compute_weight(self, offset: np.ndarray, marker: Marker) -> float:
        """Compute weight based on the selected strategy"""
        if self.center_strategy == ButtonCenterStrategy.AVERAGE:
            return 1.0
        elif self.center_strategy == ButtonCenterStrategy.FIRST_FOUND:
            return 1.0  # Will be handled in combine function
        elif self.center_strategy == ButtonCenterStrategy.CLOSEST:
            return float(1.0 / (np.linalg.norm(offset) + 1e-6))
        elif self.center_strategy == ButtonCenterStrategy.INVERSE_SQUARE:
            return float(1.0 / (np.linalg.norm(offset) ** 2 + 1e-6))
        elif self.center_strategy == ButtonCenterStrategy.INVERSE_CUBIC:
            return float(1.0 / (np.linalg.norm(offset) ** 3 + 1e-6))
        elif self.center_strategy == ButtonCenterStrategy.INVERSE_QUINTIC:
            return float(1.0 / (np.linalg.norm(offset) ** 5 + 1e-6))
        else:
            return 1.0

    def _combine_positions(
        self, positions: List[np.ndarray], weights: List[float]
    ) -> np.ndarray:
        """Combine position candidates using weights"""
        if self.center_strategy == ButtonCenterStrategy.FIRST_FOUND:
            return positions[0]

        weighted_positions = [pos * weight for pos, weight in zip(positions, weights)]
        total_weight = sum(weights)

        return np.sum(weighted_positions, axis=0) / total_weight

    def _combine_orientations(
        self, orientations: List[np.ndarray], weights: List[float]
    ) -> np.ndarray:
        """Combine orientation candidates using weights (simple averaging with quaternion sign correction)."""
        if self.center_strategy == ButtonCenterStrategy.FIRST_FOUND:
            return orientations[0]

        # Choose a reference quaternion (first one)
        ref = orientations[0]

        aligned_orientations = []
        for orient in orientations:
            # Flip if not in the same hemisphere as reference
            if np.dot(ref, orient) < 0:
                orient = -orient
            aligned_orientations.append(orient)

        # Weighted average
        weighted_orientations = [
            orient * weight for orient, weight in zip(aligned_orientations, weights)
        ]
        total_weight = sum(weights)
        combined = np.sum(weighted_orientations, axis=0) / total_weight

        # Normalize quaternion

        return combined / np.linalg.norm(combined)

    def _project_to_2d(
        self, button_3d_array: DiegeticButtonArray
    ) -> DiegeticButton2DArray:
        
        """Project 3D button positions to 2D screen coordinates"""

        button_2d_array = DiegeticButton2DArray()
        button_2d_array.header = button_3d_array.header
        button_2d_array.header.frame_id = (
            self.camera_frame_id
        )  # Changed to camera frame

        for button_3d in button_3d_array.buttons:

            # Get the 4 corners of the button in 3D world coordinates
            corner_points_3d = self._get_button_corner_points_3d(button_3d)
            
            ### Load 3D
            position = np.array([
                button_3d.button_transform.translation.x,
                button_3d.button_transform.translation.y,
                button_3d.button_transform.translation.z,
            ])
            orientation = np.array([
                button_3d.button_transform.rotation.x,
                button_3d.button_transform.rotation.y,
                button_3d.button_transform.rotation.z,
                button_3d.button_transform.rotation.w,
            ])


            # Create 2D button message
            button_2d = DiegeticButton2D()
            button_2d.button_id = button_3d.button_id

            button_2d.surface_angle_deg = self._compute_viewing_angle(position, orientation)
            behind_camera = position[2] <= 0.0

            ### Project 3D corners to 2D
            if corner_points_3d is not None:
                # Project all 4 corner points to 2D camera coordinates
                projected_corners, _ = cv2.projectPoints(
                    corner_points_3d,
                    np.zeros(3),  # No additional rotation
                    np.zeros(3),  # No additional translation
                    self.camera_matrix,
                    self.dist_coeffs,
                )

                # Extract the 4 corner points as arrays of x and y coordinates
                corner_coords = projected_corners.reshape(-1, 2)
                x_coords = corner_coords[:, 0]
                y_coords = corner_coords[:, 1]

                # Store as arrays of 4 points each (as requested in the problem)
                # Note: You'll need to update your DiegeticButton2D.msg to have these fields:
                # float64[4] x_points
                # float64[4] y_points
                # For now, I'm assuming you still want the old format but will show both approaches

                # Store corner points as arrays of 4 points each
                button_2d.x_points = x_coords.astype(float).tolist()
                button_2d.y_points = y_coords.astype(float).tolist()

                # Project button center to get screen-relative center coordinates
                center_3d = np.array(
                    [
                        [
                            button_3d.button_transform.translation.x,
                            button_3d.button_transform.translation.y,
                            button_3d.button_transform.translation.z,
                        ]
                    ]
                )

                projected_center, _ = cv2.projectPoints(
                    center_3d,
                    np.zeros(3),
                    np.zeros(3),
                    self.camera_matrix,
                    self.dist_coeffs,
                )

                button_2d.center_x = float(projected_center[0][0][0])
                button_2d.center_y = float(projected_center[0][0][1])


                in_bounds = (
                    self.image_width is not None
                    and 0 <= button_2d.center_x <= self.image_width
                    and 0 <= button_2d.center_y <= self.image_height
                )
                button_2d.in_frame = bool(in_bounds and not behind_camera)

                button_2d_array.buttons.append(button_2d)

            else:
                # Fallback: just project the center point
                center_3d = np.array(
                    [
                        [
                            button_3d.button_transform.translation.x,
                            button_3d.button_transform.translation.y,
                            button_3d.button_transform.translation.z,
                        ]
                    ]
                )

                projected_center, _ = cv2.projectPoints(
                    center_3d,
                    np.zeros(3),
                    np.zeros(3),
                    self.camera_matrix,
                    self.dist_coeffs,
                )

                button_2d.center_x = float(projected_center[0][0][0])
                button_2d.center_y = float(projected_center[0][0][1])


                in_bounds = (
                    self.image_width is not None
                    and 0 <= button_2d.center_x <= self.image_width
                    and 0 <= button_2d.center_y <= self.image_height
                )
                button_2d.in_frame = bool(in_bounds and not behind_camera)

                # Set default corner points around the center (as fallback)
                default_size = 10.0
                button_2d.x_points = [
                    button_2d.center_x - default_size,  # Bottom-left
                    button_2d.center_x + default_size,  # Bottom-right
                    button_2d.center_x + default_size,  # Top-right
                    button_2d.center_x - default_size,  # Top-left
                ]
                button_2d.y_points = [
                    button_2d.center_y + default_size,  # Bottom-left
                    button_2d.center_y + default_size,  # Bottom-right
                    button_2d.center_y - default_size,  # Top-right
                    button_2d.center_y - default_size,  # Top-left
                ]

            button_2d_array.buttons.append(button_2d)

        return button_2d_array

    def _get_button_corner_points_3d(
        self, button_3d: DiegeticButton
    ) -> Optional[np.ndarray]:
        """Get the 4 corner points of the button in 3D world coordinates"""
        try:
            # Define the 4 corners of the button in local button coordinates
            corners_local = np.array(
                [
                    [button_3d.x0, button_3d.y0, 0.0],  # Bottom-left
                    [button_3d.x1, button_3d.y0, 0.0],  # Bottom-right
                    [button_3d.x1, button_3d.y1, 0.0],  # Top-right
                    [button_3d.x0, button_3d.y1, 0.0],  # Top-left
                ]
            )

            # Get button transform (position and orientation in world coordinates)
            position = np.array(
                [
                    button_3d.button_transform.translation.x,
                    button_3d.button_transform.translation.y,
                    button_3d.button_transform.translation.z,
                ]
            )

            orientation = np.array(
                [
                    button_3d.button_transform.rotation.x,
                    button_3d.button_transform.rotation.y,
                    button_3d.button_transform.rotation.z,
                    button_3d.button_transform.rotation.w,
                ]
            )

            # Create transformation matrix from button local coordinates to world coordinates
            transform_matrix = tf.quaternion_matrix(orientation)
            transform_matrix[:3, 3] = position

            # Transform all 4 corners from button local coordinates to world coordinates
            corners_world = []
            for corner_local in corners_local:
                # Convert to homogeneous coordinates
                corner_homogeneous = np.append(corner_local, 1.0)
                # Transform to world coordinates
                corner_world = transform_matrix @ corner_homogeneous
                # Extract 3D coordinates
                corners_world.append(corner_world[:3])

            return np.array(corners_world)

        except Exception as e:
            self.get_logger().debug(f"Failed to compute 3D button corners: {e}")
            return None

    def _get_bounding_box_corners_3d(
        self, button_3d: DiegeticButton
    ) -> Optional[np.ndarray]:
        """Get 3D corners of button bounding box - DEPRECATED, use _get_button_corner_points_3d instead"""
        return self._get_button_corner_points_3d(button_3d)

    def _broadcast_transforms(self, button_3d_array: DiegeticButtonArray):
        """Broadcast TF transforms for each button"""

        for button in button_3d_array.buttons:
            transform_stamped = TransformStamped()


            # transform_stamped.header.stamp = button_3d_array.header.stamp
            transform_stamped.header.stamp = self.get_clock().now().to_msg()

            transform_stamped.header.frame_id = self.camera_frame_id
            transform_stamped.child_frame_id = f"bt_{button.button_id}"

            transform_stamped.transform.translation = (
                button.button_transform.translation
            )
            transform_stamped.transform.rotation = button.button_transform.rotation

            self.tf_broadcaster.sendTransform(transform_stamped)

            # For the alignment button, also broadcast its position relative to
            # the end-effector so the TF tree holds even when ArUco 88 is lost.
            # Tree: j2n6s300_end_effector -> bt_UpHybridRe_ee (static-ish, updated each frame)
            if button.button_id == "UpHybridRe":
                try:
                    # Look up where the button sits in the end-effector frame
                    t = self.tf_buffer.lookup_transform(
                        "j2n6s300_end_effector",
                        f"bt_{button.button_id}",
                        rclpy.time.Time()
                    )

                    ee_stamped = TransformStamped()
                    ee_stamped.header.stamp = self.get_clock().now().to_msg()
                    ee_stamped.header.frame_id = "j2n6s300_end_effector"
                    ee_stamped.child_frame_id = "bt_UpHybridRe_ee"
                    ee_stamped.transform = t.transform

                    self.tf_broadcaster.sendTransform(ee_stamped)

                except Exception:
                    pass  # Chain not yet available, skip silently

    def _trigger_haptic_feedback(self, active_buttons: Dict[str, List[Marker]]):
        """Trigger haptic feedback for newly detected buttons"""
        if active_buttons:
            haptic_msg = String()
            haptic_msg.data = "button_detected"
            self.haptic_publisher.publish(haptic_msg)

    def _publish_static_button_link(self):
        """
        Publishes a static transform connecting the end-effector to the UpHybridRe button.
        Tree: j2n6s300_end_effector -> bt_UpHybridRe
        Offset should match the physical position of the button on the controller.
        """
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "j2n6s300_end_effector"
        t.child_frame_id = "bt_UpHybridRe"

        # TODO: measure and set the actual offset of the button relative to the end-effector
        xyz = [0.0, 0.045, -0.09]
        rpy = [-np.pi / 2, 0.0, 0.0]

        t.transform.translation.x = float(xyz[0])
        t.transform.translation.y = float(xyz[1])
        t.transform.translation.z = float(xyz[2])

        quat = tf_transformations.quaternion_from_euler(rpy[0], rpy[1], rpy[2])
        t.transform.rotation.x = quat[0]
        t.transform.rotation.y = quat[1]
        t.transform.rotation.z = quat[2]
        t.transform.rotation.w = quat[3]

        self.static_broadcaster.sendTransform(t)

    @staticmethod
    def _compute_viewing_angle(position: np.ndarray, orientation: np.ndarray) -> float:
        """Angle (deg) between the button's outward normal and the camera's line of sight.
        0 = facing the camera directly, 90 = edge-on / invisible."""
        R = tf_transformations.quaternion_matrix(orientation)[:3, :3]
        normal = R @ np.array([0.0, 0.0, 1.0])          # button's local +Z, assumed outward
        to_camera = -position / (np.linalg.norm(position) + 1e-9)
        cos_angle = np.clip(np.dot(normal, to_camera), -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_angle)))


def main(args=None):
    rclpy.init(args=args)

    node = DiegeticButtonPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
