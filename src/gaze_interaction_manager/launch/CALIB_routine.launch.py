import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from launch.substitutions import ThisLaunchFileDir, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource


"""
ros2 bag record -o bag_files/CALIB/X_P_01  /pupil_glasses/event/blink /pupil_glasses/event/fixation /pupil_glasses/event/fixation_onset /pupil_glasses/event/saccade /pupil_glasses/event/saccade_onset /pupil_glasses/front_camera/camera_info /pupil_glasses/front_image /pupil_glasses/gaze_data /pupil_glasses/gaze_position /pupil_glasses/imu
"""

def generate_launch_description():
    launch_description = LaunchDescription()

    config = os.path.join(
        get_package_share_directory("gaze_interaction_manager"), "config", "CALIB_ros_params.yaml"
    )


    ### Pupil Glasses ### For recording
    pupil_node = Node(
        package="pupil_neon_ros",
        executable="async_pupil_publisher.py",
        name="pupil_glasses_node",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(pupil_node)


    ### Testing Joystick Controller with JoyCommandMapper ###
    joy_command_mapper_node = Node(
        package="gaze_interaction_manager",
        executable="joy_command_mapper.py",
        name="command_mapper_node",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(joy_command_mapper_node)

    controller_node = Node(
        package="joy",
        executable="joy_node",
        name="joy_node",
        parameters=[config],
    )
    launch_description.add_action(controller_node)

    
    audio_feedback_node = Node(
        package="feedback_tools",
        executable="audio_feedback.py",
        name="audio_feedback_node",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(audio_feedback_node)

    return launch_description
