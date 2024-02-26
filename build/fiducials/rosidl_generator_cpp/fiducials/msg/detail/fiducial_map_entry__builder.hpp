// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from fiducials:msg/FiducialMapEntry.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY__BUILDER_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "fiducials/msg/detail/fiducial_map_entry__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace fiducials
{

namespace msg
{

namespace builder
{

class Init_FiducialMapEntry_rz
{
public:
  explicit Init_FiducialMapEntry_rz(::fiducials::msg::FiducialMapEntry & msg)
  : msg_(msg)
  {}
  ::fiducials::msg::FiducialMapEntry rz(::fiducials::msg::FiducialMapEntry::_rz_type arg)
  {
    msg_.rz = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fiducials::msg::FiducialMapEntry msg_;
};

class Init_FiducialMapEntry_ry
{
public:
  explicit Init_FiducialMapEntry_ry(::fiducials::msg::FiducialMapEntry & msg)
  : msg_(msg)
  {}
  Init_FiducialMapEntry_rz ry(::fiducials::msg::FiducialMapEntry::_ry_type arg)
  {
    msg_.ry = std::move(arg);
    return Init_FiducialMapEntry_rz(msg_);
  }

private:
  ::fiducials::msg::FiducialMapEntry msg_;
};

class Init_FiducialMapEntry_rx
{
public:
  explicit Init_FiducialMapEntry_rx(::fiducials::msg::FiducialMapEntry & msg)
  : msg_(msg)
  {}
  Init_FiducialMapEntry_ry rx(::fiducials::msg::FiducialMapEntry::_rx_type arg)
  {
    msg_.rx = std::move(arg);
    return Init_FiducialMapEntry_ry(msg_);
  }

private:
  ::fiducials::msg::FiducialMapEntry msg_;
};

class Init_FiducialMapEntry_z
{
public:
  explicit Init_FiducialMapEntry_z(::fiducials::msg::FiducialMapEntry & msg)
  : msg_(msg)
  {}
  Init_FiducialMapEntry_rx z(::fiducials::msg::FiducialMapEntry::_z_type arg)
  {
    msg_.z = std::move(arg);
    return Init_FiducialMapEntry_rx(msg_);
  }

private:
  ::fiducials::msg::FiducialMapEntry msg_;
};

class Init_FiducialMapEntry_y
{
public:
  explicit Init_FiducialMapEntry_y(::fiducials::msg::FiducialMapEntry & msg)
  : msg_(msg)
  {}
  Init_FiducialMapEntry_z y(::fiducials::msg::FiducialMapEntry::_y_type arg)
  {
    msg_.y = std::move(arg);
    return Init_FiducialMapEntry_z(msg_);
  }

private:
  ::fiducials::msg::FiducialMapEntry msg_;
};

class Init_FiducialMapEntry_x
{
public:
  explicit Init_FiducialMapEntry_x(::fiducials::msg::FiducialMapEntry & msg)
  : msg_(msg)
  {}
  Init_FiducialMapEntry_y x(::fiducials::msg::FiducialMapEntry::_x_type arg)
  {
    msg_.x = std::move(arg);
    return Init_FiducialMapEntry_y(msg_);
  }

private:
  ::fiducials::msg::FiducialMapEntry msg_;
};

class Init_FiducialMapEntry_fiducial_id
{
public:
  Init_FiducialMapEntry_fiducial_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FiducialMapEntry_x fiducial_id(::fiducials::msg::FiducialMapEntry::_fiducial_id_type arg)
  {
    msg_.fiducial_id = std::move(arg);
    return Init_FiducialMapEntry_x(msg_);
  }

private:
  ::fiducials::msg::FiducialMapEntry msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::fiducials::msg::FiducialMapEntry>()
{
  return fiducials::msg::builder::Init_FiducialMapEntry_fiducial_id();
}

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY__BUILDER_HPP_
