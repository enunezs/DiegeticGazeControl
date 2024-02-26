# generated from rosidl_generator_py/resource/_idl.py.em
# with input from fiducials:msg/FiducialTransform.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_FiducialTransform(type):
    """Metaclass of message 'FiducialTransform'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('fiducials')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'fiducials.msg.FiducialTransform')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__fiducial_transform
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__fiducial_transform
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__fiducial_transform
            cls._TYPE_SUPPORT = module.type_support_msg__msg__fiducial_transform
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__fiducial_transform

            from geometry_msgs.msg import Transform
            if Transform.__class__._TYPE_SUPPORT is None:
                Transform.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class FiducialTransform(metaclass=Metaclass_FiducialTransform):
    """Message class 'FiducialTransform'."""

    __slots__ = [
        '_fiducial_id',
        '_transform',
        '_image_error',
        '_object_error',
        '_fiducial_area',
    ]

    _fields_and_field_types = {
        'fiducial_id': 'int32',
        'transform': 'geometry_msgs/Transform',
        'image_error': 'double',
        'object_error': 'double',
        'fiducial_area': 'double',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['geometry_msgs', 'msg'], 'Transform'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.fiducial_id = kwargs.get('fiducial_id', int())
        from geometry_msgs.msg import Transform
        self.transform = kwargs.get('transform', Transform())
        self.image_error = kwargs.get('image_error', float())
        self.object_error = kwargs.get('object_error', float())
        self.fiducial_area = kwargs.get('fiducial_area', float())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.fiducial_id != other.fiducial_id:
            return False
        if self.transform != other.transform:
            return False
        if self.image_error != other.image_error:
            return False
        if self.object_error != other.object_error:
            return False
        if self.fiducial_area != other.fiducial_area:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def fiducial_id(self):
        """Message field 'fiducial_id'."""
        return self._fiducial_id

    @fiducial_id.setter
    def fiducial_id(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'fiducial_id' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'fiducial_id' field must be an integer in [-2147483648, 2147483647]"
        self._fiducial_id = value

    @builtins.property
    def transform(self):
        """Message field 'transform'."""
        return self._transform

    @transform.setter
    def transform(self, value):
        if __debug__:
            from geometry_msgs.msg import Transform
            assert \
                isinstance(value, Transform), \
                "The 'transform' field must be a sub message of type 'Transform'"
        self._transform = value

    @builtins.property
    def image_error(self):
        """Message field 'image_error'."""
        return self._image_error

    @image_error.setter
    def image_error(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'image_error' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'image_error' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._image_error = value

    @builtins.property
    def object_error(self):
        """Message field 'object_error'."""
        return self._object_error

    @object_error.setter
    def object_error(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'object_error' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'object_error' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._object_error = value

    @builtins.property
    def fiducial_area(self):
        """Message field 'fiducial_area'."""
        return self._fiducial_area

    @fiducial_area.setter
    def fiducial_area(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'fiducial_area' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'fiducial_area' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._fiducial_area = value
