import cv2
import os
import numpy as np
from typing import Collection, Tuple

np.set_printoptions(threshold=np.inf, suppress=True)
from pprint import pprint


class ArucoDetectionError(Exception):
    pass


class ScreenDetector:
    """
    This class detects the corners of a screen using ARUCO tags.
    attributes:
    aruco_dict: The dictionary of ARUCO tags to use.
    aruco_ids: The ids of the ARUCO tags to use.
    frame_size: The size of the screen in pixels.
    capture_size: The size of the image captured from the camera in pixels.
    """

    def __init__(
        self,
        frame_size,
        detector,
        aruco_ids=[81, 82, 83, 84],
        min_val=-0.1,  # the next job is to enable this, gettting full screen image.,
        max_val=1.1,  # this one too!,
        aruco_config=None,
    ):
        if not aruco_config:
            self.expected_ids = aruco_ids
        else:
            self.expected_ids = aruco_config["corner_ids"]

        self.frame_size = frame_size

        self.transform = None  # This maps points on the screen to another image.
        self.scale_transform = np.eye(3)
        self.scale_transform[0, 0] = 1 / frame_size[1]
        self.scale_transform[1, 1] = 1 / frame_size[0]

        self.unit_transform = None  # This maps the screen to a unit square.
        # these are the min and max values for the screen coordinates. This allows us to have some leeway in the coordinates.
        self.min_val = min_val
        self.max_val = max_val

        self.screen_edges = np.array(
            [
                [0, 0],
                [frame_size[1], 0],
                [frame_size[1], frame_size[0]],
                [0, frame_size[0]],
            ],
            dtype=np.float32,
        )  # defining this here so we dont construct it at every step.

        # Load Aruco Detector with config files included in aruco_config_loc

        self.id_dict = {
            1: "Top-left",
            2: "Bottom-left",
            3: "Top-right",
            4: "Bottom-right",
        }
        # The corner_to_grab dict shows which corner index  should be used for each aruco tag.
        self.corner_to_grab = {
            aruco_tag: corner for corner, aruco_tag in enumerate(self.expected_ids)
        }
        self.aruco_detector = detector

    def set_image_size(self, image):
        # This function will take the image and return the size of the image
        # in pixels.
        self.frame_size = image.shape[0:-1]  # Removes the last dimension (color)

    def detect_arucos(self, image):
        self.logger.info("Detecting ARUCO markers")
        blurred_image = cv2.GaussianBlur(image, (5, 5), 0)
        amount=10
        sharpened_image = cv2.addWeighted(
            blurred_image, 1.8, image, -0.8, 0
        )  # Sharpen the image to improve detection

        resiz3ed_image = cv2.resize(
            sharpened_image, (self.frame_size[1] // 3, self.frame_size[0] // 3)
        # Just a wrapper atround cv2.ArucoDetector.detectMarkers
        corners, ids, rejected = self.aruco_detector.detectMarkers(sharpened_image)
        # print(f"raw detection values: {np.squeeze(ids)}")
        # Theres more to add here, we should really be checking if the ids are in the list of ids we want to detect.
        return corners, ids, rejected

    def filter_aruco_detections(self, corners, ids, rejected):
        """Filters out irrelevent aruco tags, leaving a list of aruco tags that match the detections.
        At the moment, this will return the first instance of any duplicates, and ignores any rejected aruco tags.
        However, we should really deal with those cases somehow.

        WARNING: This definitely isn't optimised!"""
        ids = np.squeeze(
            ids
        )  # Needed to transform ids into a row vector. simplifies filtering further down.
        corners = np.squeeze(np.array(corners))

        unique_ids = np.unique(ids)
        unique_ids = unique_ids[np.isin(unique_ids, self.expected_ids)]

        # This grabs every location that a tag appears in, and then stores it as a 3 Rank array in a dict.
        id_locations = {
            aruco_id: np.where(ids == aruco_id, True, False) for aruco_id in unique_ids
        }
        # # print("id locations:")
        # pprint(id_locations)

        # print("filtered IDS:")
        corner_loc_dict = {}

        for aruco_id, boolean_filter in id_locations.items():
            # print(f"id: {aruco_id}, filter = {boolean_filter}")
            # print(f"bool shape: {boolean_filter.T.shape}, array_shape: {corners.shape}")
            detected_ids = corners[boolean_filter][
                0
            ]  # At the moment this just grabs the first matching candidate.
            # pprint(detected_ids)
            corner_loc_dict[aruco_id] = detected_ids

        return corner_loc_dict

    def _corner_finder(self, aruco_id, corners):
        # print("_____ Corner finder: _____")
        # print(f"aruco_id: {aruco_id}")
        """Finds the correct corner given a list of ARUCO tags."""
        corner_index = self.corner_to_grab[aruco_id]
        # print(f"corner_index {corner_index}")
        corner = corners[corner_index]
        # print(f"corner location: {corner}")
        return corner

    def get_screen_corners(self, location_dict) -> Tuple[bool, np.ndarray]:
        values = [
            self._corner_finder(aruco_id, corners)
            for aruco_id, corners in location_dict.items()
        ]

        return np.array(values).astype(np.float32)

    def get_screen_transform(self, corners=None) -> np.ndarray:
        # This function will take the image and the corners of the screen and return a transform matrix
        # maps the screen corners to the image corners.
        # print("_____ Entering Screen Transform ______")
        # print(f"corners:\n{corners}")
        # print(f"screen edges:\n{self.screen_edges}\n")
        transform_matrix = cv2.getPerspectiveTransform(corners, self.screen_edges)
        # print(f"Transform matrix:\n{transform_matrix}")
        self.transform = transform_matrix
        return np.array(transform_matrix)

    def get_normalisation_transform(self, corners) -> np.ndarray:
        """This is a frame transform that normalises points detected on a screen S within a larger image I.
        The returned value will map points on the screen to [0, 1]. Any points outside the screen will be
        outside this range.

        Inputs:
        image: The source image (not used)
        corners: The detected screen corners

        #TODO: allow this function to take in raw feed and call detect_screen_corners to find all corners in the image."""

        transform_matrix = cv2.getPerspectiveTransform(corners, self.screen_edges)
        normalisation_matrix = self.scale_transform @ transform_matrix
        return normalisation_matrix

    def find_point_on_screen(self, point: np.ndarray) -> (np.ndarray, bool):
        # This function will take a point in the image and return the point on the screen.
        # This is done by using the transform matrix to map the point to the screen.
        # The point should be in the format [x, y, 1]
        # The transform matrix should be in the format [a, b, c], [d, e, f], [g, h, i]
        # The point should be in the format [x, y, 1]
        # The output should be in the format [x, y]
        if self.transform is None:
            self.transform = self.get_screen_transform()

        point = self.transform @ point
        scale_factor = point[2]
        point = point / scale_factor  # compensate for the z value.
        scaled_point = point @ self.scale_transform

    def annotate_screen(self, image: np.ndarray, screen_points) -> np.ndarray:
        # print("_____ Entering annotate Screen _____")
        # print("screen_points")
        # print(screen_points)
        # This function will take the most recent image from a stream and return a transform matrix
        # maps the screen corners to the image corners.
        im = image.copy()
        transform = self.get_screen_transform(screen_points)
        # This should be an effient way to get the screen corners.
        screen_points_copy = screen_points.copy()
        for num in screen_points_copy:
            initial_point = [num[0], num[1], 1]
            mapping_point = transform @ initial_point
            # Why does this work?
            mapping_point = mapping_point / mapping_point[2]

        screen_coords_draw = screen_points_copy.astype(np.int32)
        cv2.polylines(im, [screen_coords_draw], True, (0, 255, 255), 5)
        return im

    def check_if_gaze_is_on_screen(self, gaze_point: np.ndarray) -> bool:
        # This function will take a point in the image and return True if the point is on the screen.
        # This is done by using the transform matrix to map the point to the screen.
        # The point should be in the format [x, y, 1]
        # The transform matrix should be in the format [a, b, c], [d, e, f], [g, h, i]
        # The point should be in the format [x, y, 1]
        # The output should be in the format [x, y]
        if self.transform is None:
            self.transform = self.get_screen_transform()

        point = self.transform @ gaze_point
        point = point / point[2]
