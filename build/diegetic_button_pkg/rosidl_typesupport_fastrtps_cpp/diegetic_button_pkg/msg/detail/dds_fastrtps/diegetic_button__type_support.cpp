// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from diegetic_button_pkg:msg/DiegeticButton.idl
// generated code does not contain a copyright notice
#include "diegetic_button_pkg/msg/detail/diegetic_button__rosidl_typesupport_fastrtps_cpp.hpp"
#include "diegetic_button_pkg/msg/detail/diegetic_button__struct.hpp"

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
namespace geometry_msgs
{
namespace msg
{
namespace typesupport_fastrtps_cpp
{
bool cdr_serialize(
  const geometry_msgs::msg::Transform &,
  eprosima::fastcdr::Cdr &);
bool cdr_deserialize(
  eprosima::fastcdr::Cdr &,
  geometry_msgs::msg::Transform &);
size_t get_serialized_size(
  const geometry_msgs::msg::Transform &,
  size_t current_alignment);
size_t
max_serialized_size_Transform(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);
}  // namespace typesupport_fastrtps_cpp
}  // namespace msg
}  // namespace geometry_msgs


namespace diegetic_button_pkg
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_diegetic_button_pkg
cdr_serialize(
  const diegetic_button_pkg::msg::DiegeticButton & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: button_id
  cdr << ros_message.button_id;
  // Member: button_transform
  geometry_msgs::msg::typesupport_fastrtps_cpp::cdr_serialize(
    ros_message.button_transform,
    cdr);
  // Member: x0
  cdr << ros_message.x0;
  // Member: y0
  cdr << ros_message.y0;
  // Member: x1
  cdr << ros_message.x1;
  // Member: y1
  cdr << ros_message.y1;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_diegetic_button_pkg
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  diegetic_button_pkg::msg::DiegeticButton & ros_message)
{
  // Member: button_id
  cdr >> ros_message.button_id;

  // Member: button_transform
  geometry_msgs::msg::typesupport_fastrtps_cpp::cdr_deserialize(
    cdr, ros_message.button_transform);

  // Member: x0
  cdr >> ros_message.x0;

  // Member: y0
  cdr >> ros_message.y0;

  // Member: x1
  cdr >> ros_message.x1;

  // Member: y1
  cdr >> ros_message.y1;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_diegetic_button_pkg
get_serialized_size(
  const diegetic_button_pkg::msg::DiegeticButton & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: button_id
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.button_id.size() + 1);
  // Member: button_transform

  current_alignment +=
    geometry_msgs::msg::typesupport_fastrtps_cpp::get_serialized_size(
    ros_message.button_transform, current_alignment);
  // Member: x0
  {
    size_t item_size = sizeof(ros_message.x0);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: y0
  {
    size_t item_size = sizeof(ros_message.y0);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: x1
  {
    size_t item_size = sizeof(ros_message.x1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: y1
  {
    size_t item_size = sizeof(ros_message.y1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_diegetic_button_pkg
max_serialized_size_DiegeticButton(
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


  // Member: button_id
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

  // Member: button_transform
  {
    size_t array_size = 1;


    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      current_alignment +=
        geometry_msgs::msg::typesupport_fastrtps_cpp::max_serialized_size_Transform(
        inner_full_bounded, inner_is_plain, current_alignment);
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Member: x0
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: y0
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: x1
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: y1
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  return current_alignment - initial_alignment;
}

static bool _DiegeticButton__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const diegetic_button_pkg::msg::DiegeticButton *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _DiegeticButton__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<diegetic_button_pkg::msg::DiegeticButton *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _DiegeticButton__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const diegetic_button_pkg::msg::DiegeticButton *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _DiegeticButton__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_DiegeticButton(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _DiegeticButton__callbacks = {
  "diegetic_button_pkg::msg",
  "DiegeticButton",
  _DiegeticButton__cdr_serialize,
  _DiegeticButton__cdr_deserialize,
  _DiegeticButton__get_serialized_size,
  _DiegeticButton__max_serialized_size
};

static rosidl_message_type_support_t _DiegeticButton__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_DiegeticButton__callbacks,
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
get_message_type_support_handle<diegetic_button_pkg::msg::DiegeticButton>()
{
  return &diegetic_button_pkg::msg::typesupport_fastrtps_cpp::_DiegeticButton__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, diegetic_button_pkg, msg, DiegeticButton)() {
  return &diegetic_button_pkg::msg::typesupport_fastrtps_cpp::_DiegeticButton__handle;
}

#ifdef __cplusplus
}
#endif
