// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from diegetic_button_pkg:msg/DiegeticButton.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "diegetic_button_pkg/msg/detail/diegetic_button__rosidl_typesupport_introspection_c.h"
#include "diegetic_button_pkg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "diegetic_button_pkg/msg/detail/diegetic_button__functions.h"
#include "diegetic_button_pkg/msg/detail/diegetic_button__struct.h"


// Include directives for member types
// Member `button_id`
#include "rosidl_runtime_c/string_functions.h"
// Member `button_transform`
#include "geometry_msgs/msg/transform.h"
// Member `button_transform`
#include "geometry_msgs/msg/detail/transform__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  diegetic_button_pkg__msg__DiegeticButton__init(message_memory);
}

void diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_fini_function(void * message_memory)
{
  diegetic_button_pkg__msg__DiegeticButton__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_message_member_array[6] = {
  {
    "button_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__DiegeticButton, button_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "button_transform",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__DiegeticButton, button_transform),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "x0",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__DiegeticButton, x0),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "y0",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__DiegeticButton, y0),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "x1",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__DiegeticButton, x1),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "y1",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__DiegeticButton, y1),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_message_members = {
  "diegetic_button_pkg__msg",  // message namespace
  "DiegeticButton",  // message name
  6,  // number of fields
  sizeof(diegetic_button_pkg__msg__DiegeticButton),
  diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_message_member_array,  // message members
  diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_init_function,  // function to initialize message memory (memory has to be allocated)
  diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_message_type_support_handle = {
  0,
  &diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_diegetic_button_pkg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, diegetic_button_pkg, msg, DiegeticButton)() {
  diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, geometry_msgs, msg, Transform)();
  if (!diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_message_type_support_handle.typesupport_identifier) {
    diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &diegetic_button_pkg__msg__DiegeticButton__rosidl_typesupport_introspection_c__DiegeticButton_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
