// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from diegetic_button_pkg:msg/DiegeticButtonArray.idl
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__FUNCTIONS_H_
#define DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "diegetic_button_pkg/msg/rosidl_generator_c__visibility_control.h"

#include "diegetic_button_pkg/msg/detail/diegetic_button_array__struct.h"

/// Initialize msg/DiegeticButtonArray message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * diegetic_button_pkg__msg__DiegeticButtonArray
 * )) before or use
 * diegetic_button_pkg__msg__DiegeticButtonArray__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
bool
diegetic_button_pkg__msg__DiegeticButtonArray__init(diegetic_button_pkg__msg__DiegeticButtonArray * msg);

/// Finalize msg/DiegeticButtonArray message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
void
diegetic_button_pkg__msg__DiegeticButtonArray__fini(diegetic_button_pkg__msg__DiegeticButtonArray * msg);

/// Create msg/DiegeticButtonArray message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * diegetic_button_pkg__msg__DiegeticButtonArray__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
diegetic_button_pkg__msg__DiegeticButtonArray *
diegetic_button_pkg__msg__DiegeticButtonArray__create();

/// Destroy msg/DiegeticButtonArray message.
/**
 * It calls
 * diegetic_button_pkg__msg__DiegeticButtonArray__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
void
diegetic_button_pkg__msg__DiegeticButtonArray__destroy(diegetic_button_pkg__msg__DiegeticButtonArray * msg);

/// Check for msg/DiegeticButtonArray message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
bool
diegetic_button_pkg__msg__DiegeticButtonArray__are_equal(const diegetic_button_pkg__msg__DiegeticButtonArray * lhs, const diegetic_button_pkg__msg__DiegeticButtonArray * rhs);

/// Copy a msg/DiegeticButtonArray message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
bool
diegetic_button_pkg__msg__DiegeticButtonArray__copy(
  const diegetic_button_pkg__msg__DiegeticButtonArray * input,
  diegetic_button_pkg__msg__DiegeticButtonArray * output);

/// Initialize array of msg/DiegeticButtonArray messages.
/**
 * It allocates the memory for the number of elements and calls
 * diegetic_button_pkg__msg__DiegeticButtonArray__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
bool
diegetic_button_pkg__msg__DiegeticButtonArray__Sequence__init(diegetic_button_pkg__msg__DiegeticButtonArray__Sequence * array, size_t size);

/// Finalize array of msg/DiegeticButtonArray messages.
/**
 * It calls
 * diegetic_button_pkg__msg__DiegeticButtonArray__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
void
diegetic_button_pkg__msg__DiegeticButtonArray__Sequence__fini(diegetic_button_pkg__msg__DiegeticButtonArray__Sequence * array);

/// Create array of msg/DiegeticButtonArray messages.
/**
 * It allocates the memory for the array and calls
 * diegetic_button_pkg__msg__DiegeticButtonArray__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
diegetic_button_pkg__msg__DiegeticButtonArray__Sequence *
diegetic_button_pkg__msg__DiegeticButtonArray__Sequence__create(size_t size);

/// Destroy array of msg/DiegeticButtonArray messages.
/**
 * It calls
 * diegetic_button_pkg__msg__DiegeticButtonArray__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
void
diegetic_button_pkg__msg__DiegeticButtonArray__Sequence__destroy(diegetic_button_pkg__msg__DiegeticButtonArray__Sequence * array);

/// Check for msg/DiegeticButtonArray message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
bool
diegetic_button_pkg__msg__DiegeticButtonArray__Sequence__are_equal(const diegetic_button_pkg__msg__DiegeticButtonArray__Sequence * lhs, const diegetic_button_pkg__msg__DiegeticButtonArray__Sequence * rhs);

/// Copy an array of msg/DiegeticButtonArray messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_diegetic_button_pkg
bool
diegetic_button_pkg__msg__DiegeticButtonArray__Sequence__copy(
  const diegetic_button_pkg__msg__DiegeticButtonArray__Sequence * input,
  diegetic_button_pkg__msg__DiegeticButtonArray__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // DIEGETIC_BUTTON_PKG__MSG__DETAIL__DIEGETIC_BUTTON_ARRAY__FUNCTIONS_H_
