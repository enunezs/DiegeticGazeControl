// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from fiducials:msg/FiducialMapEntryArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__STRUCT_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'fiducials'
#include "fiducials/msg/detail/fiducial_map_entry__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__fiducials__msg__FiducialMapEntryArray __attribute__((deprecated))
#else
# define DEPRECATED__fiducials__msg__FiducialMapEntryArray __declspec(deprecated)
#endif

namespace fiducials
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FiducialMapEntryArray_
{
  using Type = FiducialMapEntryArray_<ContainerAllocator>;

  explicit FiducialMapEntryArray_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
  }

  explicit FiducialMapEntryArray_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
    (void)_alloc;
  }

  // field types and members
  using _fiducials_type =
    std::vector<fiducials::msg::FiducialMapEntry_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<fiducials::msg::FiducialMapEntry_<ContainerAllocator>>>;
  _fiducials_type fiducials;

  // setters for named parameter idiom
  Type & set__fiducials(
    const std::vector<fiducials::msg::FiducialMapEntry_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<fiducials::msg::FiducialMapEntry_<ContainerAllocator>>> & _arg)
  {
    this->fiducials = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    fiducials::msg::FiducialMapEntryArray_<ContainerAllocator> *;
  using ConstRawPtr =
    const fiducials::msg::FiducialMapEntryArray_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<fiducials::msg::FiducialMapEntryArray_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<fiducials::msg::FiducialMapEntryArray_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::FiducialMapEntryArray_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::FiducialMapEntryArray_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::FiducialMapEntryArray_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::FiducialMapEntryArray_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<fiducials::msg::FiducialMapEntryArray_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<fiducials::msg::FiducialMapEntryArray_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__fiducials__msg__FiducialMapEntryArray
    std::shared_ptr<fiducials::msg::FiducialMapEntryArray_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__fiducials__msg__FiducialMapEntryArray
    std::shared_ptr<fiducials::msg::FiducialMapEntryArray_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FiducialMapEntryArray_ & other) const
  {
    if (this->fiducials != other.fiducials) {
      return false;
    }
    return true;
  }
  bool operator!=(const FiducialMapEntryArray_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FiducialMapEntryArray_

// alias to use template instance with default allocator
using FiducialMapEntryArray =
  fiducials::msg::FiducialMapEntryArray_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__STRUCT_HPP_
