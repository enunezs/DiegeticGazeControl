// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from fiducials:msg/Fiducial.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL__BUILDER_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "fiducials/msg/detail/fiducial__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace fiducials
{

namespace msg
{

namespace builder
{

class Init_Fiducial_y3
{
public:
  explicit Init_Fiducial_y3(::fiducials::msg::Fiducial & msg)
  : msg_(msg)
  {}
  ::fiducials::msg::Fiducial y3(::fiducials::msg::Fiducial::_y3_type arg)
  {
    msg_.y3 = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

class Init_Fiducial_x3
{
public:
  explicit Init_Fiducial_x3(::fiducials::msg::Fiducial & msg)
  : msg_(msg)
  {}
  Init_Fiducial_y3 x3(::fiducials::msg::Fiducial::_x3_type arg)
  {
    msg_.x3 = std::move(arg);
    return Init_Fiducial_y3(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

class Init_Fiducial_y2
{
public:
  explicit Init_Fiducial_y2(::fiducials::msg::Fiducial & msg)
  : msg_(msg)
  {}
  Init_Fiducial_x3 y2(::fiducials::msg::Fiducial::_y2_type arg)
  {
    msg_.y2 = std::move(arg);
    return Init_Fiducial_x3(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

class Init_Fiducial_x2
{
public:
  explicit Init_Fiducial_x2(::fiducials::msg::Fiducial & msg)
  : msg_(msg)
  {}
  Init_Fiducial_y2 x2(::fiducials::msg::Fiducial::_x2_type arg)
  {
    msg_.x2 = std::move(arg);
    return Init_Fiducial_y2(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

class Init_Fiducial_y1
{
public:
  explicit Init_Fiducial_y1(::fiducials::msg::Fiducial & msg)
  : msg_(msg)
  {}
  Init_Fiducial_x2 y1(::fiducials::msg::Fiducial::_y1_type arg)
  {
    msg_.y1 = std::move(arg);
    return Init_Fiducial_x2(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

class Init_Fiducial_x1
{
public:
  explicit Init_Fiducial_x1(::fiducials::msg::Fiducial & msg)
  : msg_(msg)
  {}
  Init_Fiducial_y1 x1(::fiducials::msg::Fiducial::_x1_type arg)
  {
    msg_.x1 = std::move(arg);
    return Init_Fiducial_y1(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

class Init_Fiducial_y0
{
public:
  explicit Init_Fiducial_y0(::fiducials::msg::Fiducial & msg)
  : msg_(msg)
  {}
  Init_Fiducial_x1 y0(::fiducials::msg::Fiducial::_y0_type arg)
  {
    msg_.y0 = std::move(arg);
    return Init_Fiducial_x1(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

class Init_Fiducial_x0
{
public:
  explicit Init_Fiducial_x0(::fiducials::msg::Fiducial & msg)
  : msg_(msg)
  {}
  Init_Fiducial_y0 x0(::fiducials::msg::Fiducial::_x0_type arg)
  {
    msg_.x0 = std::move(arg);
    return Init_Fiducial_y0(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

class Init_Fiducial_direction
{
public:
  explicit Init_Fiducial_direction(::fiducials::msg::Fiducial & msg)
  : msg_(msg)
  {}
  Init_Fiducial_x0 direction(::fiducials::msg::Fiducial::_direction_type arg)
  {
    msg_.direction = std::move(arg);
    return Init_Fiducial_x0(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

class Init_Fiducial_fiducial_id
{
public:
  Init_Fiducial_fiducial_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Fiducial_direction fiducial_id(::fiducials::msg::Fiducial::_fiducial_id_type arg)
  {
    msg_.fiducial_id = std::move(arg);
    return Init_Fiducial_direction(msg_);
  }

private:
  ::fiducials::msg::Fiducial msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::fiducials::msg::Fiducial>()
{
  return fiducials::msg::builder::Init_Fiducial_fiducial_id();
}

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL__BUILDER_HPP_
