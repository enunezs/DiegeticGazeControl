// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from diegetic_button_pkg:msg/DiegeticButton.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__TRAITS_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "diegetic_button_pkg/msg/detail/diegetic_button__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'button_transform'
#include "geometry_msgs/msg/detail/transform__traits.hpp"

namespace diegetic_button_pkg
{

namespace msg
{

inline void to_flow_style_yaml(
  const DiegeticButton & msg,
  std::ostream & out)
{
  out << "{";
  // member: button_id
  {
    out << "button_id: ";
    rosidl_generator_traits::value_to_yaml(msg.button_id, out);
    out << ", ";
  }

  // member: button_transform
  {
    out << "button_transform: ";
    to_flow_style_yaml(msg.button_transform, out);
    out << ", ";
  }

  // member: x0
  {
    out << "x0: ";
    rosidl_generator_traits::value_to_yaml(msg.x0, out);
    out << ", ";
  }

  // member: y0
  {
    out << "y0: ";
    rosidl_generator_traits::value_to_yaml(msg.y0, out);
    out << ", ";
  }

  // member: x1
  {
    out << "x1: ";
    rosidl_generator_traits::value_to_yaml(msg.x1, out);
    out << ", ";
  }

  // member: y1
  {
    out << "y1: ";
    rosidl_generator_traits::value_to_yaml(msg.y1, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DiegeticButton & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: button_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "button_id: ";
    rosidl_generator_traits::value_to_yaml(msg.button_id, out);
    out << "\n";
  }

  // member: button_transform
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "button_transform:\n";
    to_block_style_yaml(msg.button_transform, out, indentation + 2);
  }

  // member: x0
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "x0: ";
    rosidl_generator_traits::value_to_yaml(msg.x0, out);
    out << "\n";
  }

  // member: y0
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "y0: ";
    rosidl_generator_traits::value_to_yaml(msg.y0, out);
    out << "\n";
  }

  // member: x1
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "x1: ";
    rosidl_generator_traits::value_to_yaml(msg.x1, out);
    out << "\n";
  }

  // member: y1
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "y1: ";
    rosidl_generator_traits::value_to_yaml(msg.y1, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DiegeticButton & msg, bool use_flow_style = false)
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
  const diegetic_button_pkg::msg::DiegeticButton & msg,
  std::ostream & out, size_t indentation = 0)
{
  diegetic_button_pkg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use diegetic_button_pkg::msg::to_yaml() instead")]]
inline std::string to_yaml(const diegetic_button_pkg::msg::DiegeticButton & msg)
{
  return diegetic_button_pkg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<diegetic_button_pkg::msg::DiegeticButton>()
{
  return "diegetic_button_pkg::msg::DiegeticButton";
}

template<>
inline const char * name<diegetic_button_pkg::msg::DiegeticButton>()
{
  return "diegetic_button_pkg/msg/DiegeticButton";
}

template<>
struct has_fixed_size<diegetic_button_pkg::msg::DiegeticButton>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<diegetic_button_pkg::msg::DiegeticButton>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<diegetic_button_pkg::msg::DiegeticButton>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__TRAITS_HPP_
