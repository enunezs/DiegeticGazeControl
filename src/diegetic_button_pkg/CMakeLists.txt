cmake_minimum_required(VERSION 3.5)
project(diegetic_button_pkg)

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
find_package(rosidl_default_generators REQUIRED)

# Path to resources
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

# Path to scripts
ament_python_install_package("scripts")

# Gen messages
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/DiegeticButton.msg"
  "msg/DiegeticButtonArray.msg"
  "msg/InputStatus.msg"
  "msg/InputStatusArray.msg"
  DEPENDENCIES builtin_interfaces
  DEPENDENCIES geometry_msgs
)

# Install python scripts
install(PROGRAMS
  scripts/diegetic_button.py
  scripts/input_check.py
  scripts/bagToCSV.py
  scripts/devices/joy.py
  scripts/devices/piano_demo.py
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
