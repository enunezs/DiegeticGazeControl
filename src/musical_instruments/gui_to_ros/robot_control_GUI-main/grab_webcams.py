import subprocess

# Needs 
webcam_string = subprocess.check_output(['v4l2-ctl', '--list-devices'], 
                                         universal_newlines=True)
print(webcam_string)
webcams = webcam_string.split('\n\n')

def split_down_cam_info(cam):
    cam_info = cam.split('\n\t')
    cam_name = cam_info[0]
    cam_streams = cam_info[1:]
    return cam_name, cam_streams


def get_cam_feeds(name_filter = ''):
    webcam_string = subprocess.check_output(['v4l2-ctl', '--list-devices'], 
                                         universal_newlines=True)

    webcams = webcam_string.split('\n\n')
    cam_data = [split_down_cam_info(cam) for cam in webcams]
    filtered_cam_data = [cam[1][0] for cam in cam_data if name_filter in cam[0]]

    return filtered_cam_data

if __name__ == "__main__":
    print(get_cam_feeds("C270 HD WEBCAM"))
    