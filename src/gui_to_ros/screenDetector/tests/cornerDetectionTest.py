import cv2
import numpy as np
import pprint


if __name__ == "__main__":
    image = cv2.imread("aruco_far_image.png")
    aruco_dict = cv2.aruco.getPredefinedDictionary(1)
    detector = cv2.aruco.ArucoDetector(aruco_dict)
    corners, ids, rejected = detector.detectMarkers(image)
    cv2.aruco.drawDetectedMarkers(image, corners, ids)
    cv2.imshow("all detected arucos", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
