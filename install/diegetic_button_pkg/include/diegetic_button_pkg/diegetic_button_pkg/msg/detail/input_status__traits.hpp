// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from diegetic_button_pkg:msg/InputStatus.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__TRAITS_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "diegetic_button_pkg/msg/detail/input_status__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace diegetic_button_pkg
{

namespace msg
{

inline void to_flow_style_yaml(
  const InputStatus & msg,
  std::ostream & out)
{
  out << "{";
  // member: input_id
  {
    out << "input_id: ";
    rosidl_generator_traits::value_to_yaml(msg.input_id, out);
    out << ", ";
  }

  // member: status
  {
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << ", ";
  }

  // member: percent
  {
    out << "percent: ";
    rosidl_generator_traits::value_to_yaml(msg.percent, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const InputStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: input_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "input_id: ";
    rosidl_generator_traits::value_to_yaml(msg.input_id, out);
    out << "\n";
  }

  // member: status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << "\n";
  }

  // member: percent
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "percent: ";
    rosidl_generator_traits::value_to_yaml(msg.percent, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const InputStatus & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace diegetic_button_pkg

namespace rosidl_generator_traits
{

[[deprecated("use diegetic_button_pkg::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const diegetic_button_pkg::msg::InputStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  diegetic_button_pkg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use diegetic_button_pkg::msg::to_yaml() instead")]]
inline std::string to_yaml(const diegetic_button_pkg::msg::InputStatus & msg)
{
  return diegetic_button_pkg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<diegetic_button_pkg::msg::InputStatus>()
{
  return "diegetic_button_pkg::msg::InputStatus";
}

template<>
inline const char * name<diegetic_button_pkg::msg::InputStatus>()
{
  return "diegetic_button_pkg/msg/InputStatus";
}

template<>
struct has_fixed_size<diegetic_button_pkg::msg::InputStatus>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<diegetic_button_pkg::msg::InputStatus>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<diegetic_button_pkg::msg::InputStatus>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__TRAITS_HPP_
