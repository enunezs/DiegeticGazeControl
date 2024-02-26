// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from fiducials:msg/FiducialArray.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "fiducials/msg/detail/fiducial_array__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace fiducials
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void FiducialArray_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) fiducials::msg::FiducialArray(_init);
}

void FiducialArray_fini_function(void * message_memory)
{
  auto typed_message = static_cast<fiducials::msg::FiducialArray *>(message_memory);
  typed_message->~FiducialArray();
}

size_t size_function__FiducialArray__fiducials(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<fiducials::msg::Fiducial> *>(untyped_member);
  return member->size();
}

const void * get_const_function__FiducialArray__fiducials(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<fiducials::msg::Fiducial> *>(untyped_member);
  return &member[index];
}

void * get_function__FiducialArray__fiducials(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<fiducials::msg::Fiducial> *>(untyped_member);
  return &member[index];
}

void fetch_function__FiducialArray__fiducials(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const fiducials::msg::Fiducial *>(
    get_const_function__FiducialArray__fiducials(untyped_member, index));
  auto & value = *reinterpret_cast<fiducials::msg::Fiducial *>(untyped_value);
  value = item;
}

void assign_function__FiducialArray__fiducials(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<fiducials::msg::Fiducial *>(
    get_function__FiducialArray__fiducials(untyped_member, index));
  const auto & value = *reinterpret_cast<const fiducials::msg::Fiducial *>(untyped_value);
  item = value;
}

void resize_function__FiducialArray__fiducials(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<fiducials::msg::Fiducial> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember FiducialArray_message_member_array[3] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials::msg::FiducialArray, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "image_seq",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials::msg::FiducialArray, image_seq),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "fiducials",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<fiducials::msg::Fiducial>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(fiducials::msg::FiducialArray, fiducials),  // bytes offset in struct
    nullptr,  // default value
    size_function__FiducialArray__fiducials,  // size() function pointer
    get_const_function__FiducialArray__fiducials,  // get_const(index) function pointer
    get_function__FiducialArray__fiducials,  // get(index) function pointer
    fetch_function__FiducialArray__fiducials,  // fetch(index, &value) function pointer
    assign_function__FiducialArray__fiducials,  // assign(index, value) function pointer
    resize_function__FiducialArray__fiducials  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers FiducialArray_message_members = {
  "fiducials::msg",  // message namespace
  "FiducialArray",  // message name
  3,  // number of fields
  sizeof(fiducials::msg::FiducialArray),
  FiducialArray_message_member_array,  // message members
  FiducialArray_init_function,  // function to initialize message memory (memory has to be allocated)
  FiducialArray_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t FiducialArray_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &FiducialArray_message_members,
  get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace fiducials


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<fiducials::msg::FiducialArray>()
{
  return &::fiducials::msg::rosidl_typesupport_introspection_cpp::FiducialArray_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, fiducials, msg, FiducialArray)() {
  return &::fiducials::msg::rosidl_typesupport_introspection_cpp::FiducialArray_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
