// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from diegetic_button_pkg:msg/InputStatus.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__STRUCT_HPP_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__diegetic_button_pkg__msg__InputStatus __attribute__((deprecated))
#else
# define DEPRECATED__diegetic_button_pkg__msg__InputStatus __declspec(deprecated)
#endif

namespace diegetic_button_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct InputStatus_
{
  using Type = InputStatus_<ContainerAllocator>;

  explicit InputStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->input_id = "";
      this->status = "";
      this->percent = 0.0;
    }
  }

  explicit InputStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : input_id(_alloc),
    status(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->input_id = "";
      this->status = "";
      this->percent = 0.0;
    }
  }

  // field types and members
  using _input_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _input_id_type input_id;
  using _status_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _status_type status;
  using _percent_type =
    double;
  _percent_type percent;

  // setters for named parameter idiom
  Type & set__input_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->input_id = _arg;
    return *this;
  }
  Type & set__status(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->status = _arg;
    return *this;
  }
  Type & set__percent(
    const double & _arg)
  {
    this->percent = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    diegetic_button_pkg::msg::InputStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const diegetic_button_pkg::msg::InputStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__diegetic_button_pkg__msg__InputStatus
    std::shared_ptr<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__diegetic_button_pkg__msg__InputStatus
    std::shared_ptr<diegetic_button_pkg::msg::InputStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const InputStatus_ & other) const
  {
    if (this->input_id != other.input_id) {
      return false;
    }
    if (this->status != other.status) {
      return false;
    }
    if (this->percent != other.percent) {
      return false;
    }
    return true;
  }
  bool operator!=(const InputStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct InputStatus_

// alias to use template instance with default allocator
using InputStatus =
  diegetic_button_pkg::msg::InputStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace diegetic_button_pkg

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__INPUT_STATUS__STRUCT_HPP_
