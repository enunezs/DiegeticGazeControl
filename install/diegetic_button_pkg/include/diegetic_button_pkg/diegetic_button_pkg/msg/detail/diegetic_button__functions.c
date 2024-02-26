// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from diegetic_button_pkg:msg/DiegeticButton.idl
// generated code does not contain a copyright notice
#include "diegetic_button_pkg/msg/detail/diegetic_button__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `button_id`
#include "rosidl_runtime_c/string_functions.h"
// Member `button_transform`
#include "geometry_msgs/msg/detail/transform__functions.h"

bool
diegetic_button_pkg__msg__DiegeticButton__init(diegetic_button_pkg__msg__DiegeticButton * msg)
{
  if (!msg) {
    return false;
  }
  // button_id
  if (!rosidl_runtime_c__String__init(&msg->button_id)) {
    diegetic_button_pkg__msg__DiegeticButton__fini(msg);
    return false;
  }
  // button_transform
  if (!geometry_msgs__msg__Transform__init(&msg->button_transform)) {
    diegetic_button_pkg__msg__DiegeticButton__fini(msg);
    return false;
  }
  // x0
  // y0
  // x1
  // y1
  return true;
}

void
diegetic_button_pkg__msg__DiegeticButton__fini(diegetic_button_pkg__msg__DiegeticButton * msg)
{
  if (!msg) {
    return;
  }
  // button_id
  rosidl_runtime_c__String__fini(&msg->button_id);
  // button_transform
  geometry_msgs__msg__Transform__fini(&msg->button_transform);
  // x0
  // y0
  // x1
  // y1
}

bool
diegetic_button_pkg__msg__DiegeticButton__are_equal(const diegetic_button_pkg__msg__DiegeticButton * lhs, const diegetic_button_pkg__msg__DiegeticButton * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // button_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->button_id), &(rhs->button_id)))
  {
    return false;
  }
  // button_transform
  if (!geometry_msgs__msg__Transform__are_equal(
      &(lhs->button_transform), &(rhs->button_transform)))
  {
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
  return true;
}

bool
diegetic_button_pkg__msg__DiegeticButton__copy(
  const diegetic_button_pkg__msg__DiegeticButton * input,
  diegetic_button_pkg__msg__DiegeticButton * output)
{
  if (!input || !output) {
    return false;
  }
  // button_id
  if (!rosidl_runtime_c__String__copy(
      &(input->button_id), &(output->button_id)))
  {
    return false;
  }
  // button_transform
  if (!geometry_msgs__msg__Transform__copy(
      &(input->button_transform), &(output->button_transform)))
  {
    return false;
  }
  // x0
  output->x0 = input->x0;
  // y0
  output->y0 = input->y0;
  // x1
  output->x1 = input->x1;
  // y1
  output->y1 = input->y1;
  return true;
}

diegetic_button_pkg__msg__DiegeticButton *
diegetic_button_pkg__msg__DiegeticButton__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  diegetic_button_pkg__msg__DiegeticButton * msg = (diegetic_button_pkg__msg__DiegeticButton *)allocator.allocate(sizeof(diegetic_button_pkg__msg__DiegeticButton), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(diegetic_button_pkg__msg__DiegeticButton));
  bool success = diegetic_button_pkg__msg__DiegeticButton__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
diegetic_button_pkg__msg__DiegeticButton__destroy(diegetic_button_pkg__msg__DiegeticButton * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    diegetic_button_pkg__msg__DiegeticButton__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
diegetic_button_pkg__msg__DiegeticButton__Sequence__init(diegetic_button_pkg__msg__DiegeticButton__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  diegetic_button_pkg__msg__DiegeticButton * data = NULL;

  if (size) {
    data = (diegetic_button_pkg__msg__DiegeticButton *)allocator.zero_allocate(size, sizeof(diegetic_button_pkg__msg__DiegeticButton), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = diegetic_button_pkg__msg__DiegeticButton__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        diegetic_button_pkg__msg__DiegeticButton__fini(&data[i - 1]);
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
diegetic_button_pkg__msg__DiegeticButton__Sequence__fini(diegetic_button_pkg__msg__DiegeticButton__Sequence * array)
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
      diegetic_button_pkg__msg__DiegeticButton__fini(&array->data[i]);
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

diegetic_button_pkg__msg__DiegeticButton__Sequence *
diegetic_button_pkg__msg__DiegeticButton__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  diegetic_button_pkg__msg__DiegeticButton__Sequence * array = (diegetic_button_pkg__msg__DiegeticButton__Sequence *)allocator.allocate(sizeof(diegetic_button_pkg__msg__DiegeticButton__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = diegetic_button_pkg__msg__DiegeticButton__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
diegetic_button_pkg__msg__DiegeticButton__Sequence__destroy(diegetic_button_pkg__msg__DiegeticButton__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    diegetic_button_pkg__msg__DiegeticButton__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
diegetic_button_pkg__msg__DiegeticButton__Sequence__are_equal(const diegetic_button_pkg__msg__DiegeticButton__Sequence * lhs, const diegetic_button_pkg__msg__DiegeticButton__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!diegetic_button_pkg__msg__DiegeticButton__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
diegetic_button_pkg__msg__DiegeticButton__Sequence__copy(
  const diegetic_button_pkg__msg__DiegeticButton__Sequence * input,
  diegetic_button_pkg__msg__DiegeticButton__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(diegetic_button_pkg__msg__DiegeticButton);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    diegetic_button_pkg__msg__DiegeticButton * data =
      (diegetic_button_pkg__msg__DiegeticButton *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!diegetic_button_pkg__msg__DiegeticButton__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          diegetic_button_pkg__msg__DiegeticButton__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!diegetic_button_pkg__msg__DiegeticButton__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
