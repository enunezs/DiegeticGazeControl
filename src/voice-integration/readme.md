# Nicole's Voice Recognition on ROS2

This project does...

## Running

### Running the Docker container

1. Open file explorer, go to `/home/emanuel/Documents/ROS2_Workspaces/Nicole_DiegeticGazeControl`
2. Open a terminal in this directory
3. Run the following command to install the required dependencies:

```bash
./docker/1_run_Nicole.sh
```

4. To run the ROS2 nodes, follow the instructions below:

```bash
ros2 run voice-integration supervisor_node2.py

or

ros2 run voice-integration automatic_speech_recognition_node.py
```

or

ros2 run voice-integration robot_actions.py

### Open command logger

cat command_log.csv

or

libreoffice command_log.csv

# Watch log update live

tail -f command_log.csv

### Robot communication

1. Go to `/home/emanuel/Documents/ROS2_Workspaces/jacoarm-ros2` and open a terminal
2. Run the following command to start the ROS2 nodes:

```bash
./docker/1_dockerscript.sh
```

3. To connect to the robot, run the following command in a terminal inside the Docker container:

```bash
colcon build --packages-select jacoarm-ros2 && source install/setup.bash
```

4. And then to run the robot driver:

```bash
ros2 launch jacoarm-ros2 jaco_with_moveit.launch.py
```

If everything is correct, a window with Rviz will pop, and the robot hand should open

6. Repeat 1-3 on a new terminal, and run:

```bash
ros2 launch jacoarm-ros2 main_controller.launch.py
```

The robot will now move to point down. You can now send messages to the /waypoint_trigger topic to move the robot to different positions.

---

# testing robot behaviour

5. To test the robot's response to voice commands, you can publish messages to the relevant ROS2 topics. For example, run the following command in a terminal:

```bash
ros2 topic pub /waypoint_trigger std_msgs/msg/String "data: 'Go'"  --once
```

# Other stuff

````bash

To get the current robot position, run:

ros2 topic echo /j2n6s300_driver/out/tool_pose

PENDING: Add instructions on how to launch

---

docker start quirky_mendel
docker exec -it quirky_mendel bash

cd /root/ws/DiegeticGazeControl

# Speech system package (need to be here to run the supervisor and ASR nodes):

cd src/speech_system/speech_system

# Open supervisor and ASR node:

nano src/speech_system/speech_system/asr_node.py

# do the same for supervisor_node.py

# After editing need to build again:

colcon build
source install/setup.bash

# Source ROS2 workspace

source /opt/ros/humble/setup.bash
source install/setup.bash

# Run nodes:

ros2 run speech_system supervisor_node

# In another terminal, run the following command to start the ASR node:

In the terminal, run the following command to start the ROS2 nodes:

```bash
python3 src/voice-integration/scripts/voice_integration1.py
````

# Testing robot's response:

ros2 topic pub /j2n6s300_driver/in/cartesian_velocity geometry_msgs/Twist "{linear: {x: 0.1}}"

# Saving to git in vscode:

1. Open the source control tab in vscode (Ctrl + Shift + G) (source control)
2. Click on stage all changes (the + icon next to changes)
3. Write a commit message in the text box at the top (e.g., "Added new feature")
4. Click on the checkmark icon to commit the changes
