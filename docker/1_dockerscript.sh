xhost +local:root

#docker image build -t origami:1.0 -f docker/Dockerfile docker     
docker pull enunezs/origami:1.0

docker run -it --env="DISPLAY" \
	--device=/dev/video0:/dev/video0 \
	--env DISPLAY=$DISPLAY \
	--env="QT_X11_NO_MITSHM=1" \
	--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	--privileged \
	--net=host \
	--volume $(pwd):/root/ws/origami \
	--volume /dev/shm:/dev/shm \
	enunezs/origami:1.0
#	--env "ROS_DOMAIN_ID=7" \


export containerId=$(docker ps -l -q)
