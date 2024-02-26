// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from diegetic_button_pkg:msg/InputStatus.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__STRUCT_H_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'input_id'
// Member 'status'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/InputStatus in the package diegetic_button_pkg.
typedef struct diegetic_button_pkg__msg__InputStatus
{
  /// Details of input
  rosidl_runtime_c__String input_id;
  rosidl_runtime_c__String status;
  double percent;
} diegetic_button_pkg__msg__InputStatus;

// Struct for a sequence of diegetic_button_pkg__msg__InputStatus.
typedef struct diegetic_button_pkg__msg__InputStatus__Sequence
{
  diegetic_button_pkg__msg__InputStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} diegetic_button_pkg__msg__InputStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__STRUCT_H_
