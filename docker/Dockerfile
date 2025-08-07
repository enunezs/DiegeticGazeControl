ARG ROS_DISTRO=humble
FROM ros:$ROS_DISTRO-ros-base
LABEL maintainer="Emanuel Nunez S gmail dot com"
ENV HOME /root
WORKDIR $HOME
SHELL ["/bin/bash", "-c"]

# Install ros2 packages
RUN apt-get update && apt-get install -y \ 
	ros-$ROS_DISTRO-cv-bridge \
	ros-$ROS_DISTRO-vision-opencv \
	ros-$ROS_DISTRO-compressed-image-transport\
	ros-$ROS_DISTRO-image-transport \
    ros-$ROS_DISTRO-tf-transformations \
    ros-$ROS_DISTRO-joy 
    
# General utilities
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    gdb \
    vim \
    nano \
	apt-utils \
	dialog \
	unzip \
	python3-vcstool

# Other tools
RUN apt-get update && apt-get install -y \
	scrot \
	python3-tk\
	python3-dev

# Install pip 
RUN apt-get update && apt-get install -y \ 
	python3-pip 
RUN pip3 install --upgrade pip

# Transformation packages
RUN apt-get update && apt-get install -y \ 
	python3-numpy

RUN pip3 install \
	transforms3d \
	scipy \
	matplotlib 

# Opencv from pip
RUN pip3 install argcomplete
# Last with backwards compatibility
RUN pip3 install --upgrade pip

# ARuco
RUN pip3 install CairoSVG
RUN apt-get update && apt-get install -y \ 
	poppler-utils

RUN pip3 install opencv-contrib-python

#	opencv-python-headless	\
# opencv-contrib-python==4.3.0.38 # Last with backwards compatibility

# Opencv from Ubuntu 
# JACK: Removed apt-update to avoid conflict with pip install
# RUN apt-get update && apt-get install -y \
#	libopencv-dev \
#	python3-opencv """
    
# QT GUI Dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-glx0 \
    libxcb-keysyms1 \
    libxcb-image0 \
    libxcb-shm0 \
    libxcb-icccm4 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libxkbcommon0 \
    x11-apps \
    xauth \
    xorg \
    libgl1-mesa-glx \
    libgl1-mesa-dri


#'stevedore>=1.3.0,<1.4.0'
RUN apt-get update && apt-get install -y \
	ffmpeg \
	libsm6 \
	libxext6  

# --- PUPIL GLASSES
RUN pip3 install pupil-labs-realtime-api

# Glasses emulation (Via Mouse)
RUN pip3 install python-xlib pyautogui

# Installing pyqt5 and dependencies
RUN apt-get update && apt-get install -y \
    python3-pyqt5 \
    python3-pyqt5.qtsvg \
    python3-pyqt5.qtwebengine \
    python3-pyqt5.qtmultimedia \
    python3-pyqt5.qtquick \
    python3-pyqt5.qtwebsockets

# JACK: Added for GUI 
ENV QT_QPA_PLATFORM=xcb
ENV QT_X11_NO_MITSHM=1

# --- Digetic Buttons
RUN pip3 install matplotlib \
	pynput 

# --- E-ink Display
RUN pip3 install paho-mqtt

# --- Piano
RUN pip3 install pysinewave
RUN apt-get update && apt-get install -y \
     libportaudio2
     
#RUN cd src/diegetic_button_pkg/scripts/pyfluidsynth-master/ && \
#	pip3 install pyfluidsynth

# SET ENVIRONMENT
WORKDIR $HOME/ws/DiegeticGazeControl

RUN echo 'alias python="python3"' >> $HOME/.bashrc
RUN echo 'source /opt/ros/humble/setup.sh && colcon build' >> $HOME/.bashrc
RUN echo 'source install/setup.bash' >> $HOME/.bashrc


