"""
Module handling the operations of an object. This contains the meat
of the code to execute various instructions.
"""

from env_v1 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev1 import create_value
from type_valuev1 import Type, Value


class ObjectDef:
    STATUS_PROCEED = 0
    STATUS_RETURN = 1
    STATUS_NAME_ERROR = 2
    STATUS_TYPE_ERROR = 3

    def __init__(self, interpreter, class_def, trace_output,classes_defined_set):
        self.interpreter = interpreter  # objref to interpreter object. used to report errors, get input, produce output
        self.class_def = class_def  # take class body from 3rd+ list elements, e.g., ["class",classname", [classbody]]
        self.classes_defined_set = classes_defined_set
        self.parent_obj = class_def.get_parent_ref()
        #print(f"{class_def.get_name()}'s parent obj is {self.parent_obj}")
        self.trace_output = trace_output
        self.__map_fields_to_values()
        self.__map_method_names_to_method_definitions()
        self.__create_map_of_operations_to_lambdas()  # sets up maps to facilitate binary and unary operations, e.g., (+ 5 6)

    def get_name(self):
        return self.class_def.get_name()

    def call_method(self, method_name, actual_params, line_num_of_caller):
        """
        actual_params is a list of Value objects (all parameters are passed by value).

        The caller passes in the line number so we can properly generate an error message.
        The error is then generated at the source (i.e., where the call is initiated).
        """
        if method_name not in self.methods:
            #now we should check the parent
            if self.parent_obj is not None:
                parent = self.parent_obj.value()
                return parent.call_method(method_name,actual_params,line_num_of_caller)
            else:
                self.interpreter.error(
                    ErrorType.NAME_ERROR,
                    "unknown method " + method_name,
                    line_num_of_caller,
                )
        method_info = self.methods[method_name]
        if len(actual_params) != len(method_info.formal_params):
            if self.parent_obj is not None:
                parent = self.parent_obj.value()
                return parent.call_method(method_name,actual_params,line_num_of_caller)
            else:
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid number of parameters in call to " + method_name,
                    line_num_of_caller,
                )
        env = [EnvironmentManager()]  # maintains lexical environment for function as stack of environments; just params for now
        
        #need to validate called types
        error = self.call_params_checker(method_info.formal_params,actual_params)
        if error:
            if self.parent_obj is not None:
                parent = self.parent_obj.value()
                return parent.call_method(method_name,actual_params,line_num_of_caller)
            else:
                self.interpreter.error(
                    ErrorType.NAME_ERROR,
                    "incorrect param types " + method_name,
                    line_num_of_caller,
                )

        for formal, actual in zip(method_info.formal_params, actual_params):
            env[0].set(formal.value(), actual)
        # since each method has a single top-level statement, execute it.
        status, return_value = self.__execute_statement(env, method_info.code)
        # if the method explicitly used the (return expression) statement to return a value, then return that
        # value back to the caller
        #print("my return type is: ", method_info.return_type)
        if status == ObjectDef.STATUS_RETURN:
            #return blank case          
            if method_info.return_type == InterpreterBase.VOID_DEF and return_value.type() != Type.NOTHING:
                return self.interpreter.error(ErrorType.TYPE_ERROR, "void must return nothing ")

            if return_value.value() == None and method_info.return_type != InterpreterBase.VOID_DEF:
                return_value = self.default_return_selector(method_info.return_type)

            self.return_type_checker(method_info.return_type,return_value)
            return return_value
        
        default_val = self.default_return_selector(method_info.return_type)
        return default_val

    def call_params_checker(self,formal_params,actual_params):

        for i,params in enumerate(formal_params):
            good = False
            if formal_params[i].type() == Type.CLASS:
                if formal_params[i].class_name() != actual_params[i].class_name():
                    temp = Value(Type.CLASS, None)
                    temp.set(actual_params[i])
                    while temp.value().parent_obj is not None:
                        if temp.value().parent_obj.value().get_name() == formal_params[i].class_name():
                            good = True
                            break
                        temp.set(temp.value().parent_obj)
                    if not good:
                        return True
            elif formal_params[i].type() != actual_params[i].type():
                return True
            
        return False
    
    
    def return_type_checker(self, return_type, return_value):
        valid_return_types = [InterpreterBase.VOID_DEF,InterpreterBase.STRING_DEF,
                              InterpreterBase.INT_DEF,InterpreterBase.BOOL_DEF]
        
        if return_type == InterpreterBase.VOID_DEF and return_value.value() != None:
            return self.interpreter.error(ErrorType.TYPE_ERROR)
        elif return_type == InterpreterBase.STRING_DEF and return_value.type() != Type.STRING:
            return self.interpreter.error(ErrorType.TYPE_ERROR)
        elif return_type == InterpreterBase.INT_DEF and return_value.type() != Type.INT:
            return self.interpreter.error(ErrorType.TYPE_ERROR)
        elif return_type == InterpreterBase.BOOL_DEF and return_value.type() != Type.BOOL:
            return self.interpreter.error(ErrorType.TYPE_ERROR)
        elif return_type in self.classes_defined_set and return_value.type() != Type.NOTHING:
            if return_value.type() != Type.CLASS:
                return self.interpreter.error(ErrorType.TYPE_ERROR,"bad class return value ")
            else:
                temp = Value(Type.CLASS, None)
                temp.set(return_value)
                while temp.value().parent_obj is not None:
                    if temp.value().parent_obj.value().get_name() == return_type:
                        return
                    temp.set(temp.value().parent_obj)
                return self.interpreter.error(ErrorType.TYPE_ERROR,"bad class return value ")
        elif return_type not in valid_return_types and return_type not in self.classes_defined_set:
            return self.interpreter.error(ErrorType.TYPE_ERROR,"invalid return type ")
        
      

        

    def default_return_selector(self,return_type):
        if return_type == InterpreterBase.INT_DEF:
            return Value(Type.INT,0)
        elif return_type == InterpreterBase.BOOL_DEF:
            return Value(Type.BOOL,False)
        elif return_type == InterpreterBase.STRING_DEF:
            return Value(Type.STRING,"")
        elif return_type in self.classes_defined_set or return_type == InterpreterBase.VOID_DEF:
            return Value(Type.NOTHING)
        else:
            return self.interpreter.error(ErrorType.TYPE_ERROR,"return type does not exist ")
       
    def __execute_statement(self, env, code):
        """
        returns (status_code, return_value) where:
        - status_code indicates if the next statement includes a return
            - if so, the current method should terminate
            - otherwise, the next statement in the method should run normally
        - return_value is a Value containing the returned value from the function
        """
        if self.trace_output:
            print(f"{code[0].line_num}: {code}")
        tok = code[0]
        if tok == InterpreterBase.BEGIN_DEF:
            return self.__execute_begin(env, code)
        if tok == InterpreterBase.SET_DEF:
            return self.__execute_set(env, code)
        if tok == InterpreterBase.IF_DEF:
            return self.__execute_if(env, code)
        if tok == InterpreterBase.CALL_DEF:
            return self.__execute_call(env, code)
        if tok == InterpreterBase.WHILE_DEF:
            return self.__execute_while(env, code)
        if tok == InterpreterBase.RETURN_DEF:
            return self.__execute_return(env, code)
        if tok == InterpreterBase.INPUT_STRING_DEF:
            return self.__execute_input(env, code, True)
        if tok == InterpreterBase.INPUT_INT_DEF:
            return self.__execute_input(env, code, False)
        if tok == InterpreterBase.PRINT_DEF:
            return self.__execute_print(env, code)
        if tok == InterpreterBase.LET_DEF:
            return self.__execute_let(env,code)

        self.interpreter.error(
            ErrorType.SYNTAX_ERROR, "unknown statement " + tok, tok.line_num
        )

    # (begin (statement1) (statement2) ... (statementn))
    def __execute_begin(self, env, code):
        for statement in code[1:]:
            status, return_value = self.__execute_statement(env, statement)
            if status == ObjectDef.STATUS_RETURN:
                return (
                    status,
                    return_value,
                )  # could be a valid return of a value or an error
        # if we run thru the entire block without a return, then just return proceed
        # we don't want the calling block to exit with a return
        return ObjectDef.STATUS_PROCEED, None

    def __execute_let(self, env, code):
        new_env = (EnvironmentManager())
        local_vars = code[1]
        name_set = set()
        for local_var in local_vars:
            new_env.set(local_var[1],self.verify_declaration(local_var,name_set))
            name_set.add(local_var[1])
        env.append(new_env)

        #now run statements
        for statement in code[2:]:
            status, return_value = self.__execute_statement(env, statement)
            if status == ObjectDef.STATUS_RETURN:
                return (
                    status,
                    return_value,
                )  # could be a valid return of a value or an error
        # if we run thru the entire block without a return, then just return proceed
        # we don't want the calling block to exit with a return

        env.pop()
        return ObjectDef.STATUS_PROCEED, None
    
    def verify_declaration(self,local_var,name_set):
        type = local_var[0]
        name = local_var[1]
        val = local_var[2]
        if name in name_set:
            return self.interpreter.error(ErrorType.NAME_ERROR, "duplicate variable names ")
        if type == InterpreterBase.BOOL_DEF:
            if val == InterpreterBase.TRUE_DEF:
                return Value(Type.BOOL, True)
            if val == InterpreterBase.FALSE_DEF:
                return Value(Type.BOOL, False)
            self.interpreter.error(ErrorType.TYPE_ERROR, "must create values with correct type ")
        if type == InterpreterBase.STRING_DEF:
            if val[0] == '"':
                return Value(Type.STRING, val.strip('"'))
            self.interpreter.error(ErrorType.TYPE_ERROR, "must create values with correct type ")
        if type == InterpreterBase.INT_DEF:
            if val.lstrip('-').isnumeric():
                return Value(Type.INT, int(val))
            self.interpreter.error(ErrorType.TYPE_ERROR, "must create values with correct type ")
        if type in self.class_set:
            if val == InterpreterBase.NULL_DEF:
                x = Value(Type.CLASS, value=None, class_name=type)
                return x
            self.interpreter.error(ErrorType.TYPE_ERROR, "must initialize a class type to null ")

        return self.interpreter.error(ErrorType.TYPE_ERROR, "invalid var type ")


    # (call object_ref/me methodname param1 param2 param3)
    # where params are expressions, and expresion could be a value, or a (+ ...)
    # statement version of a method call; there's also an expression version of a method call below
    def __execute_call(self, env, code):
        return ObjectDef.STATUS_PROCEED, self.__execute_call_aux(
            env, code, code[0].line_num
        )

    # (set varname expression), where expresion could be a value, or a (+ ...)
    def __execute_set(self, env, code):
        val = self.__evaluate_expression(env, code[2], code[0].line_num)
        self.__set_variable_aux(env, code[1], val, code[0].line_num)
        return ObjectDef.STATUS_PROCEED, None

    # (return expression) where expresion could be a value, or a (+ ...)
    def __execute_return(self, env, code):
        if len(code) == 1:
            # [return] with no return expression
            return ObjectDef.STATUS_RETURN, create_value(InterpreterBase.NOTHING_DEF)
        return ObjectDef.STATUS_RETURN, self.__evaluate_expression(
            env, code[1], code[0].line_num
        )

    # (print expression1 expression2 ...) where expresion could be a variable, value, or a (+ ...)
    def __execute_print(self, env, code):
        output = ""
        for expr in code[1:]:
            # TESTING NOTE: Will not test printing of object references
            term = self.__evaluate_expression(env, expr, code[0].line_num)
            val = term.value()
            typ = term.type()
            if typ == Type.BOOL:
                val = "true" if val else "false"
            # document - will never print out an object ref
            output += str(val)
        self.interpreter.output(output)
        return ObjectDef.STATUS_PROCEED, None

    # (inputs target_variable) or (inputi target_variable) sets target_variable to input string/int
    def __execute_input(self, env, code, get_string):
        inp = self.interpreter.get_input()
        if get_string:
            val = Value(Type.STRING, inp)
        else:
            val = Value(Type.INT, int(inp))

        self.__set_variable_aux(env, code[1], val, code[0].line_num)
        return ObjectDef.STATUS_PROCEED, None

    # helper method used to set either parameter variables or member fields; parameters currently shadow
    # member fields
    def __set_variable_aux(self, env, var_name, value, line_num):
        # parameter shadows fields
        #print("set variable args", var_name, value, env.get(var_name),self.fields)
        if value.type() == Type.NOTHING:
            self.interpreter.error(
                ErrorType.TYPE_ERROR, "can't assign to nothing " + var_name, line_num
            )

        #checking all environment instances for our variable
        for i in range(len(env)-1, -1, -1):
            param_val = env[i].get(var_name)
            if param_val is not None:
                self.__set_type_check(param_val,value)
                env[i].set(var_name, value)
                return
                
        if var_name not in self.fields:
            self.interpreter.error(
                ErrorType.NAME_ERROR, "unknown variable " + var_name, line_num
            )
        
        self.__set_type_check(self.fields[var_name], value)
        self.fields[var_name] = value

    def __set_type_check(self, variable, value):
        if value.value() == None and variable.type() == Type.CLASS:
            pass
        elif variable.type() == Type.CLASS:
            if value.type() != Type.CLASS:
                return self.interpreter.error(ErrorType.TYPE_ERROR, "have to assign class x to class x ")
            else:
                #print(variable.class_name(),value.class_name())
                if variable.class_name() != value.class_name():
                    #here I have to accept any derived classes too
                    temp = Value(Type.CLASS, None)
                    temp.set(value)
                    while temp.value().parent_obj is not None:
                        if temp.value().parent_obj.value().get_name() == variable.class_name():
                            return
                        temp.set(temp.value().parent_obj)
                    #print(variable.class_name(),value.class_name())
                    return self.interpreter.error(ErrorType.TYPE_ERROR, "have to assign class x to class x or derived class ")
        elif variable.type() != value.type():
            return self.interpreter.error(ErrorType.TYPE_ERROR, "have to assign primitive x to primitive x ")
        

    # (if expression (statement) (statement) ) where expresion could be a boolean constant (e.g., true), member
    # variable without ()s, or a boolean expression in parens, like (> 5 a)
    def __execute_if(self, env, code):
        condition = self.__evaluate_expression(env, code[1], code[0].line_num)
        if condition.type() != Type.BOOL:
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "non-boolean if condition " + ' '.join(x for x in code[1]),
                code[0].line_num,
            )
        if condition.value():
            status, return_value = self.__execute_statement(
                env, code[2]
            )  # if condition was true
            return status, return_value
        if len(code) == 4:
            status, return_value = self.__execute_statement(
                env, code[3]
            )  # if condition was false, do else
            return status, return_value
        return ObjectDef.STATUS_PROCEED, None

    # (while expression (statement) ) where expresion could be a boolean value, boolean member variable,
    # or a boolean expression in parens, like (> 5 a)
    def __execute_while(self, env, code):
        while True:
            condition = self.__evaluate_expression(env, code[1], code[0].line_num)
            if condition.type() != Type.BOOL:
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "non-boolean while condition " + ' '.join(x for x in code[1]),
                    code[0].line_num,
                )
            if not condition.value():  # condition is false, exit loop immediately
                return ObjectDef.STATUS_PROCEED, None
            # condition is true, run body of while loop
            status, return_value = self.__execute_statement(env, code[2])
            if status == ObjectDef.STATUS_RETURN:
                return (
                    status,
                    return_value,
                )  # could be a valid return of a value or an error

    # given an expression, return a Value object with the expression's evaluated result
    # expressions could be: constants (true, 5, "blah"), variables (e.g., x), arithmetic/string/logical expressions
    # like (+ 5 6), (+ "abc" "def"), (> a 5), method calls (e.g., (call me foo)), or instantiations (e.g., new dog_class)
    def __evaluate_expression(self, env, expr, line_num_of_statement):
    
        if not isinstance(expr, list):
            # locals shadow member variables
            #searches through stack of environments
            for i in range(len(env)-1, -1, -1):
                val = env[i].get(expr)
                if val is not None:
                    return val
                
            if expr in self.fields:
                return self.fields[expr]
            # need to check for variable name and get its value too
            value = create_value(expr,"val")
            if value is not None:
                return value
            self.interpreter.error(
                ErrorType.NAME_ERROR,
                "invalid field or parameter " + expr,
                line_num_of_statement,
            )

        operator = expr[0]
        if operator in self.binary_op_list:
            operand1 = self.__evaluate_expression(env, expr[1], line_num_of_statement)
            operand2 = self.__evaluate_expression(env, expr[2], line_num_of_statement)
            if operand1.type() == operand2.type() and operand1.type() == Type.INT:
                if operator not in self.binary_ops[Type.INT]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to ints",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.INT][operator](operand1, operand2)
            if operand1.type() == operand2.type() and operand1.type() == Type.STRING:
                if operator not in self.binary_ops[Type.STRING]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to strings",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.STRING][operator](operand1, operand2)
            if operand1.type() == operand2.type() and operand1.type() == Type.BOOL:
                if operator not in self.binary_ops[Type.BOOL]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to bool",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.BOOL][operator](operand1, operand2)
            
            if operand1.type() == operand2.type() and operand1.type() == Type.CLASS:
                #TODO support derive check here as well
                if operand1.class_name() != None and operand2.class_name() != None:
                    if operand1.class_name() != operand2.class_name():
                        temp = Value(Type.CLASS, None)
                        
                        temp.set(operand2)
                        while temp.value().parent_obj is not None:
                            if temp.value().parent_obj.value().get_name() == operand1.class_name():
                               return self.binary_ops[Type.CLASS][operator](operand1, operand2)
                            temp.set(temp.value().parent_obj)

                        temp.set(operand1)
                        while temp.value().parent_obj is not None:
                            if temp.value().parent_obj.value().get_name() == operand2.class_name():
                               return self.binary_ops[Type.CLASS][operator](operand1, operand2)
                            temp.set(temp.value().parent_obj)
                         
                        return self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to class",
                        line_num_of_statement,
                    )

                if operator not in self.binary_ops[Type.CLASS]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to class",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.CLASS][operator](operand1, operand2)
            # error what about an obj reference and null
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                f"operator {operator} applied to two incompatible types",
                line_num_of_statement,
            )
        if operator in self.unary_op_list:
            operand = self.__evaluate_expression(env, expr[1], line_num_of_statement)
            if operand.type() == Type.BOOL:
                if operator not in self.unary_ops[Type.BOOL]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid unary operator applied to bool",
                        line_num_of_statement,
                    )
                return self.unary_ops[Type.BOOL][operator](operand)

        # handle call expression: (call objref methodname p1 p2 p3)
        if operator == InterpreterBase.CALL_DEF:
            return self.__execute_call_aux(env, expr, line_num_of_statement)
        # handle new expression: (new classname)
        if operator == InterpreterBase.NEW_DEF:
            return self.__execute_new_aux(env, expr, line_num_of_statement)

    # (new classname)
    def __execute_new_aux(self, _, code, line_num_of_statement):
        obj = self.interpreter.instantiate(code[1], line_num_of_statement)
        #print("instantiating new class", code[1])
        return Value(Type.CLASS, obj,class_name=code[1])

    # this method is a helper used by call statements and call expressions
    # (call object_ref/me methodname p1 p2 p3)
    def __execute_call_aux(self, env, code, line_num_of_statement):
        # determine which object we want to call the method on
        obj_name = code[1]
        if obj_name == InterpreterBase.ME_DEF:
            obj = self
        elif obj_name == InterpreterBase.SUPER_DEF:
            obj = self.parent_obj
            if obj is None:
                self.interpreter.error(
                ErrorType.NAME_ERROR, "method does not exist in parent ", line_num_of_statement
            )
            obj = obj.value()
        else:
            obj = self.__evaluate_expression(
                env, obj_name, line_num_of_statement
            ).value()
        # prepare the actual arguments for passing
        if obj is None:
            self.interpreter.error(
                ErrorType.FAULT_ERROR, "null dereference", line_num_of_statement
            )
        actual_args = []
        for expr in code[3:]:
            actual_args.append(
                self.__evaluate_expression(env, expr, line_num_of_statement)
            )
        return obj.call_method(code[2], actual_args, line_num_of_statement)

    def __map_method_names_to_method_definitions(self):
        self.methods = {}
        for method in self.class_def.get_methods():
            self.methods[method.method_name] = method

    def __map_fields_to_values(self):
        self.fields = {}
        for field in self.class_def.get_fields():
            self.fields[field.field_name] = field.field_value

    def __create_map_of_operations_to_lambdas(self):
        self.binary_op_list = [
            "+",
            "-",
            "*",
            "/",
            "%",
            "==",
            "!=",
            "<",
            "<=",
            ">",
            ">=",
            "&",
            "|",
        ]
        self.unary_op_list = ["!"]
        self.binary_ops = {}
        self.binary_ops[Type.INT] = {
            "+": lambda a, b: Value(Type.INT, a.value() + b.value()),
            "-": lambda a, b: Value(Type.INT, a.value() - b.value()),
            "*": lambda a, b: Value(Type.INT, a.value() * b.value()),
            "/": lambda a, b: Value(
                Type.INT, a.value() // b.value()
            ),  # // for integer ops
            "%": lambda a, b: Value(Type.INT, a.value() % b.value()),
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
            ">": lambda a, b: Value(Type.BOOL, a.value() > b.value()),
            "<": lambda a, b: Value(Type.BOOL, a.value() < b.value()),
            ">=": lambda a, b: Value(Type.BOOL, a.value() >= b.value()),
            "<=": lambda a, b: Value(Type.BOOL, a.value() <= b.value()),
        }
        self.binary_ops[Type.STRING] = {
            "+": lambda a, b: Value(Type.STRING, a.value() + b.value()),
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
            ">": lambda a, b: Value(Type.BOOL, a.value() > b.value()),
            "<": lambda a, b: Value(Type.BOOL, a.value() < b.value()),
            ">=": lambda a, b: Value(Type.BOOL, a.value() >= b.value()),
            "<=": lambda a, b: Value(Type.BOOL, a.value() <= b.value()),
        }
        self.binary_ops[Type.BOOL] = {
            "&": lambda a, b: Value(Type.BOOL, a.value() and b.value()),
            "|": lambda a, b: Value(Type.BOOL, a.value() or b.value()),
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
        }
        self.binary_ops[Type.CLASS] = {
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
        }

        self.unary_ops = {}
        self.unary_ops[Type.BOOL] = {
            "!": lambda a: Value(Type.BOOL, not a.value()),
        }
