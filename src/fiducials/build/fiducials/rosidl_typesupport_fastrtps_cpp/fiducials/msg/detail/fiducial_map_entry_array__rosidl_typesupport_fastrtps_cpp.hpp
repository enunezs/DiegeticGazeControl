// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__rosidl_typesupport_fastrtps_cpp.hpp.em
// with input from fiducials:msg/FiducialMapEntryArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_

#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "fiducials/msg/rosidl_typesupport_fastrtps_cpp__visibility_control.h"
#include "fiducials/msg/detail/fiducial_map_entry_array__struct.hpp"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

#include "fastcdr/Cdr.h"

namespace fiducials
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_fiducials
cdr_serialize(
  const fiducials::msg::FiducialMapEntryArray & ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_fiducials
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  fiducials::msg::FiducialMapEntryArray & ros_message);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_fiducials
get_serialized_size(
  const fiducials::msg::FiducialMapEntryArray & ros_message,
  size_t current_alignment);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_fiducials
max_serialized_size_FiducialMapEntryArray(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace fiducials

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_fiducials
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, fiducials, msg, FiducialMapEntryArray)();

#ifdef __cplusplus
}
#endif

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
