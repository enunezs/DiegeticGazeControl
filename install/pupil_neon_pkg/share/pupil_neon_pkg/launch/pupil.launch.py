import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess


def generate_launch_description():
    ld = LaunchDescription()

    config = os.path.join(
        get_package_share_directory('pupil_neon_pkg'),
        'config',
        'params.yaml'
        )

    node = Node(
        package="pupil_neon_pkg",
        executable="pupil_publisher.py",
        name="pupil_glasses_node",
        emulate_tty=True,
        parameters=[config]
    )
    
    print("Pupil Neon Emulator Node is Running...")
    print(f"params.yaml: {config}")
    ld.add_action(node)
    return ld


