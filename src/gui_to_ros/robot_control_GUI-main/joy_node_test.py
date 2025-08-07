from controller_publisher_base import ControllerPublisherBase

class ControllerPublisher(ControllerPublisherBase):
        def __init__(self):
            self.current_joy_msg = {
                "Axes": [0.0] * 8, 
                "Buttons": [0] * 11
                }

        def reset_publish_msg(self):
            self.current_joy_msg = {
                "Axes": [0.0] * 8, 
                "Buttons": [0] * 11
                }

        def window_rotation_callback(self, coordinates):
            msg = self.current_joy_msg
            msg["Axes"][0] = coordinates[0]
            msg["Axes"][1] = coordinates[1]

        def window_translation_callback(self, coordinates):
            msg = self.current_joy_msg
            msg["Axes"][2] = coordinates[0]
            msg["Axes"][3] = coordinates[1]

        def button_translation_callback(self, direction):
            msg = self.current_joy_msg
            if direction == "forward":
                msg["Axes"][4] = 1
            elif direction == "backward":
                msg["Axes"][4] = -1

        def timer_callback(self):
            pass

        def button_rotation_callback(self, direction):
            msg = self.current_joy_msg
            if direction == "clockwise":
                msg["Axes"][1] = 1
            elif direction == "anticlockwise":
                msg["Axes"][1] = -1
            else:
                print("Incorrect if statement selected!")

        def send_message(self):
            print(self.current_joy_msg)
            self.reset_publish_msg()

if __name__ == "__main__":
    controller = ControllerPublisher()
    print("success!")

