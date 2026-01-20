import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from launch.substitutions import ThisLaunchFileDir, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import SetParameter

SetParameter(name="use_sim_time", value=True)


"""
ros2 launch gaze_interaction_manager rosbag_CALIB_testing.launch.py \
  bag_path:=/home/emanuel/Documents/ROS2_Workspaces/DiegeticGazeControl/bag_files/CALIB/X_P_01
"""


def generate_launch_description():

    launch_description = LaunchDescription()

    # -----------------------------
    # Launch arguments
    # -----------------------------
    # bag_path_arg = DeclareLaunchArgument(
    #     "bag_path",
    #     description="Path to the rosbag to play instead of the live Pupil node",
    # )

    # bag_path = LaunchConfiguration("bag_path")

    # # -----------------------------
    # # Rosbag player (replaces Pupil)
    # # -----------------------------
    # rosbag_play = ExecuteProcess(
    #     cmd=[
    #         "ros2", "bag", "play",
    #         bag_path,
    #         "--clock"
    #     ],
    #     output="screen",
    # )

    config = os.path.join(
        get_package_share_directory("pupil_neon_ros"), "config", "params.yaml"
    )
    # launch_description.add_action(rosbag_play)

    # ### Pupil Glasses ###
    # pupil_node = Node(
    #     package="pupil_neon_ros",
    #     executable="async_pupil_publisher.py",
    #     name="pupil_glasses_node",
    #     arguments=["__log_level:=debug"],
    #     output="screen",
    #     parameters=[config],
    # )
    # launch_description.add_action(pupil_node)

    pupil_visuals_node = Node(
        package="pupil_neon_ros",
        executable="rviz_visualizer.py",
        name="pupil_glasses_visuals_node",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(pupil_visuals_node)

    config = os.path.join(
        get_package_share_directory("diegetic_transform_engine"),
        "config",
        "params.yaml",
    )

    ### Transform Engine ###
    aruco_detector_node = Node(
        package="diegetic_transform_engine",
        executable="aruco_detector.py",
        name="aruco_detector",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(aruco_detector_node)

    button_finder_node = Node(
        package="diegetic_transform_engine",
        executable="button_finder.py",
        name="button_finder",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(button_finder_node)

    ### Gaze Interaction Manager ###

    config = os.path.join(
        get_package_share_directory("gaze_interaction_manager"),
        "config",
        "CALIB_ros_params.yaml",
    )

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

    # audio_feedback_node = Node(
    #     package="feedback_tools",
    #     executable="audio_feedback.py",
    #     name="audio_feedback_node",
    #     arguments=["__log_level:=debug"],
    #     output="screen",
    #     parameters=[config],
    # )
    # launch_description.add_action(audio_feedback_node)

    return launch_description
