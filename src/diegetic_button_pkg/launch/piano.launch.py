import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, ThisLaunchFileDir, Command

from launch_ros.actions import Node
from launch.substitutions import ThisLaunchFileDir, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    # Declare the launch argument for the optional configuration file
    override_config_file_arg = DeclareLaunchArgument(
        "override_config_file",
        default_value="",
        description="Path to the override configuration file",
    )

    # Use the custom configuration file if specified, otherwise use the default
    override_config_file = LaunchConfiguration("override_config_file")

    launch_description = LaunchDescription()
    launch_description.add_action(override_config_file_arg)

    pupil_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(get_package_share_directory("pupil_neon_pkg"), "launch"),
                "/emulator_pupil.launch.py",
            ]
        )
    )
    launch_description.add_action(pupil_launch)

    # Fiducials
    fiducials_node_detect = Node(
        package="fiducials",
        executable="aruco_detect.py",
        name="aruco_detect",
        parameters=["src/diegetic_button_pkg/config/piano_config.yaml"],
    )
    launch_description.add_action(fiducials_node_detect)

    fiducials_node_mapper = Node(
        package="fiducials",
        executable="aruco_mapper.py",
        name="aruco_mapper",
        parameters=[
            {
                "config_file_path": "src/fiducials/config/mapping.csv",
                "root_frame": "camera",
            }
        ],
    )
    launch_description.add_action(fiducials_node_mapper)

    # Diegetic Button
    diegetic_button_node = Node(
        package="diegetic_button_pkg",
        executable="diegetic_button.py",
        name="diegetic_button",
        parameters=["src/diegetic_button_pkg/config/piano_config.yaml"],
    )
    launch_description.add_action(diegetic_button_node)

    input_check_node = Node(
        package="diegetic_button_pkg",
        executable="input_check.py",
        name="process_inputs_node",
        parameters=["src/diegetic_button_pkg/config/piano_config.yaml"],
    )
    launch_description.add_action(input_check_node)

    input_check_node = Node(
        package="diegetic_button_pkg",
        executable="diegetic_parser.py",
        name="diegetic_parser_node",
        parameters=["src/diegetic_button_pkg/config/piano_config.yaml"],
    )
    launch_description.add_action(input_check_node)

    """
    # Old Piano
    piano_node = Node(
        package="diegetic_button_pkg",
        executable="piano_demo.py",
        name="piano",
        parameters=["src/diegetic_button_pkg/config/piano_config.yaml"],
    )

    launch_description.add_action(piano_node)
    """

    return launch_description
