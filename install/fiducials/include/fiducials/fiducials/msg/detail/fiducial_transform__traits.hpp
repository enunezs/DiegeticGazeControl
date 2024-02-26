// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from fiducials:msg/FiducialTransform.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__TRAITS_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "fiducials/msg/detail/fiducial_transform__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'transform'
#include "geometry_msgs/msg/detail/transform__traits.hpp"

namespace fiducials
{

namespace msg
{

inline void to_flow_style_yaml(
  const FiducialTransform & msg,
  std::ostream & out)
{
  out << "{";
  // member: fiducial_id
  {
    out << "fiducial_id: ";
    rosidl_generator_traits::value_to_yaml(msg.fiducial_id, out);
    out << ", ";
  }

  // member: transform
  {
    out << "transform: ";
    to_flow_style_yaml(msg.transform, out);
    out << ", ";
  }

  // member: image_error
  {
    out << "image_error: ";
    rosidl_generator_traits::value_to_yaml(msg.image_error, out);
    out << ", ";
  }

  // member: object_error
  {
    out << "object_error: ";
    rosidl_generator_traits::value_to_yaml(msg.object_error, out);
    out << ", ";
  }

  // member: fiducial_area
  {
    out << "fiducial_area: ";
    rosidl_generator_traits::value_to_yaml(msg.fiducial_area, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const FiducialTransform & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: fiducial_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fiducial_id: ";
    rosidl_generator_traits::value_to_yaml(msg.fiducial_id, out);
    out << "\n";
  }

  // member: transform
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "transform:\n";
    to_block_style_yaml(msg.transform, out, indentation + 2);
  }

  // member: image_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "image_error: ";
    rosidl_generator_traits::value_to_yaml(msg.image_error, out);
    out << "\n";
  }

  // member: object_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "object_error: ";
    rosidl_generator_traits::value_to_yaml(msg.object_error, out);
    out << "\n";
  }

  // member: fiducial_area
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fiducial_area: ";
    rosidl_generator_traits::value_to_yaml(msg.fiducial_area, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FiducialTransform & msg, bool use_flow_style = false)
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
  const fiducials::msg::FiducialTransform & msg,
  std::ostream & out, size_t indentation = 0)
{
  fiducials::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fiducials::msg::to_yaml() instead")]]
inline std::string to_yaml(const fiducials::msg::FiducialTransform & msg)
{
  return fiducials::msg::to_yaml(msg);
}

template<>
inline const char * data_type<fiducials::msg::FiducialTransform>()
{
  return "fiducials::msg::FiducialTransform";
}

template<>
inline const char * name<fiducials::msg::FiducialTransform>()
{
  return "fiducials/msg/FiducialTransform";
}

template<>
struct has_fixed_size<fiducials::msg::FiducialTransform>
  : std::integral_constant<bool, has_fixed_size<geometry_msgs::msg::Transform>::value> {};

template<>
struct has_bounded_size<fiducials::msg::FiducialTransform>
  : std::integral_constant<bool, has_bounded_size<geometry_msgs::msg::Transform>::value> {};

template<>
struct is_message<fiducials::msg::FiducialTransform>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__TRAITS_HPP_
