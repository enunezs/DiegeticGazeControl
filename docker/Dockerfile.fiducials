#FROM ros:$ROS_DISTRO-ros-base	
ARG ROS_DISTRO= humble 
FROM ros:$ROS_DISTRO-ros-base	
LABEL maintainer="Emanuel Nunez S gmail dot com"
ENV HOME /root
WORKDIR $HOME
SHELL ["/bin/bash", "-c"]
ARG ROS_DISTRO=foxy

# install ros2 packages
RUN apt-get update && apt-get install -y \ 
	ros-$ROS_DISTRO-cv-bridge \
	ros-$ROS_DISTRO-vision-opencv \
	ros-$ROS_DISTRO-compressed-image-transport\
	ros-$ROS_DISTRO-image-transport \
    ros-$ROS_DISTRO-tf-transformations

# install ros2 packages
RUN apt-get update && apt-get install -y \ 
	python3-numpy \
	python3-pip

RUN apt-get update && apt-get install -y \ 
	python3-vcstool \
    	apt-utils \
    	dialog
    	
# general utilities
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    gdb \
    vim \
    nano \
    python-dev \
    python3-pip \
    unzip


#pip3 install --no-cache-dir pyautogui 
RUN pip3 install --upgrade pip

# ARuco
RUN pip3 install transforms3d CairoSVG
RUN pip3 install opencv-contrib-python==4.3.0.38 # Last with backwards compatibility

RUN apt-get update && apt-get install -y \
	poppler-utils 
	
	

RUN pip3 install -U \
  	argcomplete \
	pyautogui

# Tobii glasses
RUN pip3 install -U \
	tobiiglassesctrl

# Glasses emulation (Via Mouse)
RUN pip3 install python-xlib

RUN apt-get update && apt-get install -y \
	scrot \
	python3-tk\
	python3-dev

#python-dev

    #libopencv-dev #python3-opencv


# digetic buttons
RUN pip3 install matplotlib \
	pynput \
	pyserial


# Patch 
# https://answers.ros.org/question/390451/colcon-build-fails-on-anything-with-messages-now-after-ubuntu-2004-$ROS_DISTRO-sudo-apt-upgrade/
#WORKDIR /opt/ros/$ROS_DISTRO/lib/
#RUN ln -s libfastrtps.so.2.1.2 libfastrtps.so.2.1.1

# piano
RUN apt-get update && apt-get install -y \
     libportaudio2


# Pupil Neon glasses
RUN pip3 install pupil-labs-realtime-api

RUN pip3 install pysinewave

# Patch 
# https://answers.ros.org/question/390451/colcon-build-fails-on-anything-with-messages-now-after-ubuntu-2004-foxy-sudo-apt-upgrade/
#WORKDIR /opt/ros/foxy/lib/
#RUN ln -s libfastrtps.so.2.1.2 libfastrtps.so.2.1.1


#### SET ENVIRONMENT
WORKDIR $HOME/ws/pupil

RUN echo 'alias python="python3"' >> $HOME/.bashrc
RUN echo 'source /opt/ros/humble/setup.sh && colcon build' >> $HOME/.bashrc
RUN echo 'source install/setup.bash' >> $HOME/.bashrc

#CMD ["ros2", "launch", "demo_nodes_cpp", "talker_listener.launch.py"]
