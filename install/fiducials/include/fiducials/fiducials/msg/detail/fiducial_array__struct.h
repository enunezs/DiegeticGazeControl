// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from fiducials:msg/FiducialArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_ARRAY__STRUCT_H_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_ARRAY__STRUCT_H_

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
// Member 'fiducials'
#include "fiducials/msg/detail/fiducial__struct.h"

/// Struct defined in msg/FiducialArray in the package fiducials.
/**
  * A set of fiducial vertex messages
  * to an image
 */
typedef struct fiducials__msg__FiducialArray
{
  std_msgs__msg__Header header;
  int32_t image_seq;
  fiducials__msg__Fiducial__Sequence fiducials;
} fiducials__msg__FiducialArray;

// Struct for a sequence of fiducials__msg__FiducialArray.
typedef struct fiducials__msg__FiducialArray__Sequence
{
  fiducials__msg__FiducialArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fiducials__msg__FiducialArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_ARRAY__STRUCT_H_
