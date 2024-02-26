// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from diegetic_button_pkg:msg/DiegeticButtonArray.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "diegetic_button_pkg/msg/detail/diegetic_button_array__struct.hpp"
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

void DiegeticButtonArray_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) diegetic_button_pkg::msg::DiegeticButtonArray(_init);
}

void DiegeticButtonArray_fini_function(void * message_memory)
{
  auto typed_message = static_cast<diegetic_button_pkg::msg::DiegeticButtonArray *>(message_memory);
  typed_message->~DiegeticButtonArray();
}

size_t size_function__DiegeticButtonArray__buttons(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<diegetic_button_pkg::msg::DiegeticButton> *>(untyped_member);
  return member->size();
}

const void * get_const_function__DiegeticButtonArray__buttons(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<diegetic_button_pkg::msg::DiegeticButton> *>(untyped_member);
  return &member[index];
}

void * get_function__DiegeticButtonArray__buttons(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<diegetic_button_pkg::msg::DiegeticButton> *>(untyped_member);
  return &member[index];
}

void fetch_function__DiegeticButtonArray__buttons(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const diegetic_button_pkg::msg::DiegeticButton *>(
    get_const_function__DiegeticButtonArray__buttons(untyped_member, index));
  auto & value = *reinterpret_cast<diegetic_button_pkg::msg::DiegeticButton *>(untyped_value);
  value = item;
}

void assign_function__DiegeticButtonArray__buttons(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<diegetic_button_pkg::msg::DiegeticButton *>(
    get_function__DiegeticButtonArray__buttons(untyped_member, index));
  const auto & value = *reinterpret_cast<const diegetic_button_pkg::msg::DiegeticButton *>(untyped_value);
  item = value;
}

void resize_function__DiegeticButtonArray__buttons(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<diegetic_button_pkg::msg::DiegeticButton> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember DiegeticButtonArray_message_member_array[2] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg::msg::DiegeticButtonArray, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "buttons",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<diegetic_button_pkg::msg::DiegeticButton>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg::msg::DiegeticButtonArray, buttons),  // bytes offset in struct
    nullptr,  // default value
    size_function__DiegeticButtonArray__buttons,  // size() function pointer
    get_const_function__DiegeticButtonArray__buttons,  // get_const(index) function pointer
    get_function__DiegeticButtonArray__buttons,  // get(index) function pointer
    fetch_function__DiegeticButtonArray__buttons,  // fetch(index, &value) function pointer
    assign_function__DiegeticButtonArray__buttons,  // assign(index, value) function pointer
    resize_function__DiegeticButtonArray__buttons  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers DiegeticButtonArray_message_members = {
  "diegetic_button_pkg::msg",  // message namespace
  "DiegeticButtonArray",  // message name
  2,  // number of fields
  sizeof(diegetic_button_pkg::msg::DiegeticButtonArray),
  DiegeticButtonArray_message_member_array,  // message members
  DiegeticButtonArray_init_function,  // function to initialize message memory (memory has to be allocated)
  DiegeticButtonArray_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t DiegeticButtonArray_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &DiegeticButtonArray_message_members,
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
get_message_type_support_handle<diegetic_button_pkg::msg::DiegeticButtonArray>()
{
  return &::diegetic_button_pkg::msg::rosidl_typesupport_introspection_cpp::DiegeticButtonArray_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, diegetic_button_pkg, msg, DiegeticButtonArray)() {
  return &::diegetic_button_pkg::msg::rosidl_typesupport_introspection_cpp::DiegeticButtonArray_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
