// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from fiducials:msg/FiducialTransform.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__STRUCT_H_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'transform'
#include "geometry_msgs/msg/detail/transform__struct.h"

/// Struct defined in msg/FiducialTransform in the package fiducials.
/**
  * A camera to fiducial transform with supporting data
 */
typedef struct fiducials__msg__FiducialTransform
{
  int32_t fiducial_id;
  geometry_msgs__msg__Transform transform;
  double image_error;
  double object_error;
  double fiducial_area;
} fiducials__msg__FiducialTransform;

// Struct for a sequence of fiducials__msg__FiducialTransform.
typedef struct fiducials__msg__FiducialTransform__Sequence
{
  fiducials__msg__FiducialTransform * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fiducials__msg__FiducialTransform__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__STRUCT_H_
