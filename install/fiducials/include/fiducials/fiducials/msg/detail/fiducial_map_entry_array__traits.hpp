// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from fiducials:msg/FiducialMapEntryArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__TRAITS_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "fiducials/msg/detail/fiducial_map_entry_array__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'fiducials'
#include "fiducials/msg/detail/fiducial_map_entry__traits.hpp"

namespace fiducials
{

namespace msg
{

inline void to_flow_style_yaml(
  const FiducialMapEntryArray & msg,
  std::ostream & out)
{
  out << "{";
  // member: fiducials
  {
    if (msg.fiducials.size() == 0) {
      out << "fiducials: []";
    } else {
      out << "fiducials: [";
      size_t pending_items = msg.fiducials.size();
      for (auto item : msg.fiducials) {
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
  const FiducialMapEntryArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: fiducials
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.fiducials.size() == 0) {
      out << "fiducials: []\n";
    } else {
      out << "fiducials:\n";
      for (auto item : msg.fiducials) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FiducialMapEntryArray & msg, bool use_flow_style = false)
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

}  // namespace fiducials

namespace rosidl_generator_traits
{

[[deprecated("use fiducials::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const fiducials::msg::FiducialMapEntryArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  fiducials::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fiducials::msg::to_yaml() instead")]]
inline std::string to_yaml(const fiducials::msg::FiducialMapEntryArray & msg)
{
  return fiducials::msg::to_yaml(msg);
}

template<>
inline const char * data_type<fiducials::msg::FiducialMapEntryArray>()
{
  return "fiducials::msg::FiducialMapEntryArray";
}

template<>
inline const char * name<fiducials::msg::FiducialMapEntryArray>()
{
  return "fiducials/msg/FiducialMapEntryArray";
}

template<>
struct has_fixed_size<fiducials::msg::FiducialMapEntryArray>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<fiducials::msg::FiducialMapEntryArray>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<fiducials::msg::FiducialMapEntryArray>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__TRAITS_HPP_
