# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_pupil_neon_pkg_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED pupil_neon_pkg_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(pupil_neon_pkg_FOUND FALSE)
  elseif(NOT pupil_neon_pkg_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(pupil_neon_pkg_FOUND FALSE)
  endif()
  return()
endif()
set(_pupil_neon_pkg_CONFIG_INCLUDED TRUE)

# output package information
if(NOT pupil_neon_pkg_FIND_QUIETLY)
  message(STATUS "Found pupil_neon_pkg: 1.0.0 (${pupil_neon_pkg_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'pupil_neon_pkg' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${pupil_neon_pkg_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(pupil_neon_pkg_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${pupil_neon_pkg_DIR}/${_extra}")
endforeach()
