// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from fiducials:msg/FiducialTransformArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM_ARRAY__TRAITS_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM_ARRAY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "fiducials/msg/detail/fiducial_transform_array__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'transforms'
#include "fiducials/msg/detail/fiducial_transform__traits.hpp"

namespace fiducials
{

namespace msg
{

inline void to_flow_style_yaml(
  const FiducialTransformArray & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: image_seq
  {
    out << "image_seq: ";
    rosidl_generator_traits::value_to_yaml(msg.image_seq, out);
    out << ", ";
  }

  // member: transforms
  {
    if (msg.transforms.size() == 0) {
      out << "transforms: []";
    } else {
      out << "transforms: [";
      size_t pending_items = msg.transforms.size();
      for (auto item : msg.transforms) {
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
  const FiducialTransformArray & msg,
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

  // member: image_seq
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "image_seq: ";
    rosidl_generator_traits::value_to_yaml(msg.image_seq, out);
    out << "\n";
  }

  // member: transforms
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.transforms.size() == 0) {
      out << "transforms: []\n";
    } else {
      out << "transforms:\n";
      for (auto item : msg.transforms) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FiducialTransformArray & msg, bool use_flow_style = false)
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
  const fiducials::msg::FiducialTransformArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  fiducials::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fiducials::msg::to_yaml() instead")]]
inline std::string to_yaml(const fiducials::msg::FiducialTransformArray & msg)
{
  return fiducials::msg::to_yaml(msg);
}

template<>
inline const char * data_type<fiducials::msg::FiducialTransformArray>()
{
  return "fiducials::msg::FiducialTransformArray";
}

template<>
inline const char * name<fiducials::msg::FiducialTransformArray>()
{
  return "fiducials/msg/FiducialTransformArray";
}

template<>
struct has_fixed_size<fiducials::msg::FiducialTransformArray>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<fiducials::msg::FiducialTransformArray>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<fiducials::msg::FiducialTransformArray>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM_ARRAY__TRAITS_HPP_
