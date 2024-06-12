xhost +local:root

docker image build -t diegetic_gaze_control:latest -f docker/Dockerfile docker     

docker run -it --env="DISPLAY" \
	--device=/dev/video0:/dev/video0 \
	--env DISPLAY=$DISPLAY \
	--env="QT_X11_NO_MITSHM=1" \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--privileged \
	--net=host \
	--volume $(pwd):/root/ws/DiegeticGazeControl \
	--volume /dev/shm:/dev/shm \
	diegetic_gaze_control:latest

export containerId=$(docker ps -l -q)

