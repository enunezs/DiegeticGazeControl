# generated from rosidl_generator_py/resource/_idl.py.em
# with input from diegetic_button_pkg:msg/DiegeticButton.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_DiegeticButton(type):
    """Metaclass of message 'DiegeticButton'."""

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
            module = import_type_support('diegetic_button_pkg')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'diegetic_button_pkg.msg.DiegeticButton')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__diegetic_button
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__diegetic_button
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__diegetic_button
            cls._TYPE_SUPPORT = module.type_support_msg__msg__diegetic_button
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__diegetic_button

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


class DiegeticButton(metaclass=Metaclass_DiegeticButton):
    """Message class 'DiegeticButton'."""

    __slots__ = [
        '_button_id',
        '_button_transform',
        '_x0',
        '_y0',
        '_x1',
        '_y1',
    ]

    _fields_and_field_types = {
        'button_id': 'string',
        'button_transform': 'geometry_msgs/Transform',
        'x0': 'double',
        'y0': 'double',
        'x1': 'double',
        'y1': 'double',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['geometry_msgs', 'msg'], 'Transform'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.button_id = kwargs.get('button_id', str())
        from geometry_msgs.msg import Transform
        self.button_transform = kwargs.get('button_transform', Transform())
        self.x0 = kwargs.get('x0', float())
        self.y0 = kwargs.get('y0', float())
        self.x1 = kwargs.get('x1', float())
        self.y1 = kwargs.get('y1', float())

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
        if self.button_id != other.button_id:
            return False
        if self.button_transform != other.button_transform:
            return False
        if self.x0 != other.x0:
            return False
        if self.y0 != other.y0:
            return False
        if self.x1 != other.x1:
            return False
        if self.y1 != other.y1:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def button_id(self):
        """Message field 'button_id'."""
        return self._button_id

    @button_id.setter
    def button_id(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'button_id' field must be of type 'str'"
        self._button_id = value

    @builtins.property
    def button_transform(self):
        """Message field 'button_transform'."""
        return self._button_transform

    @button_transform.setter
    def button_transform(self, value):
        if __debug__:
            from geometry_msgs.msg import Transform
            assert \
                isinstance(value, Transform), \
                "The 'button_transform' field must be a sub message of type 'Transform'"
        self._button_transform = value

    @builtins.property
    def x0(self):
        """Message field 'x0'."""
        return self._x0

    @x0.setter
    def x0(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'x0' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'x0' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._x0 = value

    @builtins.property
    def y0(self):
        """Message field 'y0'."""
        return self._y0

    @y0.setter
    def y0(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'y0' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'y0' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._y0 = value

    @builtins.property
    def x1(self):
        """Message field 'x1'."""
        return self._x1

    @x1.setter
    def x1(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'x1' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'x1' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._x1 = value

    @builtins.property
    def y1(self):
        """Message field 'y1'."""
        return self._y1

    @y1.setter
    def y1(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'y1' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'y1' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._y1 = value
