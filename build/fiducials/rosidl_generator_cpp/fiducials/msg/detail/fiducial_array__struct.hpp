// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from fiducials:msg/FiducialArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_ARRAY__STRUCT_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_ARRAY__STRUCT_HPP_

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
// Member 'fiducials'
#include "fiducials/msg/detail/fiducial__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__fiducials__msg__FiducialArray __attribute__((deprecated))
#else
# define DEPRECATED__fiducials__msg__FiducialArray __declspec(deprecated)
#endif

namespace fiducials
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FiducialArray_
{
  using Type = FiducialArray_<ContainerAllocator>;

  explicit FiducialArray_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->image_seq = 0l;
    }
  }

  explicit FiducialArray_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->image_seq = 0l;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _image_seq_type =
    int32_t;
  _image_seq_type image_seq;
  using _fiducials_type =
    std::vector<fiducials::msg::Fiducial_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<fiducials::msg::Fiducial_<ContainerAllocator>>>;
  _fiducials_type fiducials;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__image_seq(
    const int32_t & _arg)
  {
    this->image_seq = _arg;
    return *this;
  }
  Type & set__fiducials(
    const std::vector<fiducials::msg::Fiducial_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<fiducials::msg::Fiducial_<ContainerAllocator>>> & _arg)
  {
    this->fiducials = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    fiducials::msg::FiducialArray_<ContainerAllocator> *;
  using ConstRawPtr =
    const fiducials::msg::FiducialArray_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<fiducials::msg::FiducialArray_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<fiducials::msg::FiducialArray_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::FiducialArray_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::FiducialArray_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::FiducialArray_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::FiducialArray_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<fiducials::msg::FiducialArray_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<fiducials::msg::FiducialArray_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__fiducials__msg__FiducialArray
    std::shared_ptr<fiducials::msg::FiducialArray_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__fiducials__msg__FiducialArray
    std::shared_ptr<fiducials::msg::FiducialArray_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FiducialArray_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->image_seq != other.image_seq) {
      return false;
    }
    if (this->fiducials != other.fiducials) {
      return false;
    }
    return true;
  }
  bool operator!=(const FiducialArray_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FiducialArray_

// alias to use template instance with default allocator
using FiducialArray =
  fiducials::msg::FiducialArray_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_ARRAY__STRUCT_HPP_
