xhost +local:root

docker image build -t ros2_dgui .     

docker run -it --env="DISPLAY" \
	--device=/dev/video0:/dev/video0 \
	-e DISPLAY=$DISPLAY \
	--env="QT_X11_NO_MITSHM=1" \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--privileged \
	-e "ROS_DOMAIN_ID=7" \
	--net=host \
	-v $(pwd):/root/ws/ros2_dgui \
	-v /dev/shm:/dev/shm \
	ros2_dgui

export containerId=$(docker ps -l -q)

