// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from fiducials:msg/FiducialTransform.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__STRUCT_HPP_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'transform'
#include "geometry_msgs/msg/detail/transform__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__fiducials__msg__FiducialTransform __attribute__((deprecated))
#else
# define DEPRECATED__fiducials__msg__FiducialTransform __declspec(deprecated)
#endif

namespace fiducials
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FiducialTransform_
{
  using Type = FiducialTransform_<ContainerAllocator>;

  explicit FiducialTransform_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : transform(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fiducial_id = 0l;
      this->image_error = 0.0;
      this->object_error = 0.0;
      this->fiducial_area = 0.0;
    }
  }

  explicit FiducialTransform_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : transform(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fiducial_id = 0l;
      this->image_error = 0.0;
      this->object_error = 0.0;
      this->fiducial_area = 0.0;
    }
  }

  // field types and members
  using _fiducial_id_type =
    int32_t;
  _fiducial_id_type fiducial_id;
  using _transform_type =
    geometry_msgs::msg::Transform_<ContainerAllocator>;
  _transform_type transform;
  using _image_error_type =
    double;
  _image_error_type image_error;
  using _object_error_type =
    double;
  _object_error_type object_error;
  using _fiducial_area_type =
    double;
  _fiducial_area_type fiducial_area;

  // setters for named parameter idiom
  Type & set__fiducial_id(
    const int32_t & _arg)
  {
    this->fiducial_id = _arg;
    return *this;
  }
  Type & set__transform(
    const geometry_msgs::msg::Transform_<ContainerAllocator> & _arg)
  {
    this->transform = _arg;
    return *this;
  }
  Type & set__image_error(
    const double & _arg)
  {
    this->image_error = _arg;
    return *this;
  }
  Type & set__object_error(
    const double & _arg)
  {
    this->object_error = _arg;
    return *this;
  }
  Type & set__fiducial_area(
    const double & _arg)
  {
    this->fiducial_area = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    fiducials::msg::FiducialTransform_<ContainerAllocator> *;
  using ConstRawPtr =
    const fiducials::msg::FiducialTransform_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<fiducials::msg::FiducialTransform_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<fiducials::msg::FiducialTransform_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::FiducialTransform_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::FiducialTransform_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      fiducials::msg::FiducialTransform_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<fiducials::msg::FiducialTransform_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<fiducials::msg::FiducialTransform_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<fiducials::msg::FiducialTransform_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__fiducials__msg__FiducialTransform
    std::shared_ptr<fiducials::msg::FiducialTransform_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__fiducials__msg__FiducialTransform
    std::shared_ptr<fiducials::msg::FiducialTransform_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FiducialTransform_ & other) const
  {
    if (this->fiducial_id != other.fiducial_id) {
      return false;
    }
    if (this->transform != other.transform) {
      return false;
    }
    if (this->image_error != other.image_error) {
      return false;
    }
    if (this->object_error != other.object_error) {
      return false;
    }
    if (this->fiducial_area != other.fiducial_area) {
      return false;
    }
    return true;
  }
  bool operator!=(const FiducialTransform_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FiducialTransform_

// alias to use template instance with default allocator
using FiducialTransform =
  fiducials::msg::FiducialTransform_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace fiducials

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__STRUCT_HPP_
