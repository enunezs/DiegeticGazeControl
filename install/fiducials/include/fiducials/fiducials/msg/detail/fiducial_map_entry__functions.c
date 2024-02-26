// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from fiducials:msg/FiducialMapEntry.idl
// generated code does not contain a copyright notice
#include "fiducials/msg/detail/fiducial_map_entry__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
fiducials__msg__FiducialMapEntry__init(fiducials__msg__FiducialMapEntry * msg)
{
  if (!msg) {
    return false;
  }
  // fiducial_id
  // x
  // y
  // z
  // rx
  // ry
  // rz
  return true;
}

void
fiducials__msg__FiducialMapEntry__fini(fiducials__msg__FiducialMapEntry * msg)
{
  if (!msg) {
    return;
  }
  // fiducial_id
  // x
  // y
  // z
  // rx
  // ry
  // rz
}

bool
fiducials__msg__FiducialMapEntry__are_equal(const fiducials__msg__FiducialMapEntry * lhs, const fiducials__msg__FiducialMapEntry * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // fiducial_id
  if (lhs->fiducial_id != rhs->fiducial_id) {
    return false;
  }
  // x
  if (lhs->x != rhs->x) {
    return false;
  }
  // y
  if (lhs->y != rhs->y) {
    return false;
  }
  // z
  if (lhs->z != rhs->z) {
    return false;
  }
  // rx
  if (lhs->rx != rhs->rx) {
    return false;
  }
  // ry
  if (lhs->ry != rhs->ry) {
    return false;
  }
  // rz
  if (lhs->rz != rhs->rz) {
    return false;
  }
  return true;
}

bool
fiducials__msg__FiducialMapEntry__copy(
  const fiducials__msg__FiducialMapEntry * input,
  fiducials__msg__FiducialMapEntry * output)
{
  if (!input || !output) {
    return false;
  }
  // fiducial_id
  output->fiducial_id = input->fiducial_id;
  // x
  output->x = input->x;
  // y
  output->y = input->y;
  // z
  output->z = input->z;
  // rx
  output->rx = input->rx;
  // ry
  output->ry = input->ry;
  // rz
  output->rz = input->rz;
  return true;
}

fiducials__msg__FiducialMapEntry *
fiducials__msg__FiducialMapEntry__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__FiducialMapEntry * msg = (fiducials__msg__FiducialMapEntry *)allocator.allocate(sizeof(fiducials__msg__FiducialMapEntry), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fiducials__msg__FiducialMapEntry));
  bool success = fiducials__msg__FiducialMapEntry__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fiducials__msg__FiducialMapEntry__destroy(fiducials__msg__FiducialMapEntry * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fiducials__msg__FiducialMapEntry__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fiducials__msg__FiducialMapEntry__Sequence__init(fiducials__msg__FiducialMapEntry__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__FiducialMapEntry * data = NULL;

  if (size) {
    data = (fiducials__msg__FiducialMapEntry *)allocator.zero_allocate(size, sizeof(fiducials__msg__FiducialMapEntry), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fiducials__msg__FiducialMapEntry__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fiducials__msg__FiducialMapEntry__fini(&data[i - 1]);
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
fiducials__msg__FiducialMapEntry__Sequence__fini(fiducials__msg__FiducialMapEntry__Sequence * array)
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
      fiducials__msg__FiducialMapEntry__fini(&array->data[i]);
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

fiducials__msg__FiducialMapEntry__Sequence *
fiducials__msg__FiducialMapEntry__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fiducials__msg__FiducialMapEntry__Sequence * array = (fiducials__msg__FiducialMapEntry__Sequence *)allocator.allocate(sizeof(fiducials__msg__FiducialMapEntry__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fiducials__msg__FiducialMapEntry__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fiducials__msg__FiducialMapEntry__Sequence__destroy(fiducials__msg__FiducialMapEntry__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fiducials__msg__FiducialMapEntry__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fiducials__msg__FiducialMapEntry__Sequence__are_equal(const fiducials__msg__FiducialMapEntry__Sequence * lhs, const fiducials__msg__FiducialMapEntry__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fiducials__msg__FiducialMapEntry__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fiducials__msg__FiducialMapEntry__Sequence__copy(
  const fiducials__msg__FiducialMapEntry__Sequence * input,
  fiducials__msg__FiducialMapEntry__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fiducials__msg__FiducialMapEntry);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fiducials__msg__FiducialMapEntry * data =
      (fiducials__msg__FiducialMapEntry *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fiducials__msg__FiducialMapEntry__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fiducials__msg__FiducialMapEntry__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fiducials__msg__FiducialMapEntry__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
