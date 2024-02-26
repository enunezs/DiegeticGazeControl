// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from diegetic_button_pkg:msg/DiegeticButton.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "diegetic_button_pkg/msg/detail/diegetic_button__struct.h"
#include "diegetic_button_pkg/msg/detail/diegetic_button__functions.h"

#include "rosidl_runtime_c/string.h"
#include "rosidl_runtime_c/string_functions.h"

ROSIDL_GENERATOR_C_IMPORT
bool geometry_msgs__msg__transform__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * geometry_msgs__msg__transform__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool diegetic_button_pkg__msg__diegetic_button__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[56];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("diegetic_button_pkg.msg._diegetic_button.DiegeticButton", full_classname_dest, 55) == 0);
  }
  diegetic_button_pkg__msg__DiegeticButton * ros_message = _ros_message;
  {  // button_id
    PyObject * field = PyObject_GetAttrString(_pymsg, "button_id");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->button_id, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // button_transform
    PyObject * field = PyObject_GetAttrString(_pymsg, "button_transform");
    if (!field) {
      return false;
    }
    if (!geometry_msgs__msg__transform__convert_from_py(field, &ros_message->button_transform)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }
  {  // x0
    PyObject * field = PyObject_GetAttrString(_pymsg, "x0");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->x0 = PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // y0
    PyObject * field = PyObject_GetAttrString(_pymsg, "y0");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->y0 = PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // x1
    PyObject * field = PyObject_GetAttrString(_pymsg, "x1");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->x1 = PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // y1
    PyObject * field = PyObject_GetAttrString(_pymsg, "y1");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->y1 = PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * diegetic_button_pkg__msg__diegetic_button__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of DiegeticButton */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("diegetic_button_pkg.msg._diegetic_button");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "DiegeticButton");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  diegetic_button_pkg__msg__DiegeticButton * ros_message = (diegetic_button_pkg__msg__DiegeticButton *)raw_ros_message;
  {  // button_id
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->button_id.data,
      strlen(ros_message->button_id.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "button_id", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // button_transform
    PyObject * field = NULL;
    field = geometry_msgs__msg__transform__convert_to_py(&ros_message->button_transform);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "button_transform", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // x0
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->x0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "x0", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // y0
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->y0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "y0", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // x1
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->x1);
    {
      int rc = PyObject_SetAttrString(_pymessage, "x1", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // y1
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->y1);
    {
      int rc = PyObject_SetAttrString(_pymessage, "y1", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
