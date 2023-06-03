
from intbase import InterpreterBase, ErrorType
from type_valuev2 import Type, create_value, create_default_value
import copy

class VariableDef:
    # var_type is a Type() and value is a Value()
    def __init__(self, var_type, var_name, value=None):
        self.type = var_type
        self.name = var_name
        self.value = value

    def set_value(self, value):
        self.value = value


# parses and holds the definition of a member method
# [method return_type method_name [[type1 param1] [type2 param2] ...] [statement]]
class MethodDef:
    def __init__(self, method_source):
        self.line_num = method_source[0].line_num  # used for errors
        self.method_name = method_source[2]
        if method_source[1] == InterpreterBase.VOID_DEF:
            self.return_type = Type(InterpreterBase.NOTHING_DEF)
        else:
            self.return_type = Type(method_source[1])
        self.formal_params = self.__parse_params(method_source[3])
        self.code = method_source[4]

    def get_method_name(self):
        return self.method_name

    def get_formal_params(self):
        return self.formal_params

    # returns a Type()
    def get_return_type(self):
        return self.return_type

    def get_code(self):
        return self.code

    # input params in the form of [[type1 param1] [type2 param2] ...]
    # output is a set of VariableDefs
    def __parse_params(self, params):
        formal_params = []
        for param in params:
            var_def = VariableDef(Type(param[0]), param[1])
            formal_params.append(var_def)
        return formal_params

class tClassDef:
    def __init__(self, code, interpreter):
        self.interpreter = interpreter
        self.code = code
    
    def code(self):
        return self.code
    
    def create_class_def_from_template(self,class_name,actual_types):
        print(self.code)
        print(actual_types)
        code = copy.copy(self.code)
        code[0] = InterpreterBase.CLASS_DEF
        field_replacements = dict(zip(code[2], actual_types))
        code = replace_fields(code, field_replacements)
        code.pop(2)
        code[1] = class_name
        self.interpreter.type_manager.add_class_type(class_name,None)
        self.interpreter.class_index[class_name] = ClassDef(code, self.interpreter) 
        

def replace_fields(template, replacements):
    if isinstance(template, list):
        return [replace_fields(item, replacements) for item in template]
    elif isinstance(template, str):
        # Split and replace only if template is a string
        if '@' in template:
            type_name, field = template.split('@')
            return '@'.join([type_name, replacements.get(field, field)])
        else:
            return replacements.get(template, template)
    else:
        return template



# holds definition for a class, including a list of all the fields and their default values, all
# of the methods in the class, and the superclass information (if any)
# v2 class definition: [class classname [inherits baseclassname] [field1] [field2] ... [method1] [method2] ...]
# [] denotes optional syntax
class ClassDef:
    def __init__(self, class_source, interpreter):
        self.interpreter = interpreter
        self.name = class_source[1]
        self.class_source = class_source
        fields_and_methods_start_index = (
            self.__check_for_inheritance_and_set_superclass_info(class_source)
        )
        self.__create_field_list(class_source[fields_and_methods_start_index:])
        self.__create_method_list(class_source[fields_and_methods_start_index:])

    # get the classname
    def get_name(self):
        return self.name

    # get a list of FieldDef objects for all fields in the class
    def get_fields(self):
        return self.fields

    # get a list of MethodDef objects for all methods in the class
    def get_methods(self):
        return self.methods

    # returns a ClassDef object
    def get_superclass(self):
        return self.super_class

    def __check_for_inheritance_and_set_superclass_info(self, class_source):
        if class_source[2] != InterpreterBase.INHERITS_DEF:
            self.super_class = None
            return 2  # fields and method definitions start after [class classname ...], jump to the correct place to continue parsing

        super_class_name = class_source[3]
        self.super_class = self.interpreter.get_class_def(
            super_class_name, class_source[0].line_num
        )
        return 4  # fields and method definitions start after [class classname inherits baseclassname ...]

    def __create_field_list(self, class_body):
        self.fields = []  # array of VariableDefs with default values set
        self.field_map = {}
        fields_defined_so_far = set()
        for member in class_body:
            # member format is [field typename varname default_value]
            if member[0] == InterpreterBase.FIELD_DEF:
                if member[2] in fields_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate field " + member[2],
                        member[0].line_num,
                    )
                var_def = self.__create_variable_def_from_field(member)
                self.fields.append(var_def)
                self.field_map[member[2]] = var_def
                fields_defined_so_far.add(member[2])

    # field def: [field typename varname defvalue]
    # returns a VariableDef object that represents that field
    def __create_variable_def_from_field(self, field_def):
        var_def = None
        """  if '@' in field_def[1]:
                #print(field_def[0])
                if field_def[1] not in self.interpreter.class_index:
                    #Not in classes defined, must check tclass_index
                    field_def_without_at = field_def[1].split('@')[0]
                    params = field_def[1].split('@')[1:]
                    if field_def_without_at in self.interpreter.tclass_index:
                        tclass = self.interpreter.tclass_index[field_def_without_at]
                        #now we instantiate our tclass into a real class
                        tclass.create_class_def_from_template(field_def[1],params) """


        if len(field_def) == 3:
            #Default Field Values
            type = Type(field_def[1])
            value = create_default_value(type)
            var_def = VariableDef(
                Type(field_def[1]), field_def[2], value
            )
        else:
            var_def = VariableDef(
                Type(field_def[1]), field_def[2], create_value(field_def[3])
            )
        if not self.interpreter.check_type_compatibility(
            var_def.type, var_def.value.type(), True
        ):
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "invalid type/type mismatch with field " + field_def[2],
                field_def[0].line_num,
            )
        return var_def

    def __create_method_list(self, class_body):
        self.methods = []
        self.method_map = {}
        methods_defined_so_far = set()
        for member in class_body:
            if member[0] == InterpreterBase.METHOD_DEF:
                method_def = MethodDef(member)
                if method_def.method_name in methods_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate method " + method_def.method_name,
                        member[0].line_num,
                    )
                self.__check_method_names_and_types(method_def)
                self.methods.append(method_def)
                self.method_map[method_def.method_name] = method_def
                methods_defined_so_far.add(method_def.method_name)

    # for a given method, make sure that the parameter types are valid, return type is valid, and param names
    # are not duplicated
    def __check_method_names_and_types(self, method_def):
        if not self.interpreter.is_valid_type(
            method_def.return_type.type_name
        ) and method_def.return_type != Type(InterpreterBase.NOTHING_DEF): #checks that return type isn't a defined type or void
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "invalid return type for method " + method_def.method_name,
                method_def.line_num,
            )
        used_param_names = set()
        for param in method_def.formal_params:
            if param.name in used_param_names:
                self.interpreter.error(
                    ErrorType.NAME_ERROR,
                    "duplicate formal parameter " + param.name,
                    method_def.line_num,
                )
            if not self.interpreter.is_valid_type(param.type.type_name):
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid type for parameter " + param.name,
                    method_def.line_num,
                )