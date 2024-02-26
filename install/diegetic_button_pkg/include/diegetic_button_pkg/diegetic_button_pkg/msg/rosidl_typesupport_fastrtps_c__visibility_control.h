// generated from
// rosidl_typesupport_fastrtps_c/resource/rosidl_typesupport_fastrtps_c__visibility_control.h.in
// generated code does not contain a copyright notice

#ifndef DIEGETIC_BUTTON_PKG__MSG__ROSIDL_TYPESUPPORT_FASTRTPS_C__VISIBILITY_CONTROL_H_
#define DIEGETIC_BUTTON_PKG__MSG__ROSIDL_TYPESUPPORT_FASTRTPS_C__VISIBILITY_CONTROL_H_

#if __cplusplus
extern "C"
{
#endif

// This logic was borrowed (then namespaced) from the examples on the gcc wiki:
//     https://gcc.gnu.org/wiki/Visibility

#if defined _WIN32 || defined __CYGWIN__
  #ifdef __GNUC__
    #define ROSIDL_TYPESUPPORT_FASTRTPS_C_EXPORT_diegetic_button_pkg __attribute__ ((dllexport))
    #define ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_diegetic_button_pkg __attribute__ ((dllimport))
  #else
    #define ROSIDL_TYPESUPPORT_FASTRTPS_C_EXPORT_diegetic_button_pkg __declspec(dllexport)
    #define ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_diegetic_button_pkg __declspec(dllimport)
  #endif
  #ifdef ROSIDL_TYPESUPPORT_FASTRTPS_C_BUILDING_DLL_diegetic_button_pkg
    #define ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_diegetic_button_pkg ROSIDL_TYPESUPPORT_FASTRTPS_C_EXPORT_diegetic_button_pkg
  #else
    #define ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_diegetic_button_pkg ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_diegetic_button_pkg
  #endif
#else
  #define ROSIDL_TYPESUPPORT_FASTRTPS_C_EXPORT_diegetic_button_pkg __attribute__ ((visibility("default")))
  #define ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_diegetic_button_pkg
  #if __GNUC__ >= 4
    #define ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_diegetic_button_pkg __attribute__ ((visibility("default")))
  #else
    #define ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_diegetic_button_pkg
  #endif
#endif

#if __cplusplus
}
#endif

#endif  // DIEGETIC_BUTTON_PKG__MSG__ROSIDL_TYPESUPPORT_FASTRTPS_C__VISIBILITY_CONTROL_H_
