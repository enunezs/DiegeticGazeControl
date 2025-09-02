import cv2
import sys
import yaml
from pprint import pprint
import numpy as np
sys.path.append('../src')
print(sys.path)
from screenDetector import ScreenDetector
from ConfigHelperFunctions import load_aruco_config, load_detector_config

if __name__ == "__main__":
    # Load configs:
    aruco_config_loc = "../src/aruco_codes.yaml"
    detector_config_loc = "../src/detectorSettings.yaml"
    image_loc = "aruco_far_image.png" 

    # Load parameters from folder.
    aruco_params = load_aruco_config(aruco_config_loc)
    detector_params = load_detector_config(detector_config_loc)
    # Grab a test image.
    frame = cv2.imread(image_loc) 
    scaling_factor = 3
    
    # Get image size (must be a cuter way of doing this!)
    image_size_x = frame.shape[1]
    image_size_y = frame.shape[0]
    image_size = [int(image_size_x/scaling_factor), 
                  int(image_size_y/scaling_factor)
                  ]
        
    resized_frame = cv2.resize(frame, image_size)
    
    aruco_detector = cv2.aruco.ArucoDetector(
            aruco_params["aruco_dict"], 
            detector_params
            )

    detector = ScreenDetector(image_size, 
                              aruco_detector,
                              aruco_config=aruco_params)

    
    # Display the resulting frame
    corners, ids, rejected = detector.detect_arucos(resized_frame)
    # print(f"Corner Ids detected: {np.squeeze(ids)}")
    corner_detection_dict = detector.filter_aruco_detections(corners, ids, rejected)
    if len(corner_detection_dict) == 0:
        print("No aruco detected!")
        output_frame = resized_frame
    # TODO: Replace this with an actual filter!    
    elif len(corner_detection_dict) < 4:
        output_frame = cv2.aruco.drawDetectedMarkers(resized_frame, corners, ids)
    
    else:
        corners = detector.detect_screen_corners(resized_frame)
        screen_frame = detector.annotate_screen(resized_frame, corners)

        screen_coords = detector.detect_screen_corners(resized_frame)
        output_frame = detector.annotate_screen(resized_frame, screen_coords)
    
    cv2.imshow('output', output_frame)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()


