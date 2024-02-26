// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from fiducials:msg/Fiducial.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL__STRUCT_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__fiducials__msg__Fiducial __attribute__((deprecated))
#else
# define DEPRECATED__fiducials__msg__Fiducial __declspec(deprecated)
#endif

namespace fiducials
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Fiducial_
{
  using Type = Fiducial_<ContainerAllocator>;

  explicit Fiducial_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fiducial_id = 0l;
      this->direction = 0l;
      this->x0 = 0.0;
      this->y0 = 0.0;
      this->x1 = 0.0;
      this->y1 = 0.0;
      this->x2 = 0.0;
      this->y2 = 0.0;
      this->x3 = 0.0;
      this->y3 = 0.0;
    }
  }

  explicit Fiducial_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fiducial_id = 0l;
      this->direction = 0l;
      this->x0 = 0.0;
      this->y0 = 0.0;
      this->x1 = 0.0;
      this->y1 = 0.0;
      this->x2 = 0.0;
      this->y2 = 0.0;
      this->x3 = 0.0;
      this->y3 = 0.0;
    }
  }

  // field types and members
  using _fiducial_id_type =
    int32_t;
  _fiducial_id_type fiducial_id;
  using _direction_type =
    int32_t;
  _direction_type direction;
  using _x0_type =
    double;
  _x0_type x0;
  using _y0_type =
    double;
  _y0_type y0;
  using _x1_type =
    double;
  _x1_type x1;
  using _y1_type =
    double;
  _y1_type y1;
  using _x2_type =
    double;
  _x2_type x2;
  using _y2_type =
    double;
  _y2_type y2;
  using _x3_type =
    double;
  _x3_type x3;
  using _y3_type =
    double;
  _y3_type y3;

  // setters for named parameter idiom
  Type & set__fiducial_id(
    const int32_t & _arg)
  {
    this->fiducial_id = _arg;
    return *this;
  }
  Type & set__direction(
    const int32_t & _arg)
  {
    this->direction = _arg;
    return *this;
  }
  Type & set__x0(
    const double & _arg)
  {
    this->x0 = _arg;
    return *this;
  }
  Type & set__y0(
    const double & _arg)
  {
    this->y0 = _arg;
    return *this;
  }
  Type & set__x1(
    const double & _arg)
  {
    this->x1 = _arg;
    return *this;
  }
  Type & set__y1(
    const double & _arg)
  {
    this->y1 = _arg;
    return *this;
  }
  Type & set__x2(
    const double & _arg)
  {
    this->x2 = _arg;
    return *this;
  }
  Type & set__y2(
    const double & _arg)
  {
    this->y2 = _arg;
    return *this;
  }
  Type & set__x3(
    const double & _arg)
  {
    this->x3 = _arg;
    return *this;
  }
  Type & set__y3(
    const double & _arg)
  {
    this->y3 = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    fiducials::msg::Fiducial_<ContainerAllocator> *;
  using ConstRawPtr =
    const fiducials::msg::Fiducial_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<fiducials::msg::Fiducial_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<fiducials::msg::Fiducial_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::Fiducial_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::Fiducial_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::Fiducial_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::Fiducial_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<fiducials::msg::Fiducial_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<fiducials::msg::Fiducial_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__fiducials__msg__Fiducial
    std::shared_ptr<fiducials::msg::Fiducial_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__fiducials__msg__Fiducial
    std::shared_ptr<fiducials::msg::Fiducial_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Fiducial_ & other) const
  {
    if (this->fiducial_id != other.fiducial_id) {
      return false;
    }
    if (this->direction != other.direction) {
      return false;
    }
    if (this->x0 != other.x0) {
      return false;
    }
    if (this->y0 != other.y0) {
      return false;
    }
    if (this->x1 != other.x1) {
      return false;
    }
    if (this->y1 != other.y1) {
      return false;
    }
    if (this->x2 != other.x2) {
      return false;
    }
    if (this->y2 != other.y2) {
      return false;
    }
    if (this->x3 != other.x3) {
      return false;
    }
    if (this->y3 != other.y3) {
      return false;
    }
    return true;
  }
  bool operator!=(const Fiducial_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Fiducial_

// alias to use template instance with default allocator
using Fiducial =
  fiducials::msg::Fiducial_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL__STRUCT_HPP_
