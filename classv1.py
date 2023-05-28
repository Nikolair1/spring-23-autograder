# pylint: disable=too-few-public-methods

"""
Module with classes for class, field, and method definitions.

In P1, we don't allow overloading within a class;
two methods cannot have the same name with different parameters.
"""

from intbase import InterpreterBase, ErrorType
from type_valuev1 import create_value, validate_field_init, validate_method_init
from type_valuev1 import Type, Value


class MethodDef:
    """
    Wrapper struct for the definition of a member method.
    """

    def __init__(self, method_def,class_set,interpreter):
        self.class_set = class_set
        self.return_type = method_def[1]
        self.method_name = method_def[2]
        self.formal_params = validate_method_init(method_def[3],class_set,interpreter) #handles type checking of initial method values
        self.code = method_def[4]
    
    def get_return_type(self):
        return self.return_type
    

class FieldDef:
    """
    Wrapper struct for the definition of a member field.
    """

    def __init__(self, field_def, class_set,interpreter):
        self.type = field_def[1]
        self.field_name = field_def[2]
        self.default_field_value = field_def[3]
        self.class_set = class_set
        self.field_value =  validate_field_init(self.default_field_value, self.type, self.class_set,interpreter) #handles type checking of field
        


class ClassDef:
    """
    Holds definition for a class:
        - list of fields (and default values)
        - list of methods

    class definition: [class classname [field1 field2 ... method1 method2 ...]]
    """

    def __init__(self, class_def, interpreter, class_set):
        self.interpreter = interpreter
        self.name = class_def[1]
        self.class_set = class_set
        self.parent_reference = None
        self.data_index = self.__check_inheritance(class_def)
        self.__create_field_list(class_def[self.data_index:], self.class_set)
        self.__create_method_list(class_def[self.data_index:],self.class_set)
        
    def get_name(self):
        return self.name

    def get_parent_ref(self):
        return self.parent_reference
    
    def get_fields(self):
        """
        Get a list of FieldDefs for *all* fields in the class.
        """
        return self.fields

    def get_methods(self):
        """
        Get a list of MethodDefs for *all* fields in the class.
        """
        return self.methods

    def __check_inheritance(self,class_def):
        if not isinstance(class_def[2],list):
            if class_def[2] == InterpreterBase.INHERITS_DEF:
                parent = class_def[3]
                obj = self.interpreter.instantiate(parent,None)
                self.parent_reference = Value(Type.CLASS, obj,class_name=parent)
                return 4
        else:
            return 2

    def __create_field_list(self, class_body,class_set):
        #print("class_body variable: ",class_body)
        self.fields = []
        fields_defined_so_far = set()
        for member in class_body:
            if member[0] == InterpreterBase.FIELD_DEF:
                if member[2] in fields_defined_so_far:  # redefinition, works
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate field " + member[2],
                        member[0].line_num,
                    )
                self.fields.append(FieldDef(member,class_set,self.interpreter))
                fields_defined_so_far.add(member[2])
        

    def __create_method_list(self, class_body,class_set):
        self.methods = []
        methods_defined_so_far = set()
        #print(class_body)
        for member in class_body:
            if member[0] == InterpreterBase.METHOD_DEF:
                if member[2] in methods_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate method " + member[2],
                        member[0].line_num,
                    )
                self.methods.append(MethodDef(member,class_set,self.interpreter))
                methods_defined_so_far.add(member[2])
        #print(self.methods,methods_defined_so_far)
        #breakpoint()
