// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from diegetic_button_pkg:msg/InputStatusArray.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "diegetic_button_pkg/msg/detail/input_status_array__rosidl_typesupport_introspection_c.h"
#include "diegetic_button_pkg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "diegetic_button_pkg/msg/detail/input_status_array__functions.h"
#include "diegetic_button_pkg/msg/detail/input_status_array__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `inputs`
#include "diegetic_button_pkg/msg/input_status.h"
// Member `inputs`
#include "diegetic_button_pkg/msg/detail/input_status__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  diegetic_button_pkg__msg__InputStatusArray__init(message_memory);
}

void diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_fini_function(void * message_memory)
{
  diegetic_button_pkg__msg__InputStatusArray__fini(message_memory);
}

size_t diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__size_function__InputStatusArray__inputs(
  const void * untyped_member)
{
  const diegetic_button_pkg__msg__InputStatus__Sequence * member =
    (const diegetic_button_pkg__msg__InputStatus__Sequence *)(untyped_member);
  return member->size;
}

const void * diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__get_const_function__InputStatusArray__inputs(
  const void * untyped_member, size_t index)
{
  const diegetic_button_pkg__msg__InputStatus__Sequence * member =
    (const diegetic_button_pkg__msg__InputStatus__Sequence *)(untyped_member);
  return &member->data[index];
}

void * diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__get_function__InputStatusArray__inputs(
  void * untyped_member, size_t index)
{
  diegetic_button_pkg__msg__InputStatus__Sequence * member =
    (diegetic_button_pkg__msg__InputStatus__Sequence *)(untyped_member);
  return &member->data[index];
}

void diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__fetch_function__InputStatusArray__inputs(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const diegetic_button_pkg__msg__InputStatus * item =
    ((const diegetic_button_pkg__msg__InputStatus *)
    diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__get_const_function__InputStatusArray__inputs(untyped_member, index));
  diegetic_button_pkg__msg__InputStatus * value =
    (diegetic_button_pkg__msg__InputStatus *)(untyped_value);
  *value = *item;
}

void diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__assign_function__InputStatusArray__inputs(
  void * untyped_member, size_t index, const void * untyped_value)
{
  diegetic_button_pkg__msg__InputStatus * item =
    ((diegetic_button_pkg__msg__InputStatus *)
    diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__get_function__InputStatusArray__inputs(untyped_member, index));
  const diegetic_button_pkg__msg__InputStatus * value =
    (const diegetic_button_pkg__msg__InputStatus *)(untyped_value);
  *item = *value;
}

bool diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__resize_function__InputStatusArray__inputs(
  void * untyped_member, size_t size)
{
  diegetic_button_pkg__msg__InputStatus__Sequence * member =
    (diegetic_button_pkg__msg__InputStatus__Sequence *)(untyped_member);
  diegetic_button_pkg__msg__InputStatus__Sequence__fini(member);
  return diegetic_button_pkg__msg__InputStatus__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_member_array[2] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__InputStatusArray, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "inputs",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__InputStatusArray, inputs),  // bytes offset in struct
    NULL,  // default value
    diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__size_function__InputStatusArray__inputs,  // size() function pointer
    diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__get_const_function__InputStatusArray__inputs,  // get_const(index) function pointer
    diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__get_function__InputStatusArray__inputs,  // get(index) function pointer
    diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__fetch_function__InputStatusArray__inputs,  // fetch(index, &value) function pointer
    diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__assign_function__InputStatusArray__inputs,  // assign(index, value) function pointer
    diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__resize_function__InputStatusArray__inputs  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_members = {
  "diegetic_button_pkg__msg",  // message namespace
  "InputStatusArray",  // message name
  2,  // number of fields
  sizeof(diegetic_button_pkg__msg__InputStatusArray),
  diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_member_array,  // message members
  diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_init_function,  // function to initialize message memory (memory has to be allocated)
  diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_type_support_handle = {
  0,
  &diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_diegetic_button_pkg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, diegetic_button_pkg, msg, InputStatusArray)() {
  diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, diegetic_button_pkg, msg, InputStatus)();
  if (!diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_type_support_handle.typesupport_identifier) {
    diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &diegetic_button_pkg__msg__InputStatusArray__rosidl_typesupport_introspection_c__InputStatusArray_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
