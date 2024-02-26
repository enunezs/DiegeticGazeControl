xhost +local:root


docker run -it \
	--env="DISPLAY" \
	--env="QT_X11_NO_MITSHM=1" \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--privileged \
	-e "ROS_DOMAIN_ID=7" \
	--net=host \
	-v /dev/shm:/dev/shm \
	osrf/ros:foxy-desktop \
	rqt_graph

export containerId=$(docker ps -l -q)


