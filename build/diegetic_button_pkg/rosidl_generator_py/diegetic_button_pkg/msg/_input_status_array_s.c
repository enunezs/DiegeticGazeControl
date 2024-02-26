// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from diegetic_button_pkg:msg/InputStatusArray.idl
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
#include "diegetic_button_pkg/msg/detail/input_status_array__struct.h"
#include "diegetic_button_pkg/msg/detail/input_status_array__functions.h"

#include "rosidl_runtime_c/primitives_sequence.h"
#include "rosidl_runtime_c/primitives_sequence_functions.h"

// Nested array functions includes
#include "diegetic_button_pkg/msg/detail/input_status__functions.h"
// end nested array functions include
ROSIDL_GENERATOR_C_IMPORT
bool std_msgs__msg__header__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * std_msgs__msg__header__convert_to_py(void * raw_ros_message);
bool diegetic_button_pkg__msg__input_status__convert_from_py(PyObject * _pymsg, void * _ros_message);
PyObject * diegetic_button_pkg__msg__input_status__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool diegetic_button_pkg__msg__input_status_array__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[61];
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
    assert(strncmp("diegetic_button_pkg.msg._input_status_array.InputStatusArray", full_classname_dest, 60) == 0);
  }
  diegetic_button_pkg__msg__InputStatusArray * ros_message = _ros_message;
  {  // header
    PyObject * field = PyObject_GetAttrString(_pymsg, "header");
    if (!field) {
      return false;
    }
    if (!std_msgs__msg__header__convert_from_py(field, &ros_message->header)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }
  {  // inputs
    PyObject * field = PyObject_GetAttrString(_pymsg, "inputs");
    if (!field) {
      return false;
    }
    PyObject * seq_field = PySequence_Fast(field, "expected a sequence in 'inputs'");
    if (!seq_field) {
      Py_DECREF(field);
      return false;
    }
    Py_ssize_t size = PySequence_Size(field);
    if (-1 == size) {
      Py_DECREF(seq_field);
      Py_DECREF(field);
      return false;
    }
    if (!diegetic_button_pkg__msg__InputStatus__Sequence__init(&(ros_message->inputs), size)) {
      PyErr_SetString(PyExc_RuntimeError, "unable to create diegetic_button_pkg__msg__InputStatus__Sequence ros_message");
      Py_DECREF(seq_field);
      Py_DECREF(field);
      return false;
    }
    diegetic_button_pkg__msg__InputStatus * dest = ros_message->inputs.data;
    for (Py_ssize_t i = 0; i < size; ++i) {
      if (!diegetic_button_pkg__msg__input_status__convert_from_py(PySequence_Fast_GET_ITEM(seq_field, i), &dest[i])) {
        Py_DECREF(seq_field);
        Py_DECREF(field);
        return false;
      }
    }
    Py_DECREF(seq_field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * diegetic_button_pkg__msg__input_status_array__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of InputStatusArray */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("diegetic_button_pkg.msg._input_status_array");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "InputStatusArray");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  diegetic_button_pkg__msg__InputStatusArray * ros_message = (diegetic_button_pkg__msg__InputStatusArray *)raw_ros_message;
  {  // header
    PyObject * field = NULL;
    field = std_msgs__msg__header__convert_to_py(&ros_message->header);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "header", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // inputs
    PyObject * field = NULL;
    size_t size = ros_message->inputs.size;
    field = PyList_New(size);
    if (!field) {
      return NULL;
    }
    diegetic_button_pkg__msg__InputStatus * item;
    for (size_t i = 0; i < size; ++i) {
      item = &(ros_message->inputs.data[i]);
      PyObject * pyitem = diegetic_button_pkg__msg__input_status__convert_to_py(item);
      if (!pyitem) {
        Py_DECREF(field);
        return NULL;
      }
      int rc = PyList_SetItem(field, i, pyitem);
      (void)rc;
      assert(rc == 0);
    }
    assert(PySequence_Check(field));
    {
      int rc = PyObject_SetAttrString(_pymessage, "inputs", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
