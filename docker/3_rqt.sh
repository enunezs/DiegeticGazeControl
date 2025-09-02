#!/bin/bash

echo "Current DISPLAY: $DISPLAY"
echo "Allowing X11 connections..."
xhost +local:root

# Container parameters
ROS_DOMAIN_ID=7
DOCKER_IMAGE="osrf/ros:humble-desktop"
WORKSPACE_DIR="$(pwd)"
CONFIG_DIR="$WORKSPACE_DIR/config"
SRC_DIR="$WORKSPACE_DIR/src"

# Create runtime dir for XDG
mkdir -p /tmp/runtime-root && chmod 700 /tmp/runtime-root

# Run container with RQt
docker run -it \
    --env="DISPLAY=$DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --env="XDG_RUNTIME_DIR=/tmp/runtime-root" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="$HOME/.Xauthority:/root/.Xauthority:rw" \
    --volume="$CONFIG_DIR:/workspace/config" \
    --volume="$SRC_DIR:/workspace/src" \
    --privileged \
    --net=host \
    -v /dev/shm:/dev/shm \
    -e "ROS_DOMAIN_ID=$ROS_DOMAIN_ID" \
    $DOCKER_IMAGE \
    bash -c "
        source /opt/ros/humble/setup.bash &&
        rqt --perspective-file /workspace/config/rqt_config.perspective
    "

# Save container ID
export containerId=$(docker ps -l -q)
echo "Container started: $containerId"
