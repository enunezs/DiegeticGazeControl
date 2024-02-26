// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from fiducials:msg/FiducialMapEntry.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY__STRUCT_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__fiducials__msg__FiducialMapEntry __attribute__((deprecated))
#else
# define DEPRECATED__fiducials__msg__FiducialMapEntry __declspec(deprecated)
#endif

namespace fiducials
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FiducialMapEntry_
{
  using Type = FiducialMapEntry_<ContainerAllocator>;

  explicit FiducialMapEntry_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fiducial_id = 0l;
      this->x = 0.0;
      this->y = 0.0;
      this->z = 0.0;
      this->rx = 0.0;
      this->ry = 0.0;
      this->rz = 0.0;
    }
  }

  explicit FiducialMapEntry_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fiducial_id = 0l;
      this->x = 0.0;
      this->y = 0.0;
      this->z = 0.0;
      this->rx = 0.0;
      this->ry = 0.0;
      this->rz = 0.0;
    }
  }

  // field types and members
  using _fiducial_id_type =
    int32_t;
  _fiducial_id_type fiducial_id;
  using _x_type =
    double;
  _x_type x;
  using _y_type =
    double;
  _y_type y;
  using _z_type =
    double;
  _z_type z;
  using _rx_type =
    double;
  _rx_type rx;
  using _ry_type =
    double;
  _ry_type ry;
  using _rz_type =
    double;
  _rz_type rz;

  // setters for named parameter idiom
  Type & set__fiducial_id(
    const int32_t & _arg)
  {
    this->fiducial_id = _arg;
    return *this;
  }
  Type & set__x(
    const double & _arg)
  {
    this->x = _arg;
    return *this;
  }
  Type & set__y(
    const double & _arg)
  {
    this->y = _arg;
    return *this;
  }
  Type & set__z(
    const double & _arg)
  {
    this->z = _arg;
    return *this;
  }
  Type & set__rx(
    const double & _arg)
  {
    this->rx = _arg;
    return *this;
  }
  Type & set__ry(
    const double & _arg)
  {
    this->ry = _arg;
    return *this;
  }
  Type & set__rz(
    const double & _arg)
  {
    this->rz = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    fiducials::msg::FiducialMapEntry_<ContainerAllocator> *;
  using ConstRawPtr =
    const fiducials::msg::FiducialMapEntry_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<fiducials::msg::FiducialMapEntry_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<fiducials::msg::FiducialMapEntry_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::FiducialMapEntry_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::FiducialMapEntry_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::FiducialMapEntry_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::FiducialMapEntry_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<fiducials::msg::FiducialMapEntry_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<fiducials::msg::FiducialMapEntry_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__fiducials__msg__FiducialMapEntry
    std::shared_ptr<fiducials::msg::FiducialMapEntry_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__fiducials__msg__FiducialMapEntry
    std::shared_ptr<fiducials::msg::FiducialMapEntry_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FiducialMapEntry_ & other) const
  {
    if (this->fiducial_id != other.fiducial_id) {
      return false;
    }
    if (this->x != other.x) {
      return false;
    }
    if (this->y != other.y) {
      return false;
    }
    if (this->z != other.z) {
      return false;
    }
    if (this->rx != other.rx) {
      return false;
    }
    if (this->ry != other.ry) {
      return false;
    }
    if (this->rz != other.rz) {
      return false;
    }
    return true;
  }
  bool operator!=(const FiducialMapEntry_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FiducialMapEntry_

// alias to use template instance with default allocator
using FiducialMapEntry =
  fiducials::msg::FiducialMapEntry_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY__STRUCT_HPP_
