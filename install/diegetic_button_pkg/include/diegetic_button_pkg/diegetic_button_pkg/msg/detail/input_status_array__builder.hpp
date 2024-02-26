// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from diegetic_button_pkg:msg/InputStatusArray.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__BUILDER_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "diegetic_button_pkg/msg/detail/input_status_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace diegetic_button_pkg
{

namespace msg
{

namespace builder
{

class Init_InputStatusArray_inputs
{
public:
  explicit Init_InputStatusArray_inputs(::diegetic_button_pkg::msg::InputStatusArray & msg)
  : msg_(msg)
  {}
  ::diegetic_button_pkg::msg::InputStatusArray inputs(::diegetic_button_pkg::msg::InputStatusArray::_inputs_type arg)
  {
    msg_.inputs = std::move(arg);
    return std::move(msg_);
  }

private:
  ::diegetic_button_pkg::msg::InputStatusArray msg_;
};

class Init_InputStatusArray_header
{
public:
  Init_InputStatusArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_InputStatusArray_inputs header(::diegetic_button_pkg::msg::InputStatusArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_InputStatusArray_inputs(msg_);
  }

private:
  ::diegetic_button_pkg::msg::InputStatusArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::diegetic_button_pkg::msg::InputStatusArray>()
{
  return diegetic_button_pkg::msg::builder::Init_InputStatusArray_header();
}

}  // namespace diegetic_button_pkg

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__BUILDER_HPP_
