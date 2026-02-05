cmake_minimum_required(VERSION 3.5)
project(gaze_interaction_manager)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)

# find_package(cv2 REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
execute_process(COMMAND "${Python3_EXECUTABLE}" -c
  "import numpy; print(numpy.get_include())"
  OUTPUT_VARIABLE NumPy_INCLUDE_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
include_directories(${NumPy_INCLUDE_DIR})

find_package(rosidl_default_generators REQUIRED)


# Path to resources
install(
  DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}/
)

find_package(diegetic_transform_engine REQUIRED)
find_package(pupil_neon_ros REQUIRED)

# Path to scripts
ament_python_install_package("scripts")

# Gen messages
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ButtonStatus.msg"
  "msg/ButtonStatusArray.msg"
  "msg/CalibrationModel.msg"
  "msg/InteractionSegment.msg"
  DEPENDENCIES builtin_interfaces
  DEPENDENCIES geometry_msgs
  DEPENDENCIES diegetic_transform_engine
  DEPENDENCIES pupil_neon_ros
)

# Install python scripts
install(PROGRAMS
  scripts/dwell_time.py
  scripts/gaze_controller.py
  scripts/gaze_controller.py
  scripts/calibration_learner.py
  scripts/robot_command_mapper.py
  scripts/joy_command_mapper.py
  DESTINATION lib/${PROJECT_NAME}
)


# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)

# find_package(rosidl_default_generators REQUIRED)
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)

  # the following line skips the linter which checks for copyrights
  # uncomment the line when a copyright and license is not present in all source files
  # set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # uncomment the line when this package is not in a git repo
  # set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
