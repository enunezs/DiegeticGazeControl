// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from fiducials:msg/FiducialMapEntryArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__BUILDER_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "fiducials/msg/detail/fiducial_map_entry_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace fiducials
{

namespace msg
{

namespace builder
{

class Init_FiducialMapEntryArray_fiducials
{
public:
  Init_FiducialMapEntryArray_fiducials()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::fiducials::msg::FiducialMapEntryArray fiducials(::fiducials::msg::FiducialMapEntryArray::_fiducials_type arg)
  {
    msg_.fiducials = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fiducials::msg::FiducialMapEntryArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::fiducials::msg::FiducialMapEntryArray>()
{
  return fiducials::msg::builder::Init_FiducialMapEntryArray_fiducials();
}

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__BUILDER_HPP_
