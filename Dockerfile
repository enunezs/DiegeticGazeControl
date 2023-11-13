ARG ROS_DISTRO=humble
FROM ros:$ROS_DISTRO-ros-base
LABEL maintainer="Emanuel Nunez S gmail dot com"
ENV HOME /root
WORKDIR $HOME
SHELL ["/bin/bash", "-c"]

# general utilities
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    gdb \
    vim \
    nano \
    python3-pip \
    unzip


# install ros2 packages
RUN apt-get update && apt-get install -y \ 
	python3-numpy \
	python3-pip

RUN apt-get update && apt-get install -y \ 
	python3-vcstool \
    	apt-utils \
    	dialog
    	

# install ros2 packages
RUN apt-get update && apt-get install -y \ 
	ros-$ROS_DISTRO-cv-bridge \
	ros-$ROS_DISTRO-vision-opencv \
	ros-$ROS_DISTRO-compressed-image-transport\
	ros-$ROS_DISTRO-image-transport


#pip3 install --no-cache-dir pyautogui 
#RUN pip3 install --upgrade pip



RUN pip3 install -U \
  	argcomplete \
	pupil-labs-realtime-api \
	matplotlib \
	'opencv-python<=4.8.0.74'

#'stevedore>=1.3.0,<1.4.0'

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# SET ENVIRONMENT
WORKDIR $HOME/ws/origami


