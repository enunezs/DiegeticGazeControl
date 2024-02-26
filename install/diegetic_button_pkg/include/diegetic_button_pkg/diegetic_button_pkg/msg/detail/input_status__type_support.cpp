// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from diegetic_button_pkg:msg/InputStatus.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "diegetic_button_pkg/msg/detail/input_status__struct.hpp"
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

void InputStatus_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) diegetic_button_pkg::msg::InputStatus(_init);
}

void InputStatus_fini_function(void * message_memory)
{
  auto typed_message = static_cast<diegetic_button_pkg::msg::InputStatus *>(message_memory);
  typed_message->~InputStatus();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember InputStatus_message_member_array[3] = {
  {
    "input_id",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg::msg::InputStatus, input_id),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "status",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg::msg::InputStatus, status),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "percent",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(diegetic_button_pkg::msg::InputStatus, percent),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers InputStatus_message_members = {
  "diegetic_button_pkg::msg",  // message namespace
  "InputStatus",  // message name
  3,  // number of fields
  sizeof(diegetic_button_pkg::msg::InputStatus),
  InputStatus_message_member_array,  // message members
  InputStatus_init_function,  // function to initialize message memory (memory has to be allocated)
  InputStatus_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t InputStatus_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &InputStatus_message_members,
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
get_message_type_support_handle<diegetic_button_pkg::msg::InputStatus>()
{
  return &::diegetic_button_pkg::msg::rosidl_typesupport_introspection_cpp::InputStatus_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, diegetic_button_pkg, msg, InputStatus)() {
  return &::diegetic_button_pkg::msg::rosidl_typesupport_introspection_cpp::InputStatus_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
