// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from fiducials:msg/FiducialArray.idl
// generated code does not contain a copyright notice
#include "fiducials/msg/detail/fiducial_array__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `fiducials`
#include "fiducials/msg/detail/fiducial__functions.h"

bool
fiducials__msg__FiducialArray__init(fiducials__msg__FiducialArray * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    fiducials__msg__FiducialArray__fini(msg);
    return false;
  }
  // image_seq
  // fiducials
  if (!fiducials__msg__Fiducial__Sequence__init(&msg->fiducials, 0)) {
    fiducials__msg__FiducialArray__fini(msg);
    return false;
  }
  return true;
}

void
fiducials__msg__FiducialArray__fini(fiducials__msg__FiducialArray * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // image_seq
  // fiducials
  fiducials__msg__Fiducial__Sequence__fini(&msg->fiducials);
}

bool
fiducials__msg__FiducialArray__are_equal(const fiducials__msg__FiducialArray * lhs, const fiducials__msg__FiducialArray * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // image_seq
  if (lhs->image_seq != rhs->image_seq) {
    return false;
  }
  // fiducials
  if (!fiducials__msg__Fiducial__Sequence__are_equal(
      &(lhs->fiducials), &(rhs->fiducials)))
  {
    return false;
  }
  return true;
}

bool
fiducials__msg__FiducialArray__copy(
  const fiducials__msg__FiducialArray * input,
  fiducials__msg__FiducialArray * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // image_seq
  output->image_seq = input->image_seq;
  // fiducials
  if (!fiducials__msg__Fiducial__Sequence__copy(
      &(input->fiducials), &(output->fiducials)))
  {
    return false;
  }
  return true;
}

fiducials__msg__FiducialArray *
fiducials__msg__FiducialArray__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__FiducialArray * msg = (fiducials__msg__FiducialArray *)allocator.allocate(sizeof(fiducials__msg__FiducialArray), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fiducials__msg__FiducialArray));
  bool success = fiducials__msg__FiducialArray__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fiducials__msg__FiducialArray__destroy(fiducials__msg__FiducialArray * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fiducials__msg__FiducialArray__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fiducials__msg__FiducialArray__Sequence__init(fiducials__msg__FiducialArray__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__FiducialArray * data = NULL;

  if (size) {
    data = (fiducials__msg__FiducialArray *)allocator.zero_allocate(size, sizeof(fiducials__msg__FiducialArray), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fiducials__msg__FiducialArray__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fiducials__msg__FiducialArray__fini(&data[i - 1]);
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
fiducials__msg__FiducialArray__Sequence__fini(fiducials__msg__FiducialArray__Sequence * array)
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
      fiducials__msg__FiducialArray__fini(&array->data[i]);
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

fiducials__msg__FiducialArray__Sequence *
fiducials__msg__FiducialArray__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__FiducialArray__Sequence * array = (fiducials__msg__FiducialArray__Sequence *)allocator.allocate(sizeof(fiducials__msg__FiducialArray__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fiducials__msg__FiducialArray__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fiducials__msg__FiducialArray__Sequence__destroy(fiducials__msg__FiducialArray__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fiducials__msg__FiducialArray__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fiducials__msg__FiducialArray__Sequence__are_equal(const fiducials__msg__FiducialArray__Sequence * lhs, const fiducials__msg__FiducialArray__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fiducials__msg__FiducialArray__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fiducials__msg__FiducialArray__Sequence__copy(
  const fiducials__msg__FiducialArray__Sequence * input,
  fiducials__msg__FiducialArray__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fiducials__msg__FiducialArray);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fiducials__msg__FiducialArray * data =
      (fiducials__msg__FiducialArray *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fiducials__msg__FiducialArray__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fiducials__msg__FiducialArray__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fiducials__msg__FiducialArray__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
