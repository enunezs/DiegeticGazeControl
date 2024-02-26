// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from fiducials:msg/Fiducial.idl
// generated code does not contain a copyright notice
#include "fiducials/msg/detail/fiducial__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
fiducials__msg__Fiducial__init(fiducials__msg__Fiducial * msg)
{
  if (!msg) {
    return false;
  }
  // fiducial_id
  // direction
  // x0
  // y0
  // x1
  // y1
  // x2
  // y2
  // x3
  // y3
  return true;
}

void
fiducials__msg__Fiducial__fini(fiducials__msg__Fiducial * msg)
{
  if (!msg) {
    return;
  }
  // fiducial_id
  // direction
  // x0
  // y0
  // x1
  // y1
  // x2
  // y2
  // x3
  // y3
}

bool
fiducials__msg__Fiducial__are_equal(const fiducials__msg__Fiducial * lhs, const fiducials__msg__Fiducial * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // fiducial_id
  if (lhs->fiducial_id != rhs->fiducial_id) {
    return false;
  }
  // direction
  if (lhs->direction != rhs->direction) {
    return false;
  }
  // x0
  if (lhs->x0 != rhs->x0) {
    return false;
  }
  // y0
  if (lhs->y0 != rhs->y0) {
    return false;
  }
  // x1
  if (lhs->x1 != rhs->x1) {
    return false;
  }
  // y1
  if (lhs->y1 != rhs->y1) {
    return false;
  }
  // x2
  if (lhs->x2 != rhs->x2) {
    return false;
  }
  // y2
  if (lhs->y2 != rhs->y2) {
    return false;
  }
  // x3
  if (lhs->x3 != rhs->x3) {
    return false;
  }
  // y3
  if (lhs->y3 != rhs->y3) {
    return false;
  }
  return true;
}

bool
fiducials__msg__Fiducial__copy(
  const fiducials__msg__Fiducial * input,
  fiducials__msg__Fiducial * output)
{
  if (!input || !output) {
    return false;
  }
  // fiducial_id
  output->fiducial_id = input->fiducial_id;
  // direction
  output->direction = input->direction;
  // x0
  output->x0 = input->x0;
  // y0
  output->y0 = input->y0;
  // x1
  output->x1 = input->x1;
  // y1
  output->y1 = input->y1;
  // x2
  output->x2 = input->x2;
  // y2
  output->y2 = input->y2;
  // x3
  output->x3 = input->x3;
  // y3
  output->y3 = input->y3;
  return true;
}

fiducials__msg__Fiducial *
fiducials__msg__Fiducial__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__Fiducial * msg = (fiducials__msg__Fiducial *)allocator.allocate(sizeof(fiducials__msg__Fiducial), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fiducials__msg__Fiducial));
  bool success = fiducials__msg__Fiducial__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fiducials__msg__Fiducial__destroy(fiducials__msg__Fiducial * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fiducials__msg__Fiducial__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fiducials__msg__Fiducial__Sequence__init(fiducials__msg__Fiducial__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__Fiducial * data = NULL;

  if (size) {
    data = (fiducials__msg__Fiducial *)allocator.zero_allocate(size, sizeof(fiducials__msg__Fiducial), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fiducials__msg__Fiducial__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fiducials__msg__Fiducial__fini(&data[i - 1]);
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
fiducials__msg__Fiducial__Sequence__fini(fiducials__msg__Fiducial__Sequence * array)
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
      fiducials__msg__Fiducial__fini(&array->data[i]);
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

fiducials__msg__Fiducial__Sequence *
fiducials__msg__Fiducial__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__Fiducial__Sequence * array = (fiducials__msg__Fiducial__Sequence *)allocator.allocate(sizeof(fiducials__msg__Fiducial__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fiducials__msg__Fiducial__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fiducials__msg__Fiducial__Sequence__destroy(fiducials__msg__Fiducial__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fiducials__msg__Fiducial__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fiducials__msg__Fiducial__Sequence__are_equal(const fiducials__msg__Fiducial__Sequence * lhs, const fiducials__msg__Fiducial__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fiducials__msg__Fiducial__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fiducials__msg__Fiducial__Sequence__copy(
  const fiducials__msg__Fiducial__Sequence * input,
  fiducials__msg__Fiducial__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fiducials__msg__Fiducial);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fiducials__msg__Fiducial * data =
      (fiducials__msg__Fiducial *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fiducials__msg__Fiducial__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fiducials__msg__Fiducial__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fiducials__msg__Fiducial__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
