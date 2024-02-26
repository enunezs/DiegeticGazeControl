import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    config = os.path.join(
        get_package_share_directory('pupil_neon_pkg'),
        'config',
        'params.yaml'
        )

    node = Node(
        package="pupil_neon_pkg",
        executable="emulator_publisher.py",
        name="glasses_emulator_node",
        #prefix=['Terminal -e gdb -ex run --args'],
        arguments=[('__log_level:=debug')],
        output='screen',
        emulate_tty=True,
        parameters=[config]
    )
    print("Pupil Neon Emulator Node is Running...")
    print(f"params.yaml: {config}")
    ld.add_action(node)
    return ld


"""
        Node(
            package="diegetic_button_pkg",
            executable="input_check.py",
            name="process_inputs_node"
        ),
"""
