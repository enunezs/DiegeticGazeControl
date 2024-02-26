// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from fiducials:msg/Fiducial.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL__STRUCT_H_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in msg/Fiducial in the package fiducials.
/**
  * Details of a detected fiducial.
 */
typedef struct fiducials__msg__Fiducial
{
  int32_t fiducial_id;
  int32_t direction;
  /// vertices
  double x0;
  double y0;
  double x1;
  double y1;
  double x2;
  double y2;
  double x3;
  double y3;
} fiducials__msg__Fiducial;

// Struct for a sequence of fiducials__msg__Fiducial.
typedef struct fiducials__msg__Fiducial__Sequence
{
  fiducials__msg__Fiducial * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fiducials__msg__Fiducial__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL__STRUCT_H_
