xhost +local:root

docker image build -t diegetic_gaze_control:latest -f docker/Dockerfile docker     

docker run -it --env=DISPLAY=$DISPLAY \
	--device=/dev/video0:/dev/video0 \
	--env="QT_X11_NO_MITSHM=1" \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--privileged \
	--net=host \
	--volume $(pwd):/root/ws/DiegeticGazeControl \
	--volume /dev/shm:/dev/shm \
	--cap-add=NET_ADMIN \
	--cap-add=NET_RAW \
	--env=ROS_DOMAIN_ID=7 \
	diegetic_gaze_control:latest

	
export containerId=$(docker ps -l -q)

