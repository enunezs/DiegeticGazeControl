// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from fiducials:msg/FiducialMapEntryArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__STRUCT_H_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'fiducials'
#include "fiducials/msg/detail/fiducial_map_entry__struct.h"

/// Struct defined in msg/FiducialMapEntryArray in the package fiducials.
typedef struct fiducials__msg__FiducialMapEntryArray
{
  fiducials__msg__FiducialMapEntry__Sequence fiducials;
} fiducials__msg__FiducialMapEntryArray;

// Struct for a sequence of fiducials__msg__FiducialMapEntryArray.
typedef struct fiducials__msg__FiducialMapEntryArray__Sequence
{
  fiducials__msg__FiducialMapEntryArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fiducials__msg__FiducialMapEntryArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__STRUCT_H_
