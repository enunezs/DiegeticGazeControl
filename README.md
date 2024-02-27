# Current Version: Origami

This project, as detailed in the paper [_"Pupil System: A Wearable Eye Tracking System for People with Severe Motor Impairments"_](https://arxiv.org/abs/2105.05782), aims to enable interaction with prepared environments via eye-gaze using ArUco markers. Using the **_Pupil Neon Glasses_**, the user's gaze is detected and used to interact with printed interfaces or everyday items. The **_final output will be joy signals_** in ROS2.

[![DGUI V2-1](http://img.youtube.com/vi/hrXuNYLDFds/0.jpg)](https://www.youtube.com/watch?v=hrXuNYLDFds)

## Table of Contents

- [Current Version: Origami](#current-version-origami)
  - [Table of Contents](#table-of-contents)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Clone the repository](#clone-the-repository)
- [Running](#running)
  - [Gaze input to joystick output](#gaze-input-to-joystick-output)
  - [Emulated/Developer mode](#emulateddeveloper-mode)
- [Cite this repository](#cite-this-repository)

---

# Prerequisites

- Pupil Neon Glasses OR a webcam, ideally an external one.
- Docker, for running ROS2 Humble. [Install Docker here](https://docs.docker.com/get-docker/)
- Print the sample control interface on paper (see [here](/src/diegetic_button_pkg/printables/)).

# Installation

## Clone the repository

Navigate to a new workspace, then clone the repository with submodules:

```bash
git clone --recurse-submodules https://github.com/enunezs/origami
```

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
