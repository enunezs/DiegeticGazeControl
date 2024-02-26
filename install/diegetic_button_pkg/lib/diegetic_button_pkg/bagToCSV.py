#! /usr/bin/env python3

import rclpy
from rclpy.node import Node

# Messages
from sensor_msgs.msg import Image
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
from diegetic_button_pkg.msg import DiegeticButton
from diegetic_button_pkg.msg import DiegeticButtonArray
from std_msgs.msg import String
from diegetic_button_pkg.msg import InputStatus
from diegetic_button_pkg.msg import InputStatusArray

from std_msgs.msg import Float32
from std_msgs.msg import Float32MultiArray


# * Glasses messages
from tobii_glasses_pkg.msg import TobiiGlasses as TobiiGlassesMsg
from tobii_glasses_pkg.msg import EyeData as EyeDataMsg

from sensor_msgs.msg import Joy # TODO

# /tobii_glasses tobii_glasses/gaze_position /fiducial_transforms /button_transforms /joy


# For handling inputs
from pynput import keyboard  # import Listener, Key
# TODO: XBOX controller, or generic joystick

# For handling outputs
import serial
import time



# The following node listens to the following topics and stores the data in a csv file
# /tobii_glasses
# /fiducial_transforms
# /button_transforms
# /joy

class ToCSV(Node): 

    def __init__(self):

        # * Base node init
        super().__init__("process_inputs_node")

        # Initialize core button status list
        self.glasses_file = open('SubjectX_glasses.csv','w')
        string_data =  ('timestamp,  frame_id,  GazePosition_x,  GazePosition_y,  GazePosition3D_x,  GazePosition3D_y,  GazePosition3D_z,  GazePosMov,  LSensorError, RightPupilCentre_x, RightPupilCentre_y, RightPupilCentre_z, LeftPupilCentre_x, LeftPupilCentre_y, LeftPupilCentre_z, RightPupildiameter, LeftPupildiameter, RightPupilGazeDirection_x, RightPupilGazeDirection_y, RightPupilGazeDirection_z, LeftPupilGazeDirection_x, LeftPupilGazeDirection_y, LeftPupilGazeDirection_z, Accelerometer_x, Accelerometer_y, Accelerometer_z, Gyroscope_x, Gyroscope_y, Gyroscope_z\n')
        self.glasses_file.write(string_data)


        self.joy_file = open('SubjectX_joy.csv','w')
        string_data = ('timestamp,  frame_id,  S1X,  S1Y,  TL,  S2X,  S2Y,  TR,  DX,  DY,  A,  B,  X,  Y,  LB,  RB,  Select,  Start,  Xbox,  LJ,  RJ\n')
        self.joy_file.write(string_data)

        self.buttons_file = open('SubjectX_buttons.csv','w')
        string_data = ('timestamp, button_id, button_transform.translation.x, button_transform.translation.y, button_transform.translation.z, button_transform.rotation.x, button_transform.rotation.y, button_transform.rotation.z, button_transform.rotation.w\n')
        self.buttons_file.write(string_data)

        self.prev_time = self.get_clock().now()

        # add listeners to wanted topics 
        #self.create_subscription(Float32MultiArray, "/fiducial_transforms", self.glasses_fileiducial_callback, 10)
        #self.create_subscription(TobiiGlassesMsg, "/tobii_glasses", self.tobii_callback, 10)
        self.create_subscription(Joy, "/joy", self.joy_callback, 10)
        self.create_subscription(DiegeticButtonArray, "/button_transforms", self.button_callback, 10)
        #self.get_logger().info("process_inputs_node initialized")
        
    def button_callback(self, msg):
        print("Button callback")
        
        # turn header into a single number
        timestamp = (msg.header.stamp.sec + msg.header.stamp.nanosec/1000000000.0)

        message_data = (str(timestamp) )

        for button in msg.buttons:
            button_id = button.button_id
            button_transform = button.button_transform

            # convert to string 
            message_data = message_data + (',' + str(button_id) + ',' + str(button_transform.translation.x) + ',' + str(button_transform.translation.y) + ',' + str(button_transform.translation.z) + ',' + str(button_transform.rotation.x) + ',' + str(button_transform.rotation.y) + ',' + str(button_transform.rotation.z) + ',' + str(button_transform.rotation.w) )
            # separate the previous lines


        message_data = message_data + '\n'
        self.buttons_file.write(message_data)


    # Save joy data to csv
    def joy_callback(self, msg):
        print("Joy callback")
        
        # turn header into a single number
        timestamp = (msg.header.stamp.sec + msg.header.stamp.nanosec/1000000000.0)
        frame_id = msg.header.frame_id

        string_data = (str(timestamp) + ',' + str(frame_id) + ','
                    + str(msg.axes[0]) + ',' + str(msg.axes[1]) + ',' + str(msg.axes[2]) + ',' + str(msg.axes[3]) + ',' + str(msg.axes[4]) + ',' + str(msg.axes[5]) + ',' + str(msg.axes[6]) + ',' + str(msg.axes[7]) + ','
                    + str(msg.buttons[0]) + ',' + str(msg.buttons[1]) + ',' + str(msg.buttons[2]) + ',' + str(msg.buttons[3]) + ',' + str(msg.buttons[4]) + ',' + str(msg.buttons[5]) + ',' + str(msg.buttons[6]) + ',' + str(msg.buttons[7]) + ',' + str(msg.buttons[8]) + ',' + str(msg.buttons[9]) + ',' + str(msg.buttons[10]) +  '\n')
        # separate the previous lines

        self.joy_file.write(string_data)



    def tobii_callback(self, msg):
        #print individual parts of the message
        print("Tobii callback")
        # turn header into a single number
        timestamp = (msg.header.stamp.sec + msg.header.stamp.nanosec/1000000000.0)
        frame_id = msg.header.frame_id

        #print(msg.camera_image)
        # unpack gaze position
        gaze_position = msg.gaze_position
        # unpack gaze position 3D
        gaze_position_3d = msg.gaze_position_3d

        # unpack eye data
        right_eye = msg.right_eye
        left_eye = msg.left_eye
        
        # unpack pupil validity
        right_pupil_validity = right_eye.status
        left_pupil_validity = left_eye.status
        # unpack pupil center
        right_pupil_center = right_eye.pupil_center
        left_pupil_center = left_eye.pupil_center
        # unpack pupil diameter
        right_pupil_diameter = right_eye.pupil_diameter
        left_pupil_diameter = left_eye.pupil_diameter
        # unpack pupil gaze direction
        right_pupil_gaze_direction = right_eye.gaze_direction
        left_pupil_gaze_direction = left_eye.gaze_direction


        # unpack accelerometer
        accelerometer = msg.acelerometer
        # unpack gyroscope
        gyroscope = msg.gyroscope
        
        # store into csv file
        # fix the following line with the updated variable names
        
        

        string_data = (str(timestamp) + ',' + str(frame_id) + ',' 
                    + str(gaze_position[0]) + ',' + str(gaze_position[1]) + ',' 
                    + str(gaze_position_3d[0]) + ',' + str(gaze_position_3d[1]) + ',' + str(gaze_position_3d[2]) + ',' 
                    + str(right_pupil_validity) + ',' + str(left_pupil_validity) + ',' 
                    + str(right_pupil_center[0]) + ',' + str(right_pupil_center[1]) + ',' + str(right_pupil_center[2]) + ',' 
                    + str(left_pupil_center[0]) + ',' + str(left_pupil_center[1]) + ',' + str(left_pupil_center[2]) + ',' 
                    + str(right_pupil_diameter) + ',' 
                    + str(left_pupil_diameter) + ',' 
                    + str(right_pupil_gaze_direction[0]) + ','+ str(right_pupil_gaze_direction[1]) + ','+ str(right_pupil_gaze_direction[2]) + ',' 
                    + str(left_pupil_gaze_direction[0]) + ','+ str(left_pupil_gaze_direction[1]) + ','+ str(left_pupil_gaze_direction[2]) + ',' 
                    + str(accelerometer[0]) + ','+ str(accelerometer[1]) + ','+ str(accelerometer[2]) + ',' 
                    + str(gyroscope[0]) + ','+ str(gyroscope[1]) + ','+ str(gyroscope[2]) + '\n')
        # separate the previous lines

        self.glasses_file.write(string_data)



def main():
    rclpy.init()  # Initialize ROS DDS

    publisher = ToCSV()  # Create instance of function

    print('Storing to CSV running...')

    try:
        rclpy.spin(publisher)  # prevents closure. Run until interrupt
    except KeyboardInterrupt:
        # TODO : Save data to csv  

        cv2.destroyAllWindows()
        publisher.destroy_node()  # duh
        rclpy.shutdown()  # Shutdown DDS !


if __name__ == '__main__':
    main()
