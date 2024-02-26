// generated from rosidl_typesupport_c/resource/idl__type_support.cpp.em
// with input from diegetic_button_pkg:msg/InputStatus.idl
// generated code does not contain a copyright notice

#include "cstddef"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "diegetic_button_pkg/msg/detail/input_status__struct.h"
#include "diegetic_button_pkg/msg/detail/input_status__type_support.h"
#include "rosidl_typesupport_c/identifier.h"
#include "rosidl_typesupport_c/message_type_support_dispatch.h"
#include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_c/visibility_control.h"
#include "rosidl_typesupport_interface/macros.h"

namespace diegetic_button_pkg
{

namespace msg
{

namespace rosidl_typesupport_c
{

typedef struct _InputStatus_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _InputStatus_type_support_ids_t;

static const _InputStatus_type_support_ids_t _InputStatus_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _InputStatus_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _InputStatus_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _InputStatus_type_support_symbol_names_t _InputStatus_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, diegetic_button_pkg, msg, InputStatus)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, diegetic_button_pkg, msg, InputStatus)),
  }
};

typedef struct _InputStatus_type_support_data_t
{
  void * data[2];
} _InputStatus_type_support_data_t;

static _InputStatus_type_support_data_t _InputStatus_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _InputStatus_message_typesupport_map = {
  2,
  "diegetic_button_pkg",
  &_InputStatus_message_typesupport_ids.typesupport_identifier[0],
  &_InputStatus_message_typesupport_symbol_names.symbol_name[0],
  &_InputStatus_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t InputStatus_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_InputStatus_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace msg

}  // namespace diegetic_button_pkg

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, diegetic_button_pkg, msg, InputStatus)() {
  return &::diegetic_button_pkg::msg::rosidl_typesupport_c::InputStatus_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
