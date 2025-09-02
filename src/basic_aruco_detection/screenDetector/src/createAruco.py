import cv2
import numpy as np
import cv2.aruco as aruco
from typing import Collection
from ConfigHelperFunctions import load_aruco_config, load_detector_config
from numpy.matlib import repmat
from pprint import pprint


def create_aruco_border_tags(
        aruco_dict,
        aruco_size: int, 
        corner_ids: Collection[int],
        border_size: int,
        monitor_size,
        **kwargs):

    if border_size is False:
        border_size = aruco_size // 6 # Default border size if not specified
    """This function generates an ARUCO border for an image. This is used to detect a computer/images location in space."""
    print(corner_ids)
    print(corner_ids)
    images = [aruco.generateImageMarker(aruco_dict, aruco_id, aruco_size - (2 * border_size)) for aruco_id in corner_ids]

    image_w_border = [np.ones([aruco_size, aruco_size], np.uint8) * 255 
               for image in corner_ids]

    for image, border in zip(images, image_w_border):
        border[border_size:-border_size, border_size:-border_size] = image
    
    return image_w_border


def add_aruco_tag_to_image(base_image, aruco_images: Collection):
    """overlays aruco border tags onto an image """

    aruco_image_size = np.shape(aruco_images[0])[0]
    print(np.shape(aruco_images[0]))
    # If the image is coloured, then aruco 
    aruco_images = [cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) for image in aruco_images]

    base_image_shape = np.shape(base_image)
    
    base_image[0:aruco_image_size, 0:aruco_image_size, :] = aruco_images[0]
    base_image[0:aruco_image_size, -aruco_image_size:, :] = aruco_images[1]
    base_image[-aruco_image_size:, -aruco_image_size:, :] = aruco_images[2]
    base_image[-aruco_image_size:, 0:aruco_image_size,:] = aruco_images[3]
    
    return base_image


if __name__ == "__main__":
    ARUCO_CONFIG_LOC = "aruco_codes.yaml"
    aruco_params = load_aruco_config(ARUCO_CONFIG_LOC)

    DETECTOR_CONFIG_LOC = "detectorSettings.yaml"
    detector_params = load_detector_config(DETECTOR_CONFIG_LOC)

    print("Getting aruco config info!")
    pprint(aruco_params)

    aruco_tags = create_aruco_border_tags(**aruco_params)
    base_image = np.zeros((*aruco_params["monitor_size"], 3), dtype=np.uint8)
    base_image[:] = aruco_params["background_colour"]  # Fill with colo    
    
    aruco_image = add_aruco_tag_to_image(base_image, aruco_tags)
    
    aruco_detector = cv2.aruco.ArucoDetector(aruco_params['aruco_dict'], detector_params)
    corners, ids, rejected = aruco_detector.detectMarkers(aruco_image)
    print(ids)
    cv2.imwrite("../tests/ArucoTagTest.png", aruco_image)
    cv2.imshow("aruco tags overlaid on image", aruco_image)
    
    aruco_check_image = aruco_image.copy()
    cv2.aruco.drawDetectedMarkers(aruco_check_image, corners, ids)
    # cv2.imshow("aruco check image", aruco_check_image)
    cv2.waitKey(0)


