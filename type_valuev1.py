"""
Module that contains the Value definition and associated type constructs.
"""

from enum import Enum
from intbase import InterpreterBase, ErrorType


class Type(Enum):
    """Enum for all possible Brewin types."""

    INT = 1
    BOOL = 2
    STRING = 3
    CLASS = 4
    NOTHING = 5


# Represents a value, which has a type and its value
class Value:
    """A representation for a value that contains a type tag."""

    def __init__(self, value_type, value=None,class_name = None):
        self.__type = value_type
        self.__value = value
        self.__class_name = class_name

    def type(self):
        return self.__type

    def value(self):
        return self.__value
    
    def class_name(self):
        return self.__class_name

    def set(self, other):
        self.__type = other.type()
        self.__value = other.value()


def validate_field_init(val, type, class_set,interpreter):
        if type == InterpreterBase.BOOL_DEF:
            if val == InterpreterBase.TRUE_DEF:
                return Value(Type.BOOL, True)
            if val == InterpreterBase.FALSE_DEF:
                return Value(Type.BOOL, False)
            interpreter.error(ErrorType.TYPE_ERROR, "must create values with correct type ")
        if type == InterpreterBase.STRING_DEF:
            if val[0] == '"':
                return Value(Type.STRING, val.strip('"'))
            interpreter.error(ErrorType.TYPE_ERROR, "must create values with correct type ")
        if type == InterpreterBase.INT_DEF:
            if val.lstrip('-').isnumeric():
                return Value(Type.INT, int(val))
            interpreter.error(ErrorType.TYPE_ERROR, "must create values with correct type ")
        
        if type in class_set:
            if val == InterpreterBase.NULL_DEF:
                x = Value(Type.CLASS, value=None, class_name=type)
                return x
            interpreter.error(ErrorType.TYPE_ERROR, "must initialize a class type to null ")

        return interpreter.error(ErrorType.TYPE_ERROR, "invalid field type ")


def validate_method_init(vals,class_set,interpreter):
    formal_params = []
    name_set = set()
    for val in vals:
            type = val[0]
            name = val[1]
            if name in name_set:
                interpreter.error(ErrorType.NAME_ERROR, "duplicate formal params ")
            name_set.add(name)
            if type == InterpreterBase.BOOL_DEF:
                formal_params.append(Value(Type.BOOL, name))
            elif type == InterpreterBase.STRING_DEF:
                 formal_params.append(Value(Type.STRING, name))
            elif type == InterpreterBase.INT_DEF:
                formal_params.append(Value(Type.INT, name))
            elif type in class_set:
                formal_params.append(Value(Type.CLASS, value=name, class_name=type))
            else: 
                interpreter.error(ErrorType.TYPE_ERROR, "invalid formal param type ")
    return formal_params




# pylint: disable=too-many-return-statements
def create_value(val,type=None):
    """
    Create a Value object from a Python value.
    """
   
    if type=="val":
        return create_just_a_value(val)
    
    if type == InterpreterBase.BOOL_DEF:
        if val == InterpreterBase.TRUE_DEF:
            return Value(Type.BOOL, True)
        if val == InterpreterBase.FALSE_DEF:
            return Value(Type.BOOL, False)
        InterpreterBase.error(ErrorType.TYPE_ERROR, "must create values with correct type ")
    if type == InterpreterBase.STRING_DEF:
        if val[0] == '"':
            return Value(Type.STRING, val.strip('"'))
        InterpreterBase.error(ErrorType.TYPE_ERROR, "must create values with correct type ")
    if type == InterpreterBase.INT_DEF:
        if val.lstrip('-').isnumeric():
            return Value(Type.INT, int(val))
        InterpreterBase.error(ErrorType.TYPE_ERROR, "must create values with correct type ")
    #TODO: For checking null, I need to check if the type is a class that has been defined or the current class
    if val == InterpreterBase.NULL_DEF:
        return Value(Type.CLASS, None)
    if val == InterpreterBase.NOTHING_DEF:
        return Value(Type.NOTHING, None)
    return None

def create_just_a_value(val):
    if val == InterpreterBase.TRUE_DEF:
        return Value(Type.BOOL, True)
    if val == InterpreterBase.FALSE_DEF:
        return Value(Type.BOOL, False)
    if val[0] == '"':
        return Value(Type.STRING, val.strip('"'))
    if val.lstrip('-').isnumeric():
        return Value(Type.INT, int(val))
    if val == InterpreterBase.NULL_DEF:
        return Value(Type.CLASS, None)
    if val == InterpreterBase.NOTHING_DEF:
        return Value(Type.NOTHING, None)
    return None