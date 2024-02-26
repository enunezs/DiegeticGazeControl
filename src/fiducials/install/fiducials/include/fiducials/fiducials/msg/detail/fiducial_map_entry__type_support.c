// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from fiducials:msg/FiducialMapEntry.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "fiducials/msg/detail/fiducial_map_entry__rosidl_typesupport_introspection_c.h"
#include "fiducials/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "fiducials/msg/detail/fiducial_map_entry__functions.h"
#include "fiducials/msg/detail/fiducial_map_entry__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  fiducials__msg__FiducialMapEntry__init(message_memory);
}

void fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_fini_function(void * message_memory)
{
  fiducials__msg__FiducialMapEntry__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_message_member_array[7] = {
  {
    "fiducial_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialMapEntry, fiducial_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "x",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialMapEntry, x),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "y",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialMapEntry, y),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "z",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialMapEntry, z),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "rx",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialMapEntry, rx),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "ry",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialMapEntry, ry),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "rz",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialMapEntry, rz),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_message_members = {
  "fiducials__msg",  // message namespace
  "FiducialMapEntry",  // message name
  7,  // number of fields
  sizeof(fiducials__msg__FiducialMapEntry),
  fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_message_member_array,  // message members
  fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_init_function,  // function to initialize message memory (memory has to be allocated)
  fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_message_type_support_handle = {
  0,
  &fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_fiducials
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fiducials, msg, FiducialMapEntry)() {
  if (!fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_message_type_support_handle.typesupport_identifier) {
    fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &fiducials__msg__FiducialMapEntry__rosidl_typesupport_introspection_c__FiducialMapEntry_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
