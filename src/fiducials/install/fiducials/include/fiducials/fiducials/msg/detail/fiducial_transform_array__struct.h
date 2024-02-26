// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from fiducials:msg/FiducialTransformArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM_ARRAY__STRUCT_H_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM_ARRAY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'transforms'
#include "fiducials/msg/detail/fiducial_transform__struct.h"

/// Struct defined in msg/FiducialTransformArray in the package fiducials.
/**
  * A set of camera to fiducial transform with supporting data corresponding
  * to an image
 */
typedef struct fiducials__msg__FiducialTransformArray
{
  std_msgs__msg__Header header;
  int32_t image_seq;
  fiducials__msg__FiducialTransform__Sequence transforms;
} fiducials__msg__FiducialTransformArray;

// Struct for a sequence of fiducials__msg__FiducialTransformArray.
typedef struct fiducials__msg__FiducialTransformArray__Sequence
{
  fiducials__msg__FiducialTransformArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fiducials__msg__FiducialTransformArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM_ARRAY__STRUCT_H_
