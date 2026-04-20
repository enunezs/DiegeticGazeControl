ARG ROS_DISTRO=humble
FROM ros:$ROS_DISTRO-ros-base
LABEL maintainer="Emanuel Nunez S gmail dot com"
ENV HOME=/root
WORKDIR $HOME
SHELL ["/bin/bash", "-c"]




# Set environment variables for OpenCV
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists and install basic utilities
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
    python3-vcstool \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --upgrade pip

# Install specific numpy version FIRST (critical for cv_bridge and OpenCV compatibility)
# Use system numpy to avoid version conflicts with precompiled OpenCV
RUN apt-get update && apt-get install -y \
    python3-numpy \
    python3-numpy-dev \
    && rm -rf /var/lib/apt/lists/*

# Lock pip numpy to match system version and prevent upgrades
# RUN pip3 install "numpy>=1.21.0,<1.25.0" --force-reinstall
RUN pip3 install numpy==1.23.5 --force-reinstall

# Install OpenCV system dependencies
RUN apt-get update && apt-get install -y \
    libopencv-dev \
    libopencv-contrib-dev \
    python3-opencv \
    libgtk-3-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Install ROS2 packages (after OpenCV dependencies)
RUN apt-get update && apt-get install -y \
    ros-$ROS_DISTRO-cv-bridge \
    ros-$ROS_DISTRO-vision-opencv \
    ros-$ROS_DISTRO-compressed-image-transport \
    ros-$ROS_DISTRO-image-transport \
    ros-$ROS_DISTRO-tf-transformations \
    ros-$ROS_DISTRO-joy \
    && rm -rf /var/lib/apt/lists/*

# Install Python scientific packages (maintaining strict numpy version constraint)
RUN pip3 install --no-deps \
    scipy \
    matplotlib \
    transforms3d \
    argcomplete

# Install scikit-learn (compatible with NumPy 1.23.x)
RUN pip3 install \
    scikit-learn==1.1.3

# Reinstall dependencies that scipy/matplotlib need, but control numpy version
RUN pip3 install \
    python-dateutil \
    pyparsing==3.0.9 \
    cycler \
    kiwisolver \
    pillow \
    fonttools \
    packaging

# Additional multimedia libraries
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    scrot \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install application-specific packages
RUN pip3 install \
    pupil-labs-realtime-api \
    python-xlib \
    pyautogui \
    CairoSVG


# Install X11 and Qt dependencies for PySide6
RUN apt-get update && apt-get install -y \
    libxcb-cursor0 \
    libxcb-cursor-dev \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libxkbcommon0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libdbus-1-3 \
    libfontconfig1 \
    libx11-xcb1 \
    libegl1 \
    libxcb-glx0 \
    && rm -rf /var/lib/apt/lists/*

    
# Install PySide6 for GUI applications
RUN pip3 install \
     pyside6

# Install sound and text-to-speech engine
RUN apt-get update && apt-get install -y \
    alsa-utils \
    espeak-ng \
    libespeak1 \
    ffmpeg


RUN pip3 install \
    pyttsx3 \
    gTTS \
    pydub \ 
    playsound==1.2.2 \
    pyttsx3 \
    simpleaudio

RUN pip3 install \
    python3-pytest

# Network configuration for RTP streams
RUN echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf && \
    echo 'net.core.rmem_default = 65536' >> /etc/sysctl.conf

# Set up environment
WORKDIR $HOME/ws/DiegeticGazeControl

# Configure bash environment
RUN echo 'alias python="python3"' >> $HOME/.bashrc && \
    echo 'source /opt/ros/humble/setup.bash && colcon build' >> $HOME/.bashrc && \
    echo 'source install/setup.bash' >> $HOME/.bashrc

# Verification step - check OpenCV installation
RUN python3 -c "import numpy; print('NumPy version:', numpy.__version__)" && \
    python3 -c "import cv2; print('OpenCV version:', cv2.__version__); print('OpenCV build info:'); print(cv2.getBuildInformation())"



RUN python3 - <<EOF
import matplotlib
import pyparsing
from sklearn.linear_model import Ridge
from scipy.stats import binned_statistic_2d
print("matplotlib:", matplotlib.__version__)
print("pyparsing:", pyparsing.__version__)
print("All scientific imports OK")
EOF

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]