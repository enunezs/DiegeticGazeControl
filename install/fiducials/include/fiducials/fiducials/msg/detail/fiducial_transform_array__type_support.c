// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from fiducials:msg/FiducialTransformArray.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "fiducials/msg/detail/fiducial_transform_array__rosidl_typesupport_introspection_c.h"
#include "fiducials/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "fiducials/msg/detail/fiducial_transform_array__functions.h"
#include "fiducials/msg/detail/fiducial_transform_array__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `transforms`
#include "fiducials/msg/fiducial_transform.h"
// Member `transforms`
#include "fiducials/msg/detail/fiducial_transform__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  fiducials__msg__FiducialTransformArray__init(message_memory);
}

void fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_fini_function(void * message_memory)
{
  fiducials__msg__FiducialTransformArray__fini(message_memory);
}

size_t fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__size_function__FiducialTransformArray__transforms(
  const void * untyped_member)
{
  const fiducials__msg__FiducialTransform__Sequence * member =
    (const fiducials__msg__FiducialTransform__Sequence *)(untyped_member);
  return member->size;
}

const void * fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__get_const_function__FiducialTransformArray__transforms(
  const void * untyped_member, size_t index)
{
  const fiducials__msg__FiducialTransform__Sequence * member =
    (const fiducials__msg__FiducialTransform__Sequence *)(untyped_member);
  return &member->data[index];
}

void * fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__get_function__FiducialTransformArray__transforms(
  void * untyped_member, size_t index)
{
  fiducials__msg__FiducialTransform__Sequence * member =
    (fiducials__msg__FiducialTransform__Sequence *)(untyped_member);
  return &member->data[index];
}

void fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__fetch_function__FiducialTransformArray__transforms(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const fiducials__msg__FiducialTransform * item =
    ((const fiducials__msg__FiducialTransform *)
    fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__get_const_function__FiducialTransformArray__transforms(untyped_member, index));
  fiducials__msg__FiducialTransform * value =
    (fiducials__msg__FiducialTransform *)(untyped_value);
  *value = *item;
}

void fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__assign_function__FiducialTransformArray__transforms(
  void * untyped_member, size_t index, const void * untyped_value)
{
  fiducials__msg__FiducialTransform * item =
    ((fiducials__msg__FiducialTransform *)
    fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__get_function__FiducialTransformArray__transforms(untyped_member, index));
  const fiducials__msg__FiducialTransform * value =
    (const fiducials__msg__FiducialTransform *)(untyped_value);
  *item = *value;
}

bool fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__resize_function__FiducialTransformArray__transforms(
  void * untyped_member, size_t size)
{
  fiducials__msg__FiducialTransform__Sequence * member =
    (fiducials__msg__FiducialTransform__Sequence *)(untyped_member);
  fiducials__msg__FiducialTransform__Sequence__fini(member);
  return fiducials__msg__FiducialTransform__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_member_array[3] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialTransformArray, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "image_seq",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialTransformArray, image_seq),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "transforms",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials__msg__FiducialTransformArray, transforms),  // bytes offset in struct
    NULL,  // default value
    fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__size_function__FiducialTransformArray__transforms,  // size() function pointer
    fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__get_const_function__FiducialTransformArray__transforms,  // get_const(index) function pointer
    fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__get_function__FiducialTransformArray__transforms,  // get(index) function pointer
    fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__fetch_function__FiducialTransformArray__transforms,  // fetch(index, &value) function pointer
    fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__assign_function__FiducialTransformArray__transforms,  // assign(index, value) function pointer
    fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__resize_function__FiducialTransformArray__transforms  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_members = {
  "fiducials__msg",  // message namespace
  "FiducialTransformArray",  // message name
  3,  // number of fields
  sizeof(fiducials__msg__FiducialTransformArray),
  fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_member_array,  // message members
  fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_init_function,  // function to initialize message memory (memory has to be allocated)
  fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_type_support_handle = {
  0,
  &fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_fiducials
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fiducials, msg, FiducialTransformArray)() {
  fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_member_array[2].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fiducials, msg, FiducialTransform)();
  if (!fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_type_support_handle.typesupport_identifier) {
    fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &fiducials__msg__FiducialTransformArray__rosidl_typesupport_introspection_c__FiducialTransformArray_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
