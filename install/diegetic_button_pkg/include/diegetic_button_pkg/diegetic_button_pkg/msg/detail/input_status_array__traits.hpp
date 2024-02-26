// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from diegetic_button_pkg:msg/InputStatusArray.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__TRAITS_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "diegetic_button_pkg/msg/detail/input_status_array__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'inputs'
#include "diegetic_button_pkg/msg/detail/input_status__traits.hpp"

namespace diegetic_button_pkg
{

namespace msg
{

inline void to_flow_style_yaml(
  const InputStatusArray & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: inputs
  {
    if (msg.inputs.size() == 0) {
      out << "inputs: []";
    } else {
      out << "inputs: [";
      size_t pending_items = msg.inputs.size();
      for (auto item : msg.inputs) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const InputStatusArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: inputs
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.inputs.size() == 0) {
      out << "inputs: []\n";
    } else {
      out << "inputs:\n";
      for (auto item : msg.inputs) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const InputStatusArray & msg, bool use_flow_style = false)
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
  const diegetic_button_pkg::msg::InputStatusArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  diegetic_button_pkg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use diegetic_button_pkg::msg::to_yaml() instead")]]
inline std::string to_yaml(const diegetic_button_pkg::msg::InputStatusArray & msg)
{
  return diegetic_button_pkg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<diegetic_button_pkg::msg::InputStatusArray>()
{
  return "diegetic_button_pkg::msg::InputStatusArray";
}

template<>
inline const char * name<diegetic_button_pkg::msg::InputStatusArray>()
{
  return "diegetic_button_pkg/msg/InputStatusArray";
}

template<>
struct has_fixed_size<diegetic_button_pkg::msg::InputStatusArray>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<diegetic_button_pkg::msg::InputStatusArray>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<diegetic_button_pkg::msg::InputStatusArray>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__TRAITS_HPP_
