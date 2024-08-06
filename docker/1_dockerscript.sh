#!/bin/bash
xhost +local:root

docker pull enunezs/diegetic_gaze_control:1.1

docker run -it \
	--env="DISPLAY" \
	--device=/dev/video0:/dev/video0 \
	--env DISPLAY=$DISPLAY \
	--env="QT_X11_NO_MITSHM=1" \
	--privileged \
	--net=host \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--volume="$HOME/.Xauthority:/root/.Xauthority" \
	--volume $(pwd):/root/ws/DiegeticGazeControl \
	--volume /dev/shm:/dev/shm \
	enunezs/diegetic_gaze_control:1.1
#	--env "ROS_DOMAIN_ID=7" \

export containerId=$(docker ps -l -q)
