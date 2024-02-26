# Current Version: Origami

This project, as detailed in the paper [_"Pupil System: A Wearable Eye Tracking System for People with Severe Motor Impairments"_](https://arxiv.org/abs/2105.05782), aims to enable interaction with prepared environments via eye-gaze using ArUco markers. Using the **_Pupil Neon Glasses_**, the user's gaze is detected and used to interact with printed interfaces or everyday items. The **_final output will be joy signals_** in ROS2.

[![DGUI V2-1](http://img.youtube.com/vi/hrXuNYLDFds/0.jpg)](https://www.youtube.com/watch?v=hrXuNYLDFds)

## Table of Contents

- [Prerequisites](#prerequisites)
- [Running](#running)

# Prerequisites

- Pupil Neon Glasses OR a webcam, ideally an external one.
- Docker, for running ROS2 Humble. [Install Docker here](https://docs.docker.com/get-docker/)
- Print the sample control interface on paper (see [here](/src/diegetic_button_pkg/printables/)).

# Running

## Gaze input to joystick output

From the root of the repository, run the following command to **build and run** the docker image:

```bash
./docker/1_docker_script.sh
```

Then, run the following command to start the container:

```bash
ros2 launch diegetic_button_pkg devel.launch.py
```

## Emulated/Developer mode

```bash
ros2 launch diegetic_button_pkg devel.launch.py
```

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
