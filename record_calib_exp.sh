#!/bin/bash

# Check input
if [ -z "$1" ]; then
  echo "Usage: $0 <participant_id>"
  exit 1
fi

participant="$1"

test_name="bag_files/NEW_CALIB/p_${participant}_calib_experiment_$(date +%Y%m%d_%H%M%S)"

ros2 bag record -o $test_name \
    /pupil_glasses/event/blink \
    /pupil_glasses/event/fixation \
    /pupil_glasses/event/fixation_onset \
    /pupil_glasses/event/saccade \
    /pupil_glasses/event/saccade_onset \
    /pupil_glasses/front_camera/camera_info \
    /pupil_glasses/front_image \
    /pupil_glasses/gaze_data \
    /pupil_glasses/gaze_position \
    /pupil_glasses/imu \
    /fiducial_transforms \
    /joy 