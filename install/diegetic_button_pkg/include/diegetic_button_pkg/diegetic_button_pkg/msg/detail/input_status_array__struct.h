// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from diegetic_button_pkg:msg/InputStatusArray.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__STRUCT_H_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__STRUCT_H_

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
// Member 'inputs'
#include "diegetic_button_pkg/msg/detail/input_status__struct.h"

/// Struct defined in msg/InputStatusArray in the package diegetic_button_pkg.
typedef struct diegetic_button_pkg__msg__InputStatusArray
{
  std_msgs__msg__Header header;
  diegetic_button_pkg__msg__InputStatus__Sequence inputs;
} diegetic_button_pkg__msg__InputStatusArray;

// Struct for a sequence of diegetic_button_pkg__msg__InputStatusArray.
typedef struct diegetic_button_pkg__msg__InputStatusArray__Sequence
{
  diegetic_button_pkg__msg__InputStatusArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} diegetic_button_pkg__msg__InputStatusArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__STRUCT_H_
