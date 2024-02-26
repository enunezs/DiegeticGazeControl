// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from diegetic_button_pkg:msg/DiegeticButtonArray.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__STRUCT_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"
// Member 'buttons'
#include "diegetic_button_pkg/msg/detail/diegetic_button__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__diegetic_button_pkg__msg__DiegeticButtonArray __attribute__((deprecated))
#else
# define DEPRECATED__diegetic_button_pkg__msg__DiegeticButtonArray __declspec(deprecated)
#endif

namespace diegetic_button_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct DiegeticButtonArray_
{
  using Type = DiegeticButtonArray_<ContainerAllocator>;

  explicit DiegeticButtonArray_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    (void)_init;
  }

  explicit DiegeticButtonArray_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _buttons_type =
    std::vector<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>>>;
  _buttons_type buttons;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__buttons(
    const std::vector<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<diegetic_button_pkg::msg::DiegeticButton_<ContainerAllocator>>> & _arg)
  {
    this->buttons = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator> *;
  using ConstRawPtr =
    const diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__diegetic_button_pkg__msg__DiegeticButtonArray
    std::shared_ptr<diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__diegetic_button_pkg__msg__DiegeticButtonArray
    std::shared_ptr<diegetic_button_pkg::msg::DiegeticButtonArray_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DiegeticButtonArray_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->buttons != other.buttons) {
      return false;
    }
    return true;
  }
  bool operator!=(const DiegeticButtonArray_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DiegeticButtonArray_

// alias to use template instance with default allocator
using DiegeticButtonArray =
  diegetic_button_pkg::msg::DiegeticButtonArray_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace diegetic_button_pkg

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__STRUCT_HPP_
