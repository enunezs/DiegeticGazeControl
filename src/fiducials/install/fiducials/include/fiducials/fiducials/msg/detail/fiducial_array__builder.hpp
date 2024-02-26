// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from fiducials:msg/FiducialArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_ARRAY__BUILDER_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "fiducials/msg/detail/fiducial_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace fiducials
{

namespace msg
{

namespace builder
{

class Init_FiducialArray_fiducials
{
public:
  explicit Init_FiducialArray_fiducials(::fiducials::msg::FiducialArray & msg)
  : msg_(msg)
  {}
  ::fiducials::msg::FiducialArray fiducials(::fiducials::msg::FiducialArray::_fiducials_type arg)
  {
    msg_.fiducials = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fiducials::msg::FiducialArray msg_;
};

class Init_FiducialArray_image_seq
{
public:
  explicit Init_FiducialArray_image_seq(::fiducials::msg::FiducialArray & msg)
  : msg_(msg)
  {}
  Init_FiducialArray_fiducials image_seq(::fiducials::msg::FiducialArray::_image_seq_type arg)
  {
    msg_.image_seq = std::move(arg);
    return Init_FiducialArray_fiducials(msg_);
  }

private:
  ::fiducials::msg::FiducialArray msg_;
};

class Init_FiducialArray_header
{
public:
  Init_FiducialArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FiducialArray_image_seq header(::fiducials::msg::FiducialArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FiducialArray_image_seq(msg_);
  }

private:
  ::fiducials::msg::FiducialArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::fiducials::msg::FiducialArray>()
{
  return fiducials::msg::builder::Init_FiducialArray_header();
}

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_ARRAY__BUILDER_HPP_
