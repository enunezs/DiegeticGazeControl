#FROM ros:$ROS_DISTRO-ros-base	
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
	ros-$ROS_DISTRO-cv-bridge \
	ros-$ROS_DISTRO-vision-opencv \
	ros-$ROS_DISTRO-compressed-image-transport\
	ros-$ROS_DISTRO-image-transport

RUN apt-get update && apt-get install -y \ 
	python3-numpy \
	python3-pip

RUN apt-get update && apt-get install -y \ 
	python3-vcstool \
    	apt-utils \
    	dialog
    	

# ------

RUN pip3 install --upgrade pip

# Pupil Neon glasses
RUN pip3 install pupil-labs-realtime-api

# Glasses emulation (Via Mouse)
RUN pip3 install python-xlib pyautogui

# Other
RUN apt-get update && apt-get install -y \
	scrot \
	python3-tk\
	python3-dev \
	ros-$ROS_DISTRO-tf-transformations
    	#libopencv-dev 
    	#python3-opencv


#### SET ENVIRONMENT
WORKDIR $HOME/ws/ros2_dgui

RUN echo 'alias python="python3"' >> $HOME/.bashrc
RUN echo 'source /opt/ros/$ROS_DISTRO/setup.sh && colcon build' >> $HOME/.bashrc
RUN echo 'source install/setup.bash' >> $HOME/.bashrc

#CMD ["ros2", "launch", "demo_nodes_cpp", "talker_listener.launch.py"]
