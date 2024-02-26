// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from diegetic_button_pkg:msg/DiegeticButtonArray.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__BUILDER_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "diegetic_button_pkg/msg/detail/diegetic_button_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace diegetic_button_pkg
{

namespace msg
{

namespace builder
{

class Init_DiegeticButtonArray_buttons
{
public:
  explicit Init_DiegeticButtonArray_buttons(::diegetic_button_pkg::msg::DiegeticButtonArray & msg)
  : msg_(msg)
  {}
  ::diegetic_button_pkg::msg::DiegeticButtonArray buttons(::diegetic_button_pkg::msg::DiegeticButtonArray::_buttons_type arg)
  {
    msg_.buttons = std::move(arg);
    return std::move(msg_);
  }

private:
  ::diegetic_button_pkg::msg::DiegeticButtonArray msg_;
};

class Init_DiegeticButtonArray_header
{
public:
  Init_DiegeticButtonArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DiegeticButtonArray_buttons header(::diegetic_button_pkg::msg::DiegeticButtonArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_DiegeticButtonArray_buttons(msg_);
  }

private:
  ::diegetic_button_pkg::msg::DiegeticButtonArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::diegetic_button_pkg::msg::DiegeticButtonArray>()
{
  return diegetic_button_pkg::msg::builder::Init_DiegeticButtonArray_header();
}

}  // namespace diegetic_button_pkg

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__BUILDER_HPP_
