# Set up

1. Open file explorer, go to `/home/emanuel/Documents/ROS2_Workspaces`
2. Open a terminal in this directory
3. Run the following command to install the required dependencies:

```bash
./docker/1_run_Nicole.sh
```

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
```

# Saving to git in vscode:

1. Open the source control tab in vscode (Ctrl + Shift + G) (source control)
2. Click on stage all changes (the + icon next to changes)
3. Write a commit message in the text box at the top (e.g., "Added new feature")
4. Click on the checkmark icon to commit the changes
