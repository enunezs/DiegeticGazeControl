xhost +local:root

docker image build -t origami:latest -f docker/Dockerfile docker     

docker run -it --env="DISPLAY" \
	--device=/dev/video0:/dev/video0 \
	--env DISPLAY=$DISPLAY \
	--env="QT_X11_NO_MITSHM=1" \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--privileged \
	--env "ROS_DOMAIN_ID=7" \
	--net=host \
	--volume $(pwd):/root/ws/origami \
	--volume /dev/shm:/dev/shm \
	origami:latest

export containerId=$(docker ps -l -q)

