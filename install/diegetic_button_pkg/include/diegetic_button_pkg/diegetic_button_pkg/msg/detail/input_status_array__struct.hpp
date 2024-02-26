// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from diegetic_button_pkg:msg/InputStatusArray.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__STRUCT_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__STRUCT_HPP_

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
// Member 'inputs'
#include "diegetic_button_pkg/msg/detail/input_status__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__diegetic_button_pkg__msg__InputStatusArray __attribute__((deprecated))
#else
# define DEPRECATED__diegetic_button_pkg__msg__InputStatusArray __declspec(deprecated)
#endif

namespace diegetic_button_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct InputStatusArray_
{
  using Type = InputStatusArray_<ContainerAllocator>;

  explicit InputStatusArray_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    (void)_init;
  }

  explicit InputStatusArray_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _inputs_type =
    std::vector<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>>>;
  _inputs_type inputs;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__inputs(
    const std::vector<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>>> & _arg)
  {
    this->inputs = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator> *;
  using ConstRawPtr =
    const diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__diegetic_button_pkg__msg__InputStatusArray
    std::shared_ptr<diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__diegetic_button_pkg__msg__InputStatusArray
    std::shared_ptr<diegetic_button_pkg::msg::InputStatusArray_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const InputStatusArray_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->inputs != other.inputs) {
      return false;
    }
    return true;
  }
  bool operator!=(const InputStatusArray_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct InputStatusArray_

// alias to use template instance with default allocator
using InputStatusArray =
  diegetic_button_pkg::msg::InputStatusArray_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace diegetic_button_pkg

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS_ARRAY__STRUCT_HPP_
