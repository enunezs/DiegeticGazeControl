<p align="center">
  <img src="./doc/images/DiegeticGazeControlLogo.png" alt="Description Anim" width="400">
</p>

<a href="https://www.youtube.com/watch?v=hrXuNYLDFds&feature=youtu.be">
  <img src="https://img.shields.io/badge/youtube-d95652.svg?style=flat-square&logo=youtube" alt="youtube" style="height: 20px;">
</a>

[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/enunezs/diegetic_gaze_control/1.0?logo=docker)](https://hub.docker.com/repository/docker/enunezs/diegetic_gaze_control/general)

<p align="center">
<b>Diegetic Gaze Control</b> allows you to interact with printed paper interfaces, the world, and even robots, using only <b>your eye-gaze</b>.
</p>

<p align="center">
  <img src="./doc/images/DGUI_StartTrim.gif" alt="Description Anim" width="500">
</p>

<p align="center">
Define and interact with <b>printed interfaces</b> or with <b>everyday objects</b> directly.
</p>

<p align="center">
  <img src="./doc/images/DGUI_OtherInputsTrim.gif" alt="Description Anim" width="600">
</p>

Made with:

<p align="center">
  <img src="https://raw.githubusercontent.com/fkromer/awesome-ros2/master/ros_logo.svg?sanitize=true" alt="Description Anim" height="30" style="margin: 0 10px;">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/70/Docker_logo.png" alt="Description Anim" height="30" style="margin: 0 10px;">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/OpenCV_Logo_with_text.png/487px-OpenCV_Logo_with_text.png" alt="Description Anim" height="40" style="margin: 0 10px;">
</p>

---

The project is detailed in the preprint:

<p align="center">

  <a href="https://arxiv.org/abs/2401.03944">
  Diegetic Graphical User Interfaces and Intuitive Control of Assistive Robots via Eye-gaze
  </a>
</p>

---

## Contents
- [Why?](#why)
- [Setting up the software environment](#Software-Setup)
- [Hardware Setup](#Installation)
  - [Method 1: Setting Up Pupil Glasses](#Pupil-Neon-Glasses-Setup)
  - [Method 2: Webcam Setup](#Webcam-Setup)
- [Setting Up Robotic Arm](#Robotic-Arm-Setup)
- [Exploring Features](#Exploring-New-Features)
- [How does it work?](#How-Does-It-Work)
- [Citing The Work](#Citing-This-Work)


## why

<p align="center">
Our goal is to empower people with disabilities to interact with the world without constraining them to a screen.
</p>

- Compared to other approaches, gaze is always kept on the robot. This makes it easier, more intuitive and safer.
- Compared to screens, it does not constrain the user to a specific location.
- Paper interfaces are flexible, cheap, and easy to create and customise.
- No VR illness, no need for a large VR headset.

Our aim is to enable interaction with prepared environments via eye-gaze using ArUco markers. Using the **_Pupil Neon Glasses_**, the user's gaze is detected and used to interact with printed interfaces or everyday items. The **_final output is a `/joy` message_** in ROS2.

<p align="center">
  <img src="./doc/images/DGUI_DescriptionTrim.gif" alt="Description Anim" width="700">
</p>

---

## Installation

Navigate to a new workspace, then clone the repository with submodules:

```bash
git clone --recurse-submodules https://github.com/enunezs/DiegeticGazeControl
cd DiegeticGazeControl
```

This will add this repository and the [Pupil Neon Glasses repository](https://github.com/enunezs/pupil_neon_pkg/tree/release) in the `/src` folder

From the root of the repository, run the following command to **pull and run** the following [docker image](https://hub.docker.com/repository/docker/enunezs/diegetic_gaze_control/general) with:

```bash
./docker/1_dockerscript.sh
```

---

### Pupil Neon Glasses Setup

For some wearers, you may find a constant offset in their gaze estimates. To compensate for those, you can use the Offset Correction feature in the Neon Companion App. See the video below to learn how it works! Check https://docs.pupil-labs.com/neon/ for documentation.

[![Watch the video](https://img.youtube.com/vi/7weK8UPLOzo/0.jpg)](https://youtu.be/7weK8UPLOzo)

To **connect to the glasses and start** the gaze input to joystick output, first modify the `config.yaml` file in the `pupil_neon_pkg` package to match your glasses' IP address at `src/pupil_neon_pkg/config/config.yaml`.

Then run the following command:

```bash
ros2 launch diegetic_button_pkg eyes_to_joy.launch.py
```

### Webcam Setup

The laptop webcam can be used instead of the glasses with the use of a mouse for the focus.

Alternatively, you can run the following command to start the **emulated mode**, which will use a **webcam instead of the glasses**:

```bash
ros2 launch diegetic_button_pkg webcam_to_joy.launch.py
```

### Visualising Gaze Data

You can visualize the scene and gaze data by running the following command:

```bash
./docker/2_rviz2.sh
```

## How Does It Work

The following is a brief overview of the code structure. It is composed of three main packages:

![ImageProcessingDiagramAlt(1).png](<doc/images/ImageProcessingDiagramAlt(1).png>)

The project is workspace with three main components:

- **Input from the gaze-tracking glasses**, receiving a stream of the scene and gaze point data. This is captured and processed by the [`pupil_neon_pkg`](https://github.com/enunezs/pupil_neon_pkg) or the [`ros2_tobii_glasses2`](https://github.com/enunezs/ros2_tobii_glasses2) package, wrappers for their respective APIs. It outputs two messages: the gaze data (coordinates) and the scene image.

- **Detection of the Diegetic Buttons**, is processed by the [`fiducials`](/src/fiducials/) which detects the ArUco markers, and [`diegetic_button_pkg`](/src/diegetic_button_pkg/) which finds the button position relative to the fiducials.

- **Gaze interaction pipeline**, which is processed by the [`gaze_input`](/src/diegetic_button_pkg/) node. The node checks whether the user is looking at the buttons and filters or debounces depending on the preferred strategy. The button is then activated, and if desired, `/joy_message` is sent.

- **Robot control**, which is robot-dependant. It is handled by the [`ros2_franka`](https://github.com/enunezs/ros2_franka_docker) or [`ros2_jaco_controller`](https://github.com/enunezs/ros2_jaco_controller).

![Nodes2.png](doc/images/Nodes2.png)

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

