// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from diegetic_button_pkg:msg/InputStatus.idl
// generated code does not contain a copyright notice
#include "diegetic_button_pkg/msg/detail/input_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `input_id`
// Member `status`
#include "rosidl_runtime_c/string_functions.h"

bool
diegetic_button_pkg__msg__InputStatus__init(diegetic_button_pkg__msg__InputStatus * msg)
{
  if (!msg) {
    return false;
  }
  // input_id
  if (!rosidl_runtime_c__String__init(&msg->input_id)) {
    diegetic_button_pkg__msg__InputStatus__fini(msg);
    return false;
  }
  // status
  if (!rosidl_runtime_c__String__init(&msg->status)) {
    diegetic_button_pkg__msg__InputStatus__fini(msg);
    return false;
  }
  // percent
  return true;
}

void
diegetic_button_pkg__msg__InputStatus__fini(diegetic_button_pkg__msg__InputStatus * msg)
{
  if (!msg) {
    return;
  }
  // input_id
  rosidl_runtime_c__String__fini(&msg->input_id);
  // status
  rosidl_runtime_c__String__fini(&msg->status);
  // percent
}

bool
diegetic_button_pkg__msg__InputStatus__are_equal(const diegetic_button_pkg__msg__InputStatus * lhs, const diegetic_button_pkg__msg__InputStatus * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // input_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->input_id), &(rhs->input_id)))
  {
    return false;
  }
  // status
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->status), &(rhs->status)))
  {
    return false;
  }
  // percent
  if (lhs->percent != rhs->percent) {
    return false;
  }
  return true;
}

bool
diegetic_button_pkg__msg__InputStatus__copy(
  const diegetic_button_pkg__msg__InputStatus * input,
  diegetic_button_pkg__msg__InputStatus * output)
{
  if (!input || !output) {
    return false;
  }
  // input_id
  if (!rosidl_runtime_c__String__copy(
      &(input->input_id), &(output->input_id)))
  {
    return false;
  }
  // status
  if (!rosidl_runtime_c__String__copy(
      &(input->status), &(output->status)))
  {
    return false;
  }
  // percent
  output->percent = input->percent;
  return true;
}

diegetic_button_pkg__msg__InputStatus *
diegetic_button_pkg__msg__InputStatus__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  diegetic_button_pkg__msg__InputStatus * msg = (diegetic_button_pkg__msg__InputStatus *)allocator.allocate(sizeof(diegetic_button_pkg__msg__InputStatus), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(diegetic_button_pkg__msg__InputStatus));
  bool success = diegetic_button_pkg__msg__InputStatus__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
diegetic_button_pkg__msg__InputStatus__destroy(diegetic_button_pkg__msg__InputStatus * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    diegetic_button_pkg__msg__InputStatus__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
diegetic_button_pkg__msg__InputStatus__Sequence__init(diegetic_button_pkg__msg__InputStatus__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  diegetic_button_pkg__msg__InputStatus * data = NULL;

  if (size) {
    data = (diegetic_button_pkg__msg__InputStatus *)allocator.zero_allocate(size, sizeof(diegetic_button_pkg__msg__InputStatus), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = diegetic_button_pkg__msg__InputStatus__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        diegetic_button_pkg__msg__InputStatus__fini(&data[i - 1]);
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
diegetic_button_pkg__msg__InputStatus__Sequence__fini(diegetic_button_pkg__msg__InputStatus__Sequence * array)
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
      diegetic_button_pkg__msg__InputStatus__fini(&array->data[i]);
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

diegetic_button_pkg__msg__InputStatus__Sequence *
diegetic_button_pkg__msg__InputStatus__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  diegetic_button_pkg__msg__InputStatus__Sequence * array = (diegetic_button_pkg__msg__InputStatus__Sequence *)allocator.allocate(sizeof(diegetic_button_pkg__msg__InputStatus__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = diegetic_button_pkg__msg__InputStatus__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
diegetic_button_pkg__msg__InputStatus__Sequence__destroy(diegetic_button_pkg__msg__InputStatus__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    diegetic_button_pkg__msg__InputStatus__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
diegetic_button_pkg__msg__InputStatus__Sequence__are_equal(const diegetic_button_pkg__msg__InputStatus__Sequence * lhs, const diegetic_button_pkg__msg__InputStatus__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!diegetic_button_pkg__msg__InputStatus__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
diegetic_button_pkg__msg__InputStatus__Sequence__copy(
  const diegetic_button_pkg__msg__InputStatus__Sequence * input,
  diegetic_button_pkg__msg__InputStatus__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(diegetic_button_pkg__msg__InputStatus);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    diegetic_button_pkg__msg__InputStatus * data =
      (diegetic_button_pkg__msg__InputStatus *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!diegetic_button_pkg__msg__InputStatus__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          diegetic_button_pkg__msg__InputStatus__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!diegetic_button_pkg__msg__InputStatus__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
