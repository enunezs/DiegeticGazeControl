// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from diegetic_button_pkg:msg/DiegeticButton.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__STRUCT_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'button_transform'
#include "geometry_msgs/msg/detail/transform__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__diegetic_button_pkg__msg__DiegeticButton __attribute__((deprecated))
#else
# define DEPRECATED__diegetic_button_pkg__msg__DiegeticButton __declspec(deprecated)
#endif

namespace diegetic_button_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct DiegeticButton_
{
  using Type = DiegeticButton_<ContainerAllocator>;

  explicit DiegeticButton_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : button_transform(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->button_id = "";
      this->x0 = 0.0;
      this->y0 = 0.0;
      this->x1 = 0.0;
      this->y1 = 0.0;
    }
  }

  explicit DiegeticButton_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : button_id(_alloc),
    button_transform(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->button_id = "";
      this->x0 = 0.0;
      this->y0 = 0.0;
      this->x1 = 0.0;
      this->y1 = 0.0;
    }
  }

  // field types and members
  using _button_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _button_id_type button_id;
  using _button_transform_type =
    geometry_msgs::msg::Transform_<ContainerAllocator>;
  _button_transform_type button_transform;
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

  // setters for named parameter idiom
  Type & set__button_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->button_id = _arg;
    return *this;
  }
  Type & set__button_transform(
    const geometry_msgs::msg::Transform_<ContainerAllocator> & _arg)
  {
    this->button_transform = _arg;
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

  // constant declarations

  // pointer types
  using RawPtr =
    diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator> *;
  using ConstRawPtr =
    const diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__diegetic_button_pkg__msg__DiegeticButton
    std::shared_ptr<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__diegetic_button_pkg__msg__DiegeticButton
    std::shared_ptr<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DiegeticButton_ & other) const
  {
    if (this->button_id != other.button_id) {
      return false;
    }
    if (this->button_transform != other.button_transform) {
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
    return true;
  }
  bool operator!=(const DiegeticButton_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DiegeticButton_

// alias to use template instance with default allocator
using DiegeticButton =
  diegetic_button_pkg::msg::DiegeticButton_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace diegetic_button_pkg

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON__STRUCT_HPP_
