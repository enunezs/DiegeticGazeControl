import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    launch_description = LaunchDescription()

    config = os.path.join(
        get_package_share_directory("diegetic_transform_engine"),
        "config",
        "params.yaml",
    )

    aruco_detector_node = Node(
        package="diegetic_transform_engine",
        executable="aruco_detector.py",
        name="aruco_detector",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(aruco_detector_node)

    aruco_visualizer_node = Node(
        package="diegetic_transform_engine",
        executable="aruco_visualizer.py",
        name="aruco_visualizer",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(aruco_visualizer_node)

    button_finder_node = Node(
        package="diegetic_transform_engine",
        executable="button_finder.py",
        name="button_finder",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(button_finder_node)

    button_visualizer_node = Node(
        package="diegetic_transform_engine",
        executable="button_visualizer.py",
        name="button_visualizer",
        arguments=["__log_level:=debug"],
        output="screen",
        parameters=[config],
    )
    launch_description.add_action(button_visualizer_node)

    print("Diegetic Transform Engine Launch is Running...")
    print(f"params.yaml: {config}")

    return launch_description
