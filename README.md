<p align="center"style="font-family: 'Courier New', Courier, monospace; font-size: 40px;">Diegetic Gaze Control</p>

`Diegetic Gaze Control` lets you **interact** with printed paper interfaces, the world and robots using your **eye-gaze**.

<h4 align="center">
  <a href="https://www.youtube.com/watch?v=hrXuNYLDFds&feature=youtu.be">
    <img src="https://img.shields.io/badge/youtube-d95652.svg?style=flat-square&logo=youtube" alt="youtube" style="height: 20px;">
  </a>
<img src='https://img.shields.io/github/v/release/enunezs/origami/?color=%23FDD835&label=version&style=for-the-badge'>
</h4>

<p align="center">
  <img src="./doc/DGUI_StartTrim.gif" alt="Description Anim" width="500">
</p>

Define and interact with **printed interfaces** or with **everyday objects** directly .

<p align="center">
  <img src="./doc/DGUI_OtherInputsTrim.gif" alt="Description Anim" width="600">
</p>

Our goal is to empower people with dissabilities to interact with the world around them, without constraining them to a screen.

<p align="center">
  <img src="https://raw.githubusercontent.com/fkromer/awesome-ros2/master/ros_logo.svg?sanitize=true" alt="Description Anim" width="100">
  ^^^
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/70/Docker_logo.png" alt="Description Anim" width="100">
</p>

<p align="center">
  The project is detailed in the preprint

  <a href="https://arxiv.org/abs/2401.03944">
  Diegetic Graphical User Interfaces and Intuitive Control of Assistive Robots via Eye-gaze
  </a>
</p>

# Pending

- [ ] Docker?
- [ ] Other repos

---

## Table of Contents

- [Pending](#pending)
  - [Table of Contents](#table-of-contents)
- [Why?](#why)
- [How does it work?](#how-does-it-work)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running](#running)
  - [Gaze input to joystick output](#gaze-input-to-joystick-output)
  - [Emulated/Developer mode](#emulateddeveloper-mode)
    - [Pupil Neon Pkg](#pupil-neon-pkg)
    - [Fiducials / ArUco detection \[\[source\]\](](#fiducials--aruco-detection-source)
    - [Diegetic button pkg](#diegetic-button-pkg)
    - [Launch files](#launch-files)
- [License](#license)
- [Cite this repository](#cite-this-repository)

# Why?

- Interfaces are flexible, cheap, and easy to create.
- Compared to screens, it doesnt constrain the user to a specific location.
- No VR illness, no need for a large VR headset.

aims to enable interaction with prepared environments via eye-gaze using ArUco markers. Using the **_Pupil Neon Glasses_**, the user's gaze is detected and used to interact with printed interfaces or everyday items. The **_final output will be joy signals_** in ROS2.

<p align="center">

[![DGUI V2-1](http://img.youtube.com/vi/hrXuNYLDFds/0.jpg)](https://www.youtube.com/watch?v=hrXuNYLDFds)

</p>

# How does it work?

<p align="center">
  <img src="./doc/DGUI_DescriptionTrim.gif" alt="Description Anim" width="600">
</p>

The following is a brief overview of the code structure. It is composed of three main packages:

![ImageProcessingDiagramAlt(1).png](<doc/ImageProcessingDiagramAlt(1).png>)

The project is workspace with three main components:

- **Input from the gaze-tracking glasses**, receiving a stream of the scene and gaze point data. This is captured and processed by the `pupil_neon_pkg` or the `tobii_pro` package.

- **Detection of the Diegetic Buttons**, which is processed by the `aruco_pkg` and `diegetic_button_pkg` packages. The `aruco_pkg` package detects the ArUco markers in the environment, while the `diegetic_button_pkg` package performs all the transformations and calculations to find the button position relative to the ArUco markers.

- **Gaze interaction pipeline**, which is processed by the `input_check` node. The `input_check` node checks whether the user is looking at the buttons and filters or debounces depending on the preferred strategy. The button is then activated, and if desired, `joy_message` is sent.

The third package performs all the transformations and calculations to find the button position relative to the ArUco markers. The `input_check` node checks whether the user is looking at a button or not. It receives the gaze data and uses it to determine which button the user is looking at. The button is then activated, and the joystick signals are output.

![Nodes2.png](Nodes2.png)

---

# Prerequisites

- Pupil Neon Glasses, Tobii Glasses Pro 2 OR a webcam, ideally an external (USB) one.
- Optionally for a quick start, Docker. [Install Docker here](https://docs.docker.com/get-docker/)
- Print the sample control interface on paper (see [here](/src/diegetic_button_pkg/printables/)).

# Installation

Navigate to a new workspace, then clone the repository with submodules:

```bash
mkdir ws
cd ws
git clone --recurse-submodules https://github.com/enunezs/origami
cd origami
```

NOTE: On linux, you need to use Ctrk+Shift+V to paste in the terminal!

This will add this repository and the [Pupil Neon Glasses repository](https://github.com/enunezs/pupil_neon_pkg/tree/release) in the `/src` folder

# Running

From the root of the repository, run the following command to **pull and run** the docker image:

```bash
./docker/1_dockerscript.sh
```

You need to have your Docker set up for this to work.

## Gaze input to joystick output

To connect to the glasses and start the gaze input to joystick output, run the following command:

```bash
ros2 launch diegetic_button_pkg devel.launch.py
```

## Emulated/Developer mode

...alternatively, you can run the following command to start the emulated mode, which will use a webcam instead of the glasses:

```bash
ros2 launch diegetic_button_pkg devel.launch.py
```

---

### Pupil Neon Pkg

- `pupil_neon_pkg`: The package for connecting to the glasses and receiving the gaze data. It acts as a wrapper for the Pupil Labs API, and it is used to connect to the glasses and receive the gaze data. It outputs two messages: the gaze data (coordinates) and the scene image.
  [See the package here](/src/pupil_neon_pkg/)

### Fiducials / ArUco detection [[source]](

- `aruco_pkg`: The package for detecting ArUco markers in the environment. It is used to detect the ArUco markers in the environment and to determine the user's gaze point. It wraps parts of the opencv library to detect the markers and calculate the gaze point. It outputs the position of the markers and their number code associated to each.
  [See the package here](/src/aruco_pkg/)

### Diegetic button pkg

- `diegetic_button`: Performs all the transformations and calculations to find the button position relative to the ArUco markers.

- `input_check`: Checks whether the user is looking at a button or not. It receives the gaze data, and it then uses the gaze data to determine which button the user is looking at. The button is then activated. It outputs the joystick signals.

[See the package here](/src/diegetic_button_pkg/)

### Launch files

- `eyes_to_joy.launch.py`: The main launch file, which launches all the previous nodes.
- `webcam_to_joy.launch.py`: The launch file for the emulated mode, which uses a webcam instead of the glasses.

[See scripts here](/src/diegetic_button_pkg/launch/)

---

# License

---

# Cite this repository

If you use this repository in your research, please cite the following:

```
@software{NunezSardinha2024,
author = {Emanuel, Nunez Sardinha and Marcela, Munera and Nancy, Zook and David, Western and Virginia, Ruiz Garate},
doi = {pending},
month = nov,
title = {{Diegetic Graphical User Interfaces 2}},
url = {https://github.com/enunezs/Origami},
version = {2.0},
year = {2024}
}
```
