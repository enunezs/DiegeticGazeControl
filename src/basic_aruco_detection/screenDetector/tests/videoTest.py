import cv2
import sys
import os
import numpy as np

BASE_FOLDER = '/root/ws/DiegeticGazeControl/src/basic Aruco Detection/screenDetector'
sys.path.append('/root/ws/DiegeticGazeControl/src/basic Aruco Detection/screenDetector/src')

from screenDetector import ScreenDetector, ArucoDetectionError
from ConfigHelperFunctions import load_aruco_config, load_detector_config

MARKER_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

if __name__ == "__main__":
    aruco_config_loc = f"{BASE_FOLDER}/src/aruco_codes.yaml"
    detector_config_loc = f"{BASE_FOLDER}/src/detectorSettings.yaml"
    image_loc = "error_images/0001.png" 

    # Load parameters from folder.
    aruco_params = load_aruco_config(aruco_config_loc)
    detector_params = load_detector_config(detector_config_loc)
    
    detector = None
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    last_detection = None
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if not ret:
            print("camera feed not yeilding frame!")
            continue
        print("Camera yeilded a frame!")
        
        #If a detector isn't set up, then set up a detector!
        if detector is None:
            scaling_factor = 1
            # Get image size (must be a cuter way of doing this!)
            
            image_size_x = frame.shape[1]
            image_size_y = frame.shape[0]
            image_size = [
                    int(image_size_x/scaling_factor), 
                    int(image_size_y/scaling_factor)
                  ]
            
            aruco_detector = cv2.aruco.ArucoDetector(
                aruco_params["aruco_dict"], 
                detector_params
            )

            detector = ScreenDetector(
                    image_size, 
                    aruco_detector,
                    aruco_params["corner_ids"],
                    aruco_config=aruco_params
                    )
        # Display the resulting frame
        
        resized_frame = cv2.resize(frame, detector.frame_size)
        corners, ids, rejected = detector.detect_arucos(resized_frame)
        print(f"Corner Ids detected: {ids}")
        corner_detection_dict = detector.filter_aruco_detections(corners, ids, rejected)
        
        print("corner detections", "\n", corner_detection_dict)
        
        if len(corner_detection_dict) == 0:
            print("No aruco detected!")
            output_frame = resized_frame
        # TODO: Replace this with an actual filter!    
        
        elif len(corner_detection_dict) < 4:
            output_frame = resized_frame.copy()
            output_frame = cv2.aruco.drawDetectedMarkers(resized_frame, corners, ids)
            if last_detection is not None:
                for aruco_id, corners in corner_detection_dict.items():
                    last_detection[aruco_id] = corners
                screen_corners = detector.get_screen_corners(last_detection)
                output_frame = detector.annotate_screen(output_frame, screen_corners)
             
        
        else:
            print("All four corners detected!")
            screen_coords = detector.get_screen_corners(corner_detection_dict)
            last_detection = corner_detection_dict
            print(last_detection)
            print("corners detected:\n{last_detection}")

            output_frame = detector.annotate_screen(resized_frame, screen_coords)
            output_frame = cv2.aruco.drawDetectedMarkers(output_frame, corners, ids)
            cv2.imshow('output', output_frame)

        cv2.imshow('output', output_frame)
        
        if cv2.waitKey(1) == ord('q'):
            break

        
    
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
