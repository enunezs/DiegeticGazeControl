import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import ThisLaunchFileDir, PathJoinSubstitution


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="pupil_neon_pkg",
                executable="emulator_publisher.py",
                name="pupil_glasses_emulator_node",
                arguments=[("__log_level:=debug")],
                output="screen",
                parameters=[
                    os.path.join(
                        get_package_share_directory("pupil_neon_pkg"),
                        "config",
                        "params.yaml",
                    )
                ],
            ),
            Node(
                package="fiducials",
                executable="aruco_detect.py",
                name="aruco_detect",
                parameters=["src/fiducials/config/params.yaml"],
            ),
            Node(
                package="fiducials",
                executable="aruco_mapper.py",
                name="aruco_mapper",
                parameters=[
                    {
                        "config_file_path": "src/fiducials/config/mapping.csv",
                        "root_frame": "camera",
                    }
                ],
            ),
            Node(
                package="diegetic_button_pkg",
                executable="diegetic_button.py",
                name="diegetic_button",
                parameters=["src/diegetic_button_pkg/config/params.yaml"],
            ),
            Node(
                package="diegetic_button_pkg",
                executable="input_check.py",
                name="input_check",
                parameters=["src/diegetic_button_pkg/config/params.yaml"],
            ),
            Node(
                package="diegetic_button_pkg",
                executable="joy.py",
                name="joy",
            ),
        ]
    )
