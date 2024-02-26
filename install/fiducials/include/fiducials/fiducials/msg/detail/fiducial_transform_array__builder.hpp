// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from fiducials:msg/FiducialTransformArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM_ARRAY__BUILDER_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "fiducials/msg/detail/fiducial_transform_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace fiducials
{

namespace msg
{

namespace builder
{

class Init_FiducialTransformArray_transforms
{
public:
  explicit Init_FiducialTransformArray_transforms(::fiducials::msg::FiducialTransformArray & msg)
  : msg_(msg)
  {}
  ::fiducials::msg::FiducialTransformArray transforms(::fiducials::msg::FiducialTransformArray::_transforms_type arg)
  {
    msg_.transforms = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fiducials::msg::FiducialTransformArray msg_;
};

class Init_FiducialTransformArray_image_seq
{
public:
  explicit Init_FiducialTransformArray_image_seq(::fiducials::msg::FiducialTransformArray & msg)
  : msg_(msg)
  {}
  Init_FiducialTransformArray_transforms image_seq(::fiducials::msg::FiducialTransformArray::_image_seq_type arg)
  {
    msg_.image_seq = std::move(arg);
    return Init_FiducialTransformArray_transforms(msg_);
  }

private:
  ::fiducials::msg::FiducialTransformArray msg_;
};

class Init_FiducialTransformArray_header
{
public:
  Init_FiducialTransformArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FiducialTransformArray_image_seq header(::fiducials::msg::FiducialTransformArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FiducialTransformArray_image_seq(msg_);
  }

private:
  ::fiducials::msg::FiducialTransformArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::fiducials::msg::FiducialTransformArray>()
{
  return fiducials::msg::builder::Init_FiducialTransformArray_header();
}

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM_ARRAY__BUILDER_HPP_
