// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from diegetic_button_pkg:msg/InputStatusArray.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "diegetic_button_pkg/msg/detail/input_status_array__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace diegetic_button_pkg
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void InputStatusArray_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) diegetic_button_pkg::msg::InputStatusArray(_init);
}

void InputStatusArray_fini_function(void * message_memory)
{
  auto typed_message = static_cast<diegetic_button_pkg::msg::InputStatusArray *>(message_memory);
  typed_message->~InputStatusArray();
}

size_t size_function__InputStatusArray__inputs(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<diegetic_button_pkg::msg::InputStatus> *>(untyped_member);
  return member->size();
}

const void * get_const_function__InputStatusArray__inputs(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<diegetic_button_pkg::msg::InputStatus> *>(untyped_member);
  return &member[index];
}

void * get_function__InputStatusArray__inputs(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<diegetic_button_pkg::msg::InputStatus> *>(untyped_member);
  return &member[index];
}

void fetch_function__InputStatusArray__inputs(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const diegetic_button_pkg::msg::InputStatus *>(
    get_const_function__InputStatusArray__inputs(untyped_member, index));
  auto & value = *reinterpret_cast<diegetic_button_pkg::msg::InputStatus *>(untyped_value);
  value = item;
}

void assign_function__InputStatusArray__inputs(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<diegetic_button_pkg::msg::InputStatus *>(
    get_function__InputStatusArray__inputs(untyped_member, index));
  const auto & value = *reinterpret_cast<const diegetic_button_pkg::msg::InputStatus *>(untyped_value);
  item = value;
}

void resize_function__InputStatusArray__inputs(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<diegetic_button_pkg::msg::InputStatus> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember InputStatusArray_message_member_array[2] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg::msg::InputStatusArray, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "inputs",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<diegetic_button_pkg::msg::InputStatus>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg::msg::InputStatusArray, inputs),  // bytes offset in struct
    nullptr,  // default value
    size_function__InputStatusArray__inputs,  // size() function pointer
    get_const_function__InputStatusArray__inputs,  // get_const(index) function pointer
    get_function__InputStatusArray__inputs,  // get(index) function pointer
    fetch_function__InputStatusArray__inputs,  // fetch(index, &value) function pointer
    assign_function__InputStatusArray__inputs,  // assign(index, value) function pointer
    resize_function__InputStatusArray__inputs  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers InputStatusArray_message_members = {
  "diegetic_button_pkg::msg",  // message namespace
  "InputStatusArray",  // message name
  2,  // number of fields
  sizeof(diegetic_button_pkg::msg::InputStatusArray),
  InputStatusArray_message_member_array,  // message members
  InputStatusArray_init_function,  // function to initialize message memory (memory has to be allocated)
  InputStatusArray_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t InputStatusArray_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &InputStatusArray_message_members,
  get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace diegetic_button_pkg


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<diegetic_button_pkg::msg::InputStatusArray>()
{
  return &::diegetic_button_pkg::msg::rosidl_typesupport_introspection_cpp::InputStatusArray_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, diegetic_button_pkg, msg, InputStatusArray)() {
  return &::diegetic_button_pkg::msg::rosidl_typesupport_introspection_cpp::InputStatusArray_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
