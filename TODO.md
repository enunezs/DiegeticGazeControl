# RE+DO

New structure:

- [x] Plan

```mermaid
flowchart TB

    %% =======================
    %% CLASS DEFINITIONS
    %% =======================
    classDef pending fill:#fff3cd,stroke:#f0ad4e,stroke-width:2px,color:#333
    classDef important fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#333
    classDef done fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#333

    %% =======================
    %% GAZE TRACKER
    %% =======================
    subgraph Gaze_Tracker[👁️ Gaze Tracking +]
        Pupil[Async Pupil Node]
    end

    %% =======================
    %% DIEGETIC TRANSFORM ENGINE
    %% =======================
    subgraph DTE[🎨 Diegetic Transform Engine]
    direction TB
        ArucoPoses[Aruco Detector]
        ButtonPoses[Button Finder]
        TransformVisuals[/Transform Visuals/]
    end

    %% =======================
    %% GAZE-INTERACTION MANAGER
    %% =======================
    subgraph GFC[🎯 Gaze Interaction Manager]
    direction RL
        GazeController[Gaze Controller]
        Dwell[Dwell Detector]
        Calibrator[Gaze Calibrator]
    end

    %% =======================
    %% ROBOT CONTROL
    %% =======================
    subgraph RC[🤖 Robot Controller]
        Robot[Robot Controller]
        Jaco[Jaco Controller]
    end

    %% =======================
    %% FEEDBACK
    %% =======================
    subgraph FB[🔊 Feedback]
        Rviz[Rviz Visuals]
        RQT[RQT Visuals]
        Sound[Sound Manager]
    end

    %% =======================
    %% CONNECTIONS
    %% =======================
    %% Pupil to Aruco & Button Detection
    Pupil -->|/pupil_glasses/front_image| ArucoPoses
    Pupil -->|/pupil_glasses/front_camera/camera_info| ArucoPoses
    Pupil -->|/pupil_glasses/front_camera/camera_info| GazeController
    Pupil -->|/pupil_glasses/event/fixation| GazeController

    %% Aruco to Button + Visuals
    ArucoPoses -->|Aruco Transforms 3D| ButtonPoses
    ArucoPoses -->|Aruco Transforms 3D| TransformVisuals

    %% Button to Dwell + Visuals
    ButtonPoses -->|Button Transforms 2D| Dwell
    ButtonPoses -->|Button Transforms 2D| TransformVisuals

    %% Gaze Controller
    GazeController -->|/corrected_gaze| Dwell
    GazeController -->|Gaze error, x, y, t| Calibrator
    Calibrator -->|Correction Prediction| GazeController
    GazeController -->|Input Decision| Robot

    %% Dwell
    Dwell -->|Active Buttons| GazeController
    Dwell -->|Looked at Button| GazeController

    %% Robot Controller
    Robot -->|Joy Message| Jaco

    %% =======================
    %% LINKS
    %% =======================
    click Pupil href "https://github.com/enunezs/pupil_neon_pkg"
    click ArucoPoses href "/src/fiducials/"
    click ButtonPoses href "/src/diegetic_button_pkg/"
    click Dwell href "/src/diegetic_button_pkg/"
    click Jaco href "https://github.com/enunezs/ros2_jaco_controller"

    %% =======================
    %% STATUS TAGS
    %% Example: assign nodes to statuses
    %% =======================
    class Pupil done
    class ArucoPoses done
    class ButtonPoses done
    class Dwell important
    class GazeController important
    class Calibrator important
    class Robot done
    class Jaco done

```

- [ ] Migrate to Kaiju

## pupil_glasses_node

- [x] Sends decoupled gaze and image at different frequencies
- [x] Sends also sensor information
- [x] Send camera calibration info
- [x] Sends new messages on smooth pursuit and expanded gaze properties

## aruco_detector_node

- [x] Detect ArUco markers in scene image. Classify as fixed, robot-mounted, transient as per config file. Check if there is a package?
- [x] TF frames (aruco*marker*\*), /marker_detections (MarkerDetectionArray.msg)
- [x] MarkerArray

## button_manager_node

- [x] At start, defines fixed button transforms at the beggining from csv / config file. TF (button*candidate*\*), /button_candidates (ButtonArray.msg)
- [x] Aggregates multiple TFs to find fused pose TF (button*fused*\*), /fused_buttons (ButtonArray.msg)
- [ ] 3D Visualization node, color depending on dwell time

## dwell_interaction_node

- [x] Map gaze to button hit tests, apply dwell-time filter, publish events.
- [x] New Launch file with all components

## recalibration_manager_node

- [ ] Subscribe to dwell events and smooth pursuit.
- [ ] **IMPORTANT:** Plot activation and blocks for start / end events in RQT
  - [ ] Visualizer to plot data to rqt? Do from controller instead
- [ ] Analyze gaze drift from events, publish recalibration offsets (call service)

## sound_feedback_node

- [] Subscribe to multiple events, play sounds for feedback.

robot_controller_node

- Keep the joy node

## Project:

diegetic_V3

pupil_neon_pkg -> pupil_neon_glasses
pupil_publisher.py
emulator_publisher.py
aruco_detector
aruco_detector.py (potentially integrate above?)

diegetic_button
button_locator.py
dwell_time_manager.py
smooth_pursuit_recalibration.py

sound_manager
sound_feedback.py

## TF tree

world
├── fixed markers (environment anchors)
│ ├── aruco*marker_1
│ │ ├── button_candidate_1a
│ │ └── button_candidate_1b
│ └── aruco_marker_2
│ └── button_candidate_2a
├── robot_base_link
│ ├── robot_arm_link_1
│ └── aruco_marker_robot_7
│ ├── button_candidate_r7a
│ └── button_candidate_r7b
└── button_fused*\* (dynamic, aggregated positions)
└── odom
└── pupil_glasses_neon
├── pupil_glasses_neon_front_camera
├── imu_link (?)
├── gaze_point
└── aruco_transient_88
└── button_candidate_r7b

Use other fiducial systems

apriltag_ros
ros2_aruco (proper)
stag_ros

### Recording

```bash
ros2 bag record -o subset /button_transforms /diegetic/inputs /fiducial_transforms /j2n6s300_driver/out/cartesian_command /j2n6s300_driver/out/finger_position /j2n6s300_driver/out/joint_angles /j2n6s300_driver/out/joint_state /j2n6s300_driver/out/joint_torques /j2n6s300_driver/out/tool_pose /j2n6s300_driver/out/tool_wrench /joy /pupil_glasses/gaze_position
```
