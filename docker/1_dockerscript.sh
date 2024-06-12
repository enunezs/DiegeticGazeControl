#!/bin/bash

docker pull enunezs/diegetic_gaze_control:1.0

docker run -it \
	--env="DISPLAY" \
	--device=/dev/video0:/dev/video0 \
	--env DISPLAY=$DISPLAY \
	--env="QT_X11_NO_MITSHM=1" \
	--privileged \
	--net=host \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--volume $(pwd):/root/ws/DiegeticGazeControl \
	--volume /dev/shm:/dev/shm \
	enunezs/diegetic_gaze_control:1.0

export containerId=$(docker ps -l -q)
