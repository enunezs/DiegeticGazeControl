// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from diegetic_button_pkg:msg/InputStatus.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__BUILDER_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "diegetic_button_pkg/msg/detail/input_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace diegetic_button_pkg
{

namespace msg
{

namespace builder
{

class Init_InputStatus_percent
{
public:
  explicit Init_InputStatus_percent(::diegetic_button_pkg::msg::InputStatus & msg)
  : msg_(msg)
  {}
  ::diegetic_button_pkg::msg::InputStatus percent(::diegetic_button_pkg::msg::InputStatus::_percent_type arg)
  {
    msg_.percent = std::move(arg);
    return std::move(msg_);
  }

private:
  ::diegetic_button_pkg::msg::InputStatus msg_;
};

class Init_InputStatus_status
{
public:
  explicit Init_InputStatus_status(::diegetic_button_pkg::msg::InputStatus & msg)
  : msg_(msg)
  {}
  Init_InputStatus_percent status(::diegetic_button_pkg::msg::InputStatus::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_InputStatus_percent(msg_);
  }

private:
  ::diegetic_button_pkg::msg::InputStatus msg_;
};

class Init_InputStatus_input_id
{
public:
  Init_InputStatus_input_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_InputStatus_status input_id(::diegetic_button_pkg::msg::InputStatus::_input_id_type arg)
  {
    msg_.input_id = std::move(arg);
    return Init_InputStatus_status(msg_);
  }

private:
  ::diegetic_button_pkg::msg::InputStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::diegetic_button_pkg::msg::InputStatus>()
{
  return diegetic_button_pkg::msg::builder::Init_InputStatus_input_id();
}

}  // namespace diegetic_button_pkg

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__BUILDER_HPP_
