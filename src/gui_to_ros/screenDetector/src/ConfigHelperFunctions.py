import yaml
import sys
import cv2

sys.path.append("../src")
from screenDetector import ScreenDetector

def load_aruco_config(aruco_config_loc):
    "This loads in our ARUCO config folder. This contains information about what aruco tags are on the screen, the aruco dictionary used to crate them and other identifying info. Used to link createAruco.py and screenDetector.py with the same aruco tags. Also returns an aruco dict"
    # Load in our aruco_codes file as a config file.
    with open(aruco_config_loc) as file:
        aruco_config_dict = yaml.safe_load(file)

    aruco_config_dict["aruco_dict"] = cv2.aruco.getPredefinedDictionary(
        aruco_config_dict["aruco_dict_index"]
    )
    print(aruco_config_dict["aruco_dict"], aruco_config_dict["aruco_dict_index"])
    return aruco_config_dict


def load_detector_config(detector_config_loc):
    """This function creates a detector config struct from a .yaml file. NOTE: This YAML file must be formatted with a cv2 header in order to be processed! If you want more information about the contents of the YAML file, please consult openCVs documentation about the detectorParameters struct."""

    # Create a DetectorParameters object that loads in our detector parameters file.
    fs = cv2.FileStorage(detector_config_loc, cv2.FILE_STORAGE_READ)
    detector_config_struct = cv2.aruco.DetectorParameters()
    detector_config_struct.readDetectorParameters(fs.root())
    fs.release()

    return detector_config_struct


if __name__ == "__main__":
    
    ARUCO_CONFIG_LOC = "../src/aruco_codes.yaml"
    DETECTOR_CONFIG_LOC = "../src/detectorSettings.yaml"
    image_loc = "../tests/test_save.jpeg"

    image = cv2.imread(image_loc)
    image_2 = cv2.imread("../tests/test_save_1.jpeg")
    aruco_params = load_aruco_config(ARUCO_CONFIG_LOC)
    detector_params = load_detector_config(DETECTOR_CONFIG_LOC)

    aruco_detector = cv2.aruco.ArucoDetector(aruco_params["aruco_dict"], detector_params)

    detector = ScreenDetector([720, 1080], aruco_detector, aruco_config=aruco_params)

    result = detector.detect_arucos(image)
    result2 = detector.detect_arucos(image_2)
    
    print(result[1])
    print(result2[1])
