# Diegetic Gaze Control

<p align="center">
  <img src="./doc/images/DiegeticGazeControlLogo.png" alt="Diegetic Gaze Control Logo" width="400">
</p>

<a href="https://www.youtube.com/watch?v=hrXuNYLDFds&feature=youtu.be">
  <img src="https://img.shields.io/badge/youtube-d95652.svg?style=flat-square&logo=youtube" alt="youtube" style="height: 20px;">
</a>

[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/enunezs/diegetic_gaze_control/1.0?logo=docker)](https://hub.docker.com/repository/docker/enunezs/diegetic_gaze_control/general)

---

## Introduction

Diegetic Gaze Control is an innovative system designed to enable intuitive interaction with printed paper interfaces, physical environments, and robots using only your eye-gaze. This project aims to empower individuals, particularly those with disabilities, by providing a natural and seamless way to control assistive devices without the constraints of traditional screens or complex hardware.

At the core of Diegetic Gaze Control is the use of gaze-tracking glasses such as Pupil Neon Glasses or Tobii Glasses Pro 2. These glasses capture the user’s eye movements and translate them into control signals for interacting with printed interfaces or everyday objects. The system utilizes ArUco markers for precise detection and interaction, ensuring that users can effortlessly engage with their surroundings.

This project leverages several powerful technologies, including ROS2 for robotic control, Docker for easy deployment, and OpenCV for image processing. By integrating these tools, Diegetic Gaze Control provides a robust and flexible platform for research and practical applications in assistive technology.

### Key Features

- **Intuitive Interaction**: Control interfaces and objects with eye-gaze, maintaining a natural and comfortable user experience.
- **Versatile Hardware**: Compatible with Pupil Neon Glasses, Tobii Glasses Pro 2, or a standard USB webcam.
- **Flexible Interfaces**: Use printed paper interfaces that are easy to create, customize, and replace.
- **Safe and Practical**: Keeps the user’s gaze on the task, enhancing safety and ease of use without causing VR sickness.
- **Robust Technology Stack**: Built on ROS2, Docker, and OpenCV for reliability and ease of deployment.

Diegetic Gaze Control is ideal for researchers, developers, and practitioners in the fields of assistive technology, human-computer interaction, and robotics. It provides a foundation for developing new applications that leverage eye-gaze for control and interaction, opening up new possibilities for empowering users and enhancing accessibility.

# Table of Contents

- [Introduction](#introduction)
- [Why?](#why)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Cloning](#cloning)
  - [Setting Up the Environment](#setting-up-the-environment)
- [Running](#running)
  - [Docker Setup](#docker-setup)
  - [Configuration](#configuration)
  - [Starting the Application](#starting-the-application)
- [How Does It Work?](#how-does-it-work)
  - [Code Structure](#code-structure)
  - [Launch Files](#launch-files)
- [Contribution Guidelines](#contribution-guidelines)

# Why?

<p align="center">
Our goal is to empower people with disabilities to interact with the world without constraining them to a screen.
</p>

## Motivation

The primary motivation behind Diegetic Gaze Control is to enhance the accessibility and usability of assistive technologies. Traditional control methods often rely on touchscreens, keyboards, or mouse devices, which can be cumbersome or even unusable for individuals with physical disabilities. By leveraging eye-gaze as a natural and intuitive input method, we aim to provide a more inclusive solution that enables users to interact with their environment seamlessly and independently.

## Key Advantages

### Intuitive and Natural Interaction
Diegetic Gaze Control keeps the user's gaze focused on the task at hand. Unlike screen-based interfaces, where attention is divided between the screen and the environment, our system allows for direct interaction with physical objects and printed interfaces. This approach not only enhances user experience but also reduces cognitive load and improves task efficiency.

### Versatility and Flexibility
- **Hardware Compatibility**: The system supports a range of gaze-tracking devices, including Pupil Neon Glasses, Tobii Glasses Pro 2, and even standard USB webcams. This flexibility ensures that users can choose the hardware that best fits their needs and budget.
- **Printed Interfaces**: Using printed paper interfaces provides a cost-effective and easily customizable solution. Users can create and modify their own control interfaces without the need for expensive equipment or software.

### Safety and Comfort
By keeping the user’s gaze on the robot or task, Diegetic Gaze Control enhances safety and usability. This is particularly beneficial in environments where situational awareness is crucial. Additionally, the system avoids the discomfort and potential VR sickness associated with wearing large VR headsets.

### Open and Extensible
Built on robust and widely-used technologies like ROS2, Docker, and OpenCV, Diegetic Gaze Control is designed to be easily extensible. Researchers and developers can build upon this platform to create new applications and functionalities, fostering innovation in the field of assistive technology.

## Real-World Applications

Diegetic Gaze Control has numerous potential applications:
- **Assistive Devices**: Empower individuals with disabilities to control various assistive devices, enhancing their independence and quality of life.
- **Human-Robot Interaction**: Facilitate more natural and efficient interactions between humans and robots in both industrial and domestic settings.
- **Education and Training**: Provide accessible learning tools and interfaces for students and trainees with physical limitations.

# Prerequisites

Before you begin, ensure you have met the following requirements:

## Hardware Requirements

- **Gaze-Tracking Glasses**: Pupil Neon Glasses or Tobii Glasses Pro 2 for accurate eye-tracking. Alternatively, a standard USB webcam can be used for emulated mode.
- **Computer**: A machine capable of running Docker. Ideally, it should have a modern CPU and at least 8GB of RAM to handle the image processing and Docker containers efficiently.
- **Printer**: For printing the sample control interfaces with ArUco markers. This can be a standard inkjet or laser printer.

## Software Requirements

- **Operating System**: Any OS that supports Docker. While Linux (especially Ubuntu 20.04 LTS or later) is recommended for ROS2 compatibility, Docker abstracts most OS-specific dependencies.
- **Docker**: Docker is used to containerize the application for easier deployment. [Install Docker here](https://docs.docker.com/get-docker/)

## Additional Dependencies

- **Python**: Python 3.8 or later. Ensure you have `pip` for managing Python packages (if running locally outside Docker).
- **OpenCV**: Required for image processing. Install it using `pip install opencv-python` (if running locally outside Docker).
- **ArUco**: For detecting ArUco markers. This is typically included with OpenCV, but ensure it is installed and available (if running locally outside Docker).
- **Pupil Labs Software**: If using Pupil Neon Glasses, ensure you have the necessary software and drivers installed. [Pupil Labs Documentation](https://docs.pupil-labs.com/)
- **Tobii Pro SDK**: If using Tobii Glasses Pro 2, ensure the Tobii Pro SDK is installed. [Tobii Pro SDK Documentation](https://developer.tobii.com/tobii-pro-sdk/)

## Printing the Sample Control Interface

- Download the sample control interface from the [printables directory](src/diegetic_button_pkg/printables/).
- Print the interface on standard A4 or Letter-sized paper.

## Network Requirements

- Ensure that the gaze-tracking glasses are on the same network as your computer if using wireless communication.
- If using Docker, ensure your firewall and security settings allow Docker to communicate with the necessary devices and networks.

## Environment Setup

### Cloning the Repository

Navigate to a new workspace and clone the repository with submodules:

```bash
git clone --recurse-submodules https://github.com/enunezs/DiegeticGazeControl
cd DiegeticGazeControl
```

## Setting Up Docker Environment

From the root of the repository, run the Docker setup script:

```bash
./docker/1_dockerscript.sh
```

## Configuring the System

To connect to the glasses and start the gaze input to joystick output, modify the config.yaml file in the pupil_neon_pkg package to match your glasses' IP address:

```bash
nano src/pupil_neon_pkg/config/config.yaml
```
## Starting the Application

To start the application using Docker, run:

```bash
ros2 launch diegetic_button_pkg eyes_to_joy.launch.py
```
Alternatively, to start the emulated mode using a webcam instead of the glasses, run:

```bash
ros2 launch diegetic_button_pkg webcam_to_joy.launch.py
```
You can visualize the scene and gaze data by running:
```bash
./docker/2_rviz.sh
```
## How it Works

The Diegetic Gaze Control system allows you to interact with your environment using just your eye-gaze. Here's a closer look at how everything fits together:

### System Overview

The system is composed of three main components, each playing a crucial role in enabling eye-gaze interactions:

1. **Input from Gaze-Tracking Glasses:**
   - **Capture Data:** The system uses Pupil Neon Glasses or Tobii Glasses Pro 2 to capture scene images and gaze points.
   - **Process Data:** This data is processed by the [`pupil_neon_pkg`](https://github.com/enunezs/pupil_neon_pkg) or [`ros2_tobii_glasses2`](https://github.com/enunezs/ros2_tobii_glasses2) package.
   - **Output:** The result is two messages: gaze data (coordinates) and the scene image.

2. **Detection of Diegetic Buttons:**
   - **Detect ArUco Markers:** The [`fiducials`](/src/fiducials/) package detects ArUco markers in the scene.
   - **Locate Buttons:** The [`diegetic_button_pkg`](/src/diegetic_button_pkg/) package determines button positions relative to the detected markers.

3. **Gaze Interaction Pipeline:**
   - **Process Gaze Data:** The [`gaze_input`](/src/diegetic_button_pkg/) node analyzes if the user is looking at a button.
   - **Activate Button:** When a gaze is detected on a button, it activates, sending a `/joy` message.

### Interactive Workflow

1. **Initialization:**
   - **Start the System:** Begin by initializing the system to capture data from your gaze-tracking glasses or webcam.

2. **Data Processing:**
   - **Real-Time Analysis:** The system processes the scene image and gaze data to detect ArUco markers and determine button positions.
   - **Visual Feedback:** You can visualize the scene and gaze data, providing real-time feedback on what the system sees.

3. **Gaze Detection and Interaction:**
   - **Continuous Monitoring:** The system continuously checks if you're looking at a button.
   - **Immediate Response:** When your gaze is detected on a button, it instantly activates, triggering a corresponding action via a `/joy` message.

### Robot Control

Once a button is activated, the system sends a `/joy` message to control the robot. The specific robot control is managed by:
- [`ros2_franka`](https://github.com/enunezs/ros2_franka_docker)
- [`ros2_jaco_controller`](https://github.com/enunezs/ros2_jaco_controller)

### Launch Files

Get started quickly with these launch files:

- **`eyes_to_joy.launch.py`:** Launches nodes for gaze input to joystick output.
- **`webcam_to_joy.launch.py`:** Starts the emulated mode using a webcam.

![System Overview](doc/images/ImageProcessingDiagramAlt(1).png)
![Node Architecture](doc/images/Nodes2.png)

---

### See it in Action!

Watch our demo video to see the Diegetic Gaze Control system in action and understand how it can empower users through intuitive eye-gaze interactions.

[![Watch the video](https://img.shields.io/badge/youtube-d95652.svg?style=flat-square&logo=youtube)](https://www.youtube.com/watch?v=hrXuNYLDFds&feature=youtu.be)

## Citing this work

If you use this repository in your research, please cite the following:

```
@software{NunezSardinha2024_DGUI,
author = {Emanuel, Nunez Sardinha and Marcela, Munera and Nancy, Zook and David, Western and Virginia, Ruiz Garate},
doi = {pending},
month = june,
title = {{Diegetic Graphical User Interfaces \& Intuitive
Control of Assistive Robots via Eye-gaze}},
url = {https://github.com/enunezs/DiegeticGazeControl},
version = {1.0},
year = {2024}
}
```



