xhost +local:root
docker pull ros:humble-ros-base

# docker image build --no-cache  -t diegetic_gaze_control:latest -f docker/Dockerfile docker     
docker image build -t diegetic_gaze_control:latest -f docker/Dockerfile docker     

docker run -it --env=DISPLAY=$DISPLAY \
	--privileged \
	--device=/dev/video0:/dev/video0 \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--env="QT_X11_NO_MITSHM=1" \
	--net=host \
	--volume $(pwd):/root/ws/DiegeticGazeControl \
	--volume /home/emanuel/Documents/NicoleThings/SpeechSynthesisModels:/models \
	--volume /dev/shm:/dev/shm \
	--cap-add=NET_ADMIN \
	--cap-add=NET_RAW \
	--env=ROS_DOMAIN_ID=7 \
	diegetic_gaze_control:latest

# TODO: Add user chmod thing

	
export containerId=$(docker ps -l -q)

