// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from diegetic_button_pkg:msg/InputStatusArray.idl
// generated code does not contain a copyright notice
#include "diegetic_button_pkg/msg/detail/input_status_array__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `inputs`
#include "diegetic_button_pkg/msg/detail/input_status__functions.h"

bool
diegetic_button_pkg__msg__InputStatusArray__init(diegetic_button_pkg__msg__InputStatusArray * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    diegetic_button_pkg__msg__InputStatusArray__fini(msg);
    return false;
  }
  // inputs
  if (!diegetic_button_pkg__msg__InputStatus__Sequence__init(&msg->inputs, 0)) {
    diegetic_button_pkg__msg__InputStatusArray__fini(msg);
    return false;
  }
  return true;
}

void
diegetic_button_pkg__msg__InputStatusArray__fini(diegetic_button_pkg__msg__InputStatusArray * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // inputs
  diegetic_button_pkg__msg__InputStatus__Sequence__fini(&msg->inputs);
}

bool
diegetic_button_pkg__msg__InputStatusArray__are_equal(const diegetic_button_pkg__msg__InputStatusArray * lhs, const diegetic_button_pkg__msg__InputStatusArray * rhs)
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
  // inputs
  if (!diegetic_button_pkg__msg__InputStatus__Sequence__are_equal(
      &(lhs->inputs), &(rhs->inputs)))
  {
    return false;
  }
  return true;
}

bool
diegetic_button_pkg__msg__InputStatusArray__copy(
  const diegetic_button_pkg__msg__InputStatusArray * input,
  diegetic_button_pkg__msg__InputStatusArray * output)
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
  // inputs
  if (!diegetic_button_pkg__msg__InputStatus__Sequence__copy(
      &(input->inputs), &(output->inputs)))
  {
    return false;
  }
  return true;
}

diegetic_button_pkg__msg__InputStatusArray *
diegetic_button_pkg__msg__InputStatusArray__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  diegetic_button_pkg__msg__InputStatusArray * msg = (diegetic_button_pkg__msg__InputStatusArray *)allocator.allocate(sizeof(diegetic_button_pkg__msg__InputStatusArray), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(diegetic_button_pkg__msg__InputStatusArray));
  bool success = diegetic_button_pkg__msg__InputStatusArray__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
diegetic_button_pkg__msg__InputStatusArray__destroy(diegetic_button_pkg__msg__InputStatusArray * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    diegetic_button_pkg__msg__InputStatusArray__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
diegetic_button_pkg__msg__InputStatusArray__Sequence__init(diegetic_button_pkg__msg__InputStatusArray__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  diegetic_button_pkg__msg__InputStatusArray * data = NULL;

  if (size) {
    data = (diegetic_button_pkg__msg__InputStatusArray *)allocator.zero_allocate(size, sizeof(diegetic_button_pkg__msg__InputStatusArray), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = diegetic_button_pkg__msg__InputStatusArray__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        diegetic_button_pkg__msg__InputStatusArray__fini(&data[i - 1]);
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
diegetic_button_pkg__msg__InputStatusArray__Sequence__fini(diegetic_button_pkg__msg__InputStatusArray__Sequence * array)
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
      diegetic_button_pkg__msg__InputStatusArray__fini(&array->data[i]);
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

diegetic_button_pkg__msg__InputStatusArray__Sequence *
diegetic_button_pkg__msg__InputStatusArray__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  diegetic_button_pkg__msg__InputStatusArray__Sequence * array = (diegetic_button_pkg__msg__InputStatusArray__Sequence *)allocator.allocate(sizeof(diegetic_button_pkg__msg__InputStatusArray__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = diegetic_button_pkg__msg__InputStatusArray__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
diegetic_button_pkg__msg__InputStatusArray__Sequence__destroy(diegetic_button_pkg__msg__InputStatusArray__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    diegetic_button_pkg__msg__InputStatusArray__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
diegetic_button_pkg__msg__InputStatusArray__Sequence__are_equal(const diegetic_button_pkg__msg__InputStatusArray__Sequence * lhs, const diegetic_button_pkg__msg__InputStatusArray__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!diegetic_button_pkg__msg__InputStatusArray__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
diegetic_button_pkg__msg__InputStatusArray__Sequence__copy(
  const diegetic_button_pkg__msg__InputStatusArray__Sequence * input,
  diegetic_button_pkg__msg__InputStatusArray__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(diegetic_button_pkg__msg__InputStatusArray);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    diegetic_button_pkg__msg__InputStatusArray * data =
      (diegetic_button_pkg__msg__InputStatusArray *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!diegetic_button_pkg__msg__InputStatusArray__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          diegetic_button_pkg__msg__InputStatusArray__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!diegetic_button_pkg__msg__InputStatusArray__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
