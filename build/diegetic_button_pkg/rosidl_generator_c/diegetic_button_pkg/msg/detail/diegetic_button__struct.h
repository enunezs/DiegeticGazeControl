// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from diegetic_button_pkg:msg/DiegeticButton.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__STRUCT_H_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'button_id'
#include "rosidl_runtime_c/string.h"
// Member 'button_transform'
#include "geometry_msgs/msg/detail/transform__struct.h"

/// Struct defined in msg/DiegeticButton in the package diegetic_button_pkg.
typedef struct diegetic_button_pkg__msg__DiegeticButton
{
  /// Details of a button
  rosidl_runtime_c__String button_id;
  geometry_msgs__msg__Transform button_transform;
  /// bounding box vertices in local coordinates
  double x0;
  double y0;
  double x1;
  double y1;
} diegetic_button_pkg__msg__DiegeticButton;

// Struct for a sequence of diegetic_button_pkg__msg__DiegeticButton.
typedef struct diegetic_button_pkg__msg__DiegeticButton__Sequence
{
  diegetic_button_pkg__msg__DiegeticButton * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} diegetic_button_pkg__msg__DiegeticButton__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__STRUCT_H_
