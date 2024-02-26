// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from diegetic_button_pkg:msg/DiegeticButtonArray.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__STRUCT_H_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__STRUCT_H_

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
// Member 'buttons'
#include "diegetic_button_pkg/msg/detail/diegetic_button__struct.h"

/// Struct defined in msg/DiegeticButtonArray in the package diegetic_button_pkg.
typedef struct diegetic_button_pkg__msg__DiegeticButtonArray
{
  std_msgs__msg__Header header;
  diegetic_button_pkg__msg__DiegeticButton__Sequence buttons;
} diegetic_button_pkg__msg__DiegeticButtonArray;

// Struct for a sequence of diegetic_button_pkg__msg__DiegeticButtonArray.
typedef struct diegetic_button_pkg__msg__DiegeticButtonArray__Sequence
{
  diegetic_button_pkg__msg__DiegeticButtonArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} diegetic_button_pkg__msg__DiegeticButtonArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__STRUCT_H_
