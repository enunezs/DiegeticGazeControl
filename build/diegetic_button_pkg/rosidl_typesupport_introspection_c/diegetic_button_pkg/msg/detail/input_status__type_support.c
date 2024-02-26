// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from diegetic_button_pkg:msg/InputStatus.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "diegetic_button_pkg/msg/detail/input_status__rosidl_typesupport_introspection_c.h"
#include "diegetic_button_pkg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "diegetic_button_pkg/msg/detail/input_status__functions.h"
#include "diegetic_button_pkg/msg/detail/input_status__struct.h"


// Include directives for member types
// Member `input_id`
// Member `status`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  diegetic_button_pkg__msg__InputStatus__init(message_memory);
}

void diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_fini_function(void * message_memory)
{
  diegetic_button_pkg__msg__InputStatus__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_message_member_array[3] = {
  {
    "input_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__InputStatus, input_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "status",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__InputStatus, status),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "percent",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__InputStatus, percent),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_message_members = {
  "diegetic_button_pkg__msg",  // message namespace
  "InputStatus",  // message name
  3,  // number of fields
  sizeof(diegetic_button_pkg__msg__InputStatus),
  diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_message_member_array,  // message members
  diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_init_function,  // function to initialize message memory (memory has to be allocated)
  diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_message_type_support_handle = {
  0,
  &diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_diegetic_button_pkg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, diegetic_button_pkg, msg, InputStatus)() {
  if (!diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_message_type_support_handle.typesupport_identifier) {
    diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &diegetic_button_pkg__msg__InputStatus__rosidl_typesupport_introspection_c__InputStatus_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
