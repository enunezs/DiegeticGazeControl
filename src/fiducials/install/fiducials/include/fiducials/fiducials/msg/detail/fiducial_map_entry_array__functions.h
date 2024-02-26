// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from fiducials:msg/FiducialMapEntryArray.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__FUNCTIONS_H_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "fiducials/msg/rosidl_generator_c__visibility_control.h"

#include "fiducials/msg/detail/fiducial_map_entry_array__struct.h"

/// Initialize msg/FiducialMapEntryArray message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fiducials__msg__FiducialMapEntryArray
 * )) before or use
 * fiducials__msg__FiducialMapEntryArray__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialMapEntryArray__init(fiducials__msg__FiducialMapEntryArray * msg);

/// Finalize msg/FiducialMapEntryArray message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
void
fiducials__msg__FiducialMapEntryArray__fini(fiducials__msg__FiducialMapEntryArray * msg);

/// Create msg/FiducialMapEntryArray message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fiducials__msg__FiducialMapEntryArray__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
fiducials__msg__FiducialMapEntryArray *
fiducials__msg__FiducialMapEntryArray__create();

/// Destroy msg/FiducialMapEntryArray message.
/**
 * It calls
 * fiducials__msg__FiducialMapEntryArray__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
void
fiducials__msg__FiducialMapEntryArray__destroy(fiducials__msg__FiducialMapEntryArray * msg);

/// Check for msg/FiducialMapEntryArray message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialMapEntryArray__are_equal(const fiducials__msg__FiducialMapEntryArray * lhs, const fiducials__msg__FiducialMapEntryArray * rhs);

/// Copy a msg/FiducialMapEntryArray message.
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
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialMapEntryArray__copy(
  const fiducials__msg__FiducialMapEntryArray * input,
  fiducials__msg__FiducialMapEntryArray * output);

/// Initialize array of msg/FiducialMapEntryArray messages.
/**
 * It allocates the memory for the number of elements and calls
 * fiducials__msg__FiducialMapEntryArray__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialMapEntryArray__Sequence__init(fiducials__msg__FiducialMapEntryArray__Sequence * array, size_t size);

/// Finalize array of msg/FiducialMapEntryArray messages.
/**
 * It calls
 * fiducials__msg__FiducialMapEntryArray__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
void
fiducials__msg__FiducialMapEntryArray__Sequence__fini(fiducials__msg__FiducialMapEntryArray__Sequence * array);

/// Create array of msg/FiducialMapEntryArray messages.
/**
 * It allocates the memory for the array and calls
 * fiducials__msg__FiducialMapEntryArray__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
fiducials__msg__FiducialMapEntryArray__Sequence *
fiducials__msg__FiducialMapEntryArray__Sequence__create(size_t size);

/// Destroy array of msg/FiducialMapEntryArray messages.
/**
 * It calls
 * fiducials__msg__FiducialMapEntryArray__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
void
fiducials__msg__FiducialMapEntryArray__Sequence__destroy(fiducials__msg__FiducialMapEntryArray__Sequence * array);

/// Check for msg/FiducialMapEntryArray message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialMapEntryArray__Sequence__are_equal(const fiducials__msg__FiducialMapEntryArray__Sequence * lhs, const fiducials__msg__FiducialMapEntryArray__Sequence * rhs);

/// Copy an array of msg/FiducialMapEntryArray messages.
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
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialMapEntryArray__Sequence__copy(
  const fiducials__msg__FiducialMapEntryArray__Sequence * input,
  fiducials__msg__FiducialMapEntryArray__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_MAP_ENTRY_ARRAY__FUNCTIONS_H_
