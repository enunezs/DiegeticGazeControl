// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from fiducials:msg/FiducialMapEntry.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY__STRUCT_H_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in msg/FiducialMapEntry in the package fiducials.
/**
  * pose of a fiducial
 */
typedef struct fiducials__msg__FiducialMapEntry
{
  int32_t fiducial_id;
  /// translation
  double x;
  double y;
  double z;
  /// rotation
  double rx;
  double ry;
  double rz;
} fiducials__msg__FiducialMapEntry;

// Struct for a sequence of fiducials__msg__FiducialMapEntry.
typedef struct fiducials__msg__FiducialMapEntry__Sequence
{
  fiducials__msg__FiducialMapEntry * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fiducials__msg__FiducialMapEntry__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY__STRUCT_H_
