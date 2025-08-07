def create_controller():
    try:
        from joy_node import ControllerPublisher
        print("Loaded joy node with ROS support!")
        controller = ControllerPublisher()
    
    except ImportError:
        from joy_node_test import ControllerPublisher
        print("""ROS not availible, loading joy node test class,
This will not send messages out to the robot""")

        controller = ControllerPublisher()

    return controller

if __name__ == "__main__":
    controller = create_controller()
    controller.button_rotation_callback("clockwise")
    controller.send_message()
