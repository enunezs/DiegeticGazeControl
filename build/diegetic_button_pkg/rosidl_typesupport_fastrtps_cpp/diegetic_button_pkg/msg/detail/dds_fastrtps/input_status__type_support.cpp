// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from diegetic_button_pkg:msg/InputStatus.idl
// generated code does not contain a copyright notice
#include "diegetic_button_pkg/msg/detail/input_status__rosidl_typesupport_fastrtps_cpp.hpp"
#include "diegetic_button_pkg/msg/detail/input_status__struct.hpp"

#include <limits>
#include <stdexcept>
#include <string>
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_fastrtps_cpp/identifier.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_fastrtps_cpp/wstring_conversion.hpp"
#include "fastcdr/Cdr.h"


// forward declaration of message dependencies and their conversion functions

namespace diegetic_button_pkg
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_diegetic_button_pkg
cdr_serialize(
  const diegetic_button_pkg::msg::InputStatus & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: input_id
  cdr << ros_message.input_id;
  // Member: status
  cdr << ros_message.status;
  // Member: percent
  cdr << ros_message.percent;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_diegetic_button_pkg
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  diegetic_button_pkg::msg::InputStatus & ros_message)
{
  // Member: input_id
  cdr >> ros_message.input_id;

  // Member: status
  cdr >> ros_message.status;

  // Member: percent
  cdr >> ros_message.percent;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_diegetic_button_pkg
get_serialized_size(
  const diegetic_button_pkg::msg::InputStatus & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: input_id
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.input_id.size() + 1);
  // Member: status
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.status.size() + 1);
  // Member: percent
  {
    size_t item_size = sizeof(ros_message.percent);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_diegetic_button_pkg
max_serialized_size_InputStatus(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;


  // Member: input_id
  {
    size_t array_size = 1;

    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }

  // Member: status
  {
    size_t array_size = 1;

    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }

  // Member: percent
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  return current_alignment - initial_alignment;
}

static bool _InputStatus__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const diegetic_button_pkg::msg::InputStatus *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _InputStatus__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<diegetic_button_pkg::msg::InputStatus *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _InputStatus__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const diegetic_button_pkg::msg::InputStatus *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _InputStatus__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_InputStatus(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _InputStatus__callbacks = {
  "diegetic_button_pkg::msg",
  "InputStatus",
  _InputStatus__cdr_serialize,
  _InputStatus__cdr_deserialize,
  _InputStatus__get_serialized_size,
  _InputStatus__max_serialized_size
};

static rosidl_message_type_support_t _InputStatus__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_InputStatus__callbacks,
  get_message_typesupport_handle_function,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace diegetic_button_pkg

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_diegetic_button_pkg
const rosidl_message_type_support_t *
get_message_type_support_handle<diegetic_button_pkg::msg::InputStatus>()
{
  return &diegetic_button_pkg::msg::typesupport_fastrtps_cpp::_InputStatus__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, diegetic_button_pkg, msg, InputStatus)() {
  return &diegetic_button_pkg::msg::typesupport_fastrtps_cpp::_InputStatus__handle;
}

#ifdef __cplusplus
}
#endif
