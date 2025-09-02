#!/bin/bash

echo "Current DISPLAY: $DISPLAY"
echo "Allowing X11 connections..."
xhost +local:root

# Alternative script with environment variables for ROS parameters
echo "Starting RViz2 container with ROS parameters..."
docker run -it \
	--env="DISPLAY=$DISPLAY" \
	--env="QT_X11_NO_MITSHM=1" \
	--env="XDG_RUNTIME_DIR=/tmp/runtime-root" \
	--env="QT_LOGGING_RULES=*.debug=false;qt.qpa.*=false" \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--volume="/run/user/$(id -u)/pulse:/run/user/1000/pulse" \
	--volume="$HOME/.Xauthority:/root/.Xauthority:rw" \
	--volume="$(pwd)/config:/workspace/config" \
	--volume="$(pwd)/src:/workspace/src" \
	--privileged \
	--net=host \
	-v /dev/shm:/dev/shm \
	--env="ROS_DOMAIN_ID=7" \
	osrf/ros:humble-desktop \
	bash -c "
	    mkdir -p /tmp/runtime-root && chmod 700 /tmp/runtime-root &&
		source /opt/ros/humble/setup.bash && 
		rviz2 -d /workspace/config/rviz_config.rviz --ros-args --remap __ns:=/robot"

export containerId=$(docker ps -l -q)
