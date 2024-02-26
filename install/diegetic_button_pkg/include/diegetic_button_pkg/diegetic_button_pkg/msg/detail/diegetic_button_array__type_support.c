// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from diegetic_button_pkg:msg/DiegeticButtonArray.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "diegetic_button_pkg/msg/detail/diegetic_button_array__rosidl_typesupport_introspection_c.h"
#include "diegetic_button_pkg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "diegetic_button_pkg/msg/detail/diegetic_button_array__functions.h"
#include "diegetic_button_pkg/msg/detail/diegetic_button_array__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `buttons`
#include "diegetic_button_pkg/msg/diegetic_button.h"
// Member `buttons`
#include "diegetic_button_pkg/msg/detail/diegetic_button__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  diegetic_button_pkg__msg__DiegeticButtonArray__init(message_memory);
}

void diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_fini_function(void * message_memory)
{
  diegetic_button_pkg__msg__DiegeticButtonArray__fini(message_memory);
}

size_t diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__size_function__DiegeticButtonArray__buttons(
  const void * untyped_member)
{
  const diegetic_button_pkg__msg__DiegeticButton__Sequence * member =
    (const diegetic_button_pkg__msg__DiegeticButton__Sequence *)(untyped_member);
  return member->size;
}

const void * diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__get_const_function__DiegeticButtonArray__buttons(
  const void * untyped_member, size_t index)
{
  const diegetic_button_pkg__msg__DiegeticButton__Sequence * member =
    (const diegetic_button_pkg__msg__DiegeticButton__Sequence *)(untyped_member);
  return &member->data[index];
}

void * diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__get_function__DiegeticButtonArray__buttons(
  void * untyped_member, size_t index)
{
  diegetic_button_pkg__msg__DiegeticButton__Sequence * member =
    (diegetic_button_pkg__msg__DiegeticButton__Sequence *)(untyped_member);
  return &member->data[index];
}

void diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__fetch_function__DiegeticButtonArray__buttons(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const diegetic_button_pkg__msg__DiegeticButton * item =
    ((const diegetic_button_pkg__msg__DiegeticButton *)
    diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__get_const_function__DiegeticButtonArray__buttons(untyped_member, index));
  diegetic_button_pkg__msg__DiegeticButton * value =
    (diegetic_button_pkg__msg__DiegeticButton *)(untyped_value);
  *value = *item;
}

void diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__assign_function__DiegeticButtonArray__buttons(
  void * untyped_member, size_t index, const void * untyped_value)
{
  diegetic_button_pkg__msg__DiegeticButton * item =
    ((diegetic_button_pkg__msg__DiegeticButton *)
    diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__get_function__DiegeticButtonArray__buttons(untyped_member, index));
  const diegetic_button_pkg__msg__DiegeticButton * value =
    (const diegetic_button_pkg__msg__DiegeticButton *)(untyped_value);
  *item = *value;
}

bool diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__resize_function__DiegeticButtonArray__buttons(
  void * untyped_member, size_t size)
{
  diegetic_button_pkg__msg__DiegeticButton__Sequence * member =
    (diegetic_button_pkg__msg__DiegeticButton__Sequence *)(untyped_member);
  diegetic_button_pkg__msg__DiegeticButton__Sequence__fini(member);
  return diegetic_button_pkg__msg__DiegeticButton__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_member_array[2] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__DiegeticButtonArray, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "buttons",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg__msg__DiegeticButtonArray, buttons),  // bytes offset in struct
    NULL,  // default value
    diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__size_function__DiegeticButtonArray__buttons,  // size() function pointer
    diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__get_const_function__DiegeticButtonArray__buttons,  // get_const(index) function pointer
    diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__get_function__DiegeticButtonArray__buttons,  // get(index) function pointer
    diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__fetch_function__DiegeticButtonArray__buttons,  // fetch(index, &value) function pointer
    diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__assign_function__DiegeticButtonArray__buttons,  // assign(index, value) function pointer
    diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__resize_function__DiegeticButtonArray__buttons  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_members = {
  "diegetic_button_pkg__msg",  // message namespace
  "DiegeticButtonArray",  // message name
  2,  // number of fields
  sizeof(diegetic_button_pkg__msg__DiegeticButtonArray),
  diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_member_array,  // message members
  diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_init_function,  // function to initialize message memory (memory has to be allocated)
  diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_type_support_handle = {
  0,
  &diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_diegetic_button_pkg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, diegetic_button_pkg, msg, DiegeticButtonArray)() {
  diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, diegetic_button_pkg, msg, DiegeticButton)();
  if (!diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_type_support_handle.typesupport_identifier) {
    diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &diegetic_button_pkg__msg__DiegeticButtonArray__rosidl_typesupport_introspection_c__DiegeticButtonArray_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
