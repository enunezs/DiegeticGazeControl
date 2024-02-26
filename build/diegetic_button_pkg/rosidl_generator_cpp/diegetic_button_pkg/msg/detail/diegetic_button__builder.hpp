// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from diegetic_button_pkg:msg/DiegeticButton.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__BUILDER_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "diegetic_button_pkg/msg/detail/diegetic_button__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace diegetic_button_pkg
{

namespace msg
{

namespace builder
{

class Init_DiegeticButton_y1
{
public:
  explicit Init_DiegeticButton_y1(::diegetic_button_pkg::msg::DiegeticButton & msg)
  : msg_(msg)
  {}
  ::diegetic_button_pkg::msg::DiegeticButton y1(::diegetic_button_pkg::msg::DiegeticButton::_y1_type arg)
  {
    msg_.y1 = std::move(arg);
    return std::move(msg_);
  }

private:
  ::diegetic_button_pkg::msg::DiegeticButton msg_;
};

class Init_DiegeticButton_x1
{
public:
  explicit Init_DiegeticButton_x1(::diegetic_button_pkg::msg::DiegeticButton & msg)
  : msg_(msg)
  {}
  Init_DiegeticButton_y1 x1(::diegetic_button_pkg::msg::DiegeticButton::_x1_type arg)
  {
    msg_.x1 = std::move(arg);
    return Init_DiegeticButton_y1(msg_);
  }

private:
  ::diegetic_button_pkg::msg::DiegeticButton msg_;
};

class Init_DiegeticButton_y0
{
public:
  explicit Init_DiegeticButton_y0(::diegetic_button_pkg::msg::DiegeticButton & msg)
  : msg_(msg)
  {}
  Init_DiegeticButton_x1 y0(::diegetic_button_pkg::msg::DiegeticButton::_y0_type arg)
  {
    msg_.y0 = std::move(arg);
    return Init_DiegeticButton_x1(msg_);
  }

private:
  ::diegetic_button_pkg::msg::DiegeticButton msg_;
};

class Init_DiegeticButton_x0
{
public:
  explicit Init_DiegeticButton_x0(::diegetic_button_pkg::msg::DiegeticButton & msg)
  : msg_(msg)
  {}
  Init_DiegeticButton_y0 x0(::diegetic_button_pkg::msg::DiegeticButton::_x0_type arg)
  {
    msg_.x0 = std::move(arg);
    return Init_DiegeticButton_y0(msg_);
  }

private:
  ::diegetic_button_pkg::msg::DiegeticButton msg_;
};

class Init_DiegeticButton_button_transform
{
public:
  explicit Init_DiegeticButton_button_transform(::diegetic_button_pkg::msg::DiegeticButton & msg)
  : msg_(msg)
  {}
  Init_DiegeticButton_x0 button_transform(::diegetic_button_pkg::msg::DiegeticButton::_button_transform_type arg)
  {
    msg_.button_transform = std::move(arg);
    return Init_DiegeticButton_x0(msg_);
  }

private:
  ::diegetic_button_pkg::msg::DiegeticButton msg_;
};

class Init_DiegeticButton_button_id
{
public:
  Init_DiegeticButton_button_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DiegeticButton_button_transform button_id(::diegetic_button_pkg::msg::DiegeticButton::_button_id_type arg)
  {
    msg_.button_id = std::move(arg);
    return Init_DiegeticButton_button_transform(msg_);
  }

private:
  ::diegetic_button_pkg::msg::DiegeticButton msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::diegetic_button_pkg::msg::DiegeticButton>()
{
  return diegetic_button_pkg::msg::builder::Init_DiegeticButton_button_id();
}

}  // namespace diegetic_button_pkg

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__BUILDER_HPP_
