import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from launch.substitutions import ThisLaunchFileDir, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    launch_description = LaunchDescription()

    config = os.path.join(
        get_package_share_directory("pupil_neon_ros"), "config", "params.yaml"
    )

    ### Pupil Glasses ###
    pupil_node = Node(
        package="pupil_neon_ros",
        executable="async_pupil_publisher.py",
        name="pupil_glasses_node",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(pupil_node)

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

    ### Gaze Interaction Manager
    dwell_time_node = Node(
        package="gaze_interaction_manager",
        executable="dwell_time.py",
        name="dwell_time_node",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(dwell_time_node)

    controller_node = Node(
        package="gaze_interaction_manager",
        executable="gaze_controller.py",
        name="controller_node",
        parameters=[config],
    )
    launch_description.add_action(controller_node)

    ### Visuals ###
    # button_visualizer_node = Node(
    #     package="feedback_tools",
    #     executable="2D_visuals.py",
    #     name="button_2D_visualizer",
    #     arguments=["__log_level:=debug"],
    #     output="screen",
    #     parameters=[config],
    # )
    # launch_description.add_action(button_visualizer_node)

    button_visualizer_node = Node(
        package="feedback_tools",
        executable="3D_visuals.py",
        name="button_3D_visualizer",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(button_visualizer_node)

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
