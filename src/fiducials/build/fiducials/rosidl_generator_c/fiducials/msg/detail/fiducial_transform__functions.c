// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from fiducials:msg/FiducialTransform.idl
// generated code does not contain a copyright notice
#include "fiducials/msg/detail/fiducial_transform__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `transform`
#include "geometry_msgs/msg/detail/transform__functions.h"

bool
fiducials__msg__FiducialTransform__init(fiducials__msg__FiducialTransform * msg)
{
  if (!msg) {
    return false;
  }
  // fiducial_id
  // transform
  if (!geometry_msgs__msg__Transform__init(&msg->transform)) {
    fiducials__msg__FiducialTransform__fini(msg);
    return false;
  }
  // image_error
  // object_error
  // fiducial_area
  return true;
}

void
fiducials__msg__FiducialTransform__fini(fiducials__msg__FiducialTransform * msg)
{
  if (!msg) {
    return;
  }
  // fiducial_id
  // transform
  geometry_msgs__msg__Transform__fini(&msg->transform);
  // image_error
  // object_error
  // fiducial_area
}

bool
fiducials__msg__FiducialTransform__are_equal(const fiducials__msg__FiducialTransform * lhs, const fiducials__msg__FiducialTransform * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // fiducial_id
  if (lhs->fiducial_id != rhs->fiducial_id) {
    return false;
  }
  // transform
  if (!geometry_msgs__msg__Transform__are_equal(
      &(lhs->transform), &(rhs->transform)))
  {
    return false;
  }
  // image_error
  if (lhs->image_error != rhs->image_error) {
    return false;
  }
  // object_error
  if (lhs->object_error != rhs->object_error) {
    return false;
  }
  // fiducial_area
  if (lhs->fiducial_area != rhs->fiducial_area) {
    return false;
  }
  return true;
}

bool
fiducials__msg__FiducialTransform__copy(
  const fiducials__msg__FiducialTransform * input,
  fiducials__msg__FiducialTransform * output)
{
  if (!input || !output) {
    return false;
  }
  // fiducial_id
  output->fiducial_id = input->fiducial_id;
  // transform
  if (!geometry_msgs__msg__Transform__copy(
      &(input->transform), &(output->transform)))
  {
    return false;
  }
  // image_error
  output->image_error = input->image_error;
  // object_error
  output->object_error = input->object_error;
  // fiducial_area
  output->fiducial_area = input->fiducial_area;
  return true;
}

fiducials__msg__FiducialTransform *
fiducials__msg__FiducialTransform__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__FiducialTransform * msg = (fiducials__msg__FiducialTransform *)allocator.allocate(sizeof(fiducials__msg__FiducialTransform), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fiducials__msg__FiducialTransform));
  bool success = fiducials__msg__FiducialTransform__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fiducials__msg__FiducialTransform__destroy(fiducials__msg__FiducialTransform * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fiducials__msg__FiducialTransform__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fiducials__msg__FiducialTransform__Sequence__init(fiducials__msg__FiducialTransform__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__FiducialTransform * data = NULL;

  if (size) {
    data = (fiducials__msg__FiducialTransform *)allocator.zero_allocate(size, sizeof(fiducials__msg__FiducialTransform), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fiducials__msg__FiducialTransform__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fiducials__msg__FiducialTransform__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
fiducials__msg__FiducialTransform__Sequence__fini(fiducials__msg__FiducialTransform__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      fiducials__msg__FiducialTransform__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

fiducials__msg__FiducialTransform__Sequence *
fiducials__msg__FiducialTransform__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__FiducialTransform__Sequence * array = (fiducials__msg__FiducialTransform__Sequence *)allocator.allocate(sizeof(fiducials__msg__FiducialTransform__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fiducials__msg__FiducialTransform__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fiducials__msg__FiducialTransform__Sequence__destroy(fiducials__msg__FiducialTransform__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fiducials__msg__FiducialTransform__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fiducials__msg__FiducialTransform__Sequence__are_equal(const fiducials__msg__FiducialTransform__Sequence * lhs, const fiducials__msg__FiducialTransform__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fiducials__msg__FiducialTransform__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fiducials__msg__FiducialTransform__Sequence__copy(
  const fiducials__msg__FiducialTransform__Sequence * input,
  fiducials__msg__FiducialTransform__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fiducials__msg__FiducialTransform);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fiducials__msg__FiducialTransform * data =
      (fiducials__msg__FiducialTransform *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fiducials__msg__FiducialTransform__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fiducials__msg__FiducialTransform__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fiducials__msg__FiducialTransform__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
