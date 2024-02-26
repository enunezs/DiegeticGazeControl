// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from fiducials:msg/FiducialTransform.idl
// generated code does not contain a copyright notice

#ifndef FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__FUNCTIONS_H_
#define FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "fiducials/msg/rosidl_generator_c__visibility_control.h"

#include "fiducials/msg/detail/fiducial_transform__struct.h"

/// Initialize msg/FiducialTransform message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fiducials__msg__FiducialTransform
 * )) before or use
 * fiducials__msg__FiducialTransform__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialTransform__init(fiducials__msg__FiducialTransform * msg);

/// Finalize msg/FiducialTransform message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
void
fiducials__msg__FiducialTransform__fini(fiducials__msg__FiducialTransform * msg);

/// Create msg/FiducialTransform message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fiducials__msg__FiducialTransform__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
fiducials__msg__FiducialTransform *
fiducials__msg__FiducialTransform__create();

/// Destroy msg/FiducialTransform message.
/**
 * It calls
 * fiducials__msg__FiducialTransform__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
void
fiducials__msg__FiducialTransform__destroy(fiducials__msg__FiducialTransform * msg);

/// Check for msg/FiducialTransform message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialTransform__are_equal(const fiducials__msg__FiducialTransform * lhs, const fiducials__msg__FiducialTransform * rhs);

/// Copy a msg/FiducialTransform message.
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
fiducials__msg__FiducialTransform__copy(
  const fiducials__msg__FiducialTransform * input,
  fiducials__msg__FiducialTransform * output);

/// Initialize array of msg/FiducialTransform messages.
/**
 * It allocates the memory for the number of elements and calls
 * fiducials__msg__FiducialTransform__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialTransform__Sequence__init(fiducials__msg__FiducialTransform__Sequence * array, size_t size);

/// Finalize array of msg/FiducialTransform messages.
/**
 * It calls
 * fiducials__msg__FiducialTransform__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
void
fiducials__msg__FiducialTransform__Sequence__fini(fiducials__msg__FiducialTransform__Sequence * array);

/// Create array of msg/FiducialTransform messages.
/**
 * It allocates the memory for the array and calls
 * fiducials__msg__FiducialTransform__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
fiducials__msg__FiducialTransform__Sequence *
fiducials__msg__FiducialTransform__Sequence__create(size_t size);

/// Destroy array of msg/FiducialTransform messages.
/**
 * It calls
 * fiducials__msg__FiducialTransform__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
void
fiducials__msg__FiducialTransform__Sequence__destroy(fiducials__msg__FiducialTransform__Sequence * array);

/// Check for msg/FiducialTransform message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fiducials
bool
fiducials__msg__FiducialTransform__Sequence__are_equal(const fiducials__msg__FiducialTransform__Sequence * lhs, const fiducials__msg__FiducialTransform__Sequence * rhs);

/// Copy an array of msg/FiducialTransform messages.
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
fiducials__msg__FiducialTransform__Sequence__copy(
  const fiducials__msg__FiducialTransform__Sequence * input,
  fiducials__msg__FiducialTransform__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // FIDUCIALS__MSG__DETAIL__FIDUCIAL_TRANSFORM__FUNCTIONS_H_
