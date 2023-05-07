from bparser import BParser
from bparser import StringWithLineNumber
from intbase import InterpreterBase
from intbase import ErrorType
from enum import Enum
import re
import copy

parsed_program = None
output_var = None

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBaseâ€™s constructor

    def run(self, program):
        global parsed_program
        lines = program
        numbered_lines = [StringWithLineNumber(line, i+1) for i, line in enumerate(lines)]
        result, parsed_program = BParser.parse(numbered_lines)
        #print(parsed_program)
        if result == False:
            print("Parsing failed. There must have been a mismatched parenthesis.")
            return
        class_manager_obj = self.__discover_all_classes_and_track_them(parsed_program)
        class_def = class_manager_obj.get_class_info(self.MAIN_CLASS_DEF)
        if class_def == None:
            self.error(ErrorType.TYPE_ERROR)
        #class_def.print()
        obj = class_def.instantiate_object()
        #print("OBJECT STUFF")
        #obj.print() 
        obj.call_method("main")


    def __discover_all_classes_and_track_them(self, parsed_program):
        class_manager = ClassManager(self,parsed_program)
        return class_manager
    
   
class Type(Enum):
  INT = 1
  BOOL = 2
  STRING = 3
  NULL = 4

class Value:
  def __init__(self, type, value = None):
    self.t = type
    self.v = value

  def value(self):
    return self.v

  def set(self, other):
    self.t = other.t
    self.v = other.v

  def type(self):
    return self.t

#tracks all classes
class ClassManager: 
  def __init__(self, int_base,parsed_program):
    self.int_base = int_base
    self.brewin_class_cache = {}
    self._cache_brewin_classes(parsed_program)

  #returns a Brewin Class Object
  def get_class_info(self, class_name):
    if class_name not in self.brewin_class_cache:
      return None
    return self.brewin_class_cache[class_name]

  def _cache_brewin_classes(self, parsed_program):
      for class_def in parsed_program:
            if class_def[1] in self.brewin_class_cache:
                self.int_base.error(ErrorType.TYPE_ERROR)
            self.brewin_class_cache[class_def[1]] = BrewinClass(self.int_base,class_def[1],parsed_program)
      #print(self.brewin_class_cache)

def validate_field(field):
    return bool(re.match(r'^[_a-zA-Z][_a-zA-Z0-9]*$', field))

class BrewinClass:
    def __init__(self,int_base,name,parsed_program):
        self.fields = {}
        self.methods = []
        self.name = name
        self.int_base = int_base
        self.main_exists = False
        self.name_set = set()
        self.find_brewin_class_data(parsed_program)
        if self.name == self.int_base.MAIN_CLASS_DEF and self.main_exists == False:
            self.int_base.error(ErrorType.NAME_ERROR)
        if len(self.name_set) == 0:
            self.int_base.error(ErrorType.NAME_ERROR)
        if validate_field(self.name) == False:
            self.int_base.error(ErrorType.NAME_ERROR)

    def print(self):
        print(self.name, self.fields, self.methods)

    def find_brewin_class_data(self, parsed_program):
        for class_def in parsed_program:
            if class_def[0] == self.int_base.CLASS_DEF:
                self.name = class_def[1]
                for item in class_def:
                    if item[0] == self.int_base.FIELD_DEF:
                        print(item)
                        if validate_field(item[1]):
                            if item[1] in self.fields:
                                self.int_base.error(ErrorType.NAME_ERROR)
                            else:
                                self.fields[item[1]] = create_value(self.int_base,item[2])
                                #print(self.fields[item[1]].value())
                        else:
                            self.int_base.error(ErrorType.NAME_ERROR)
                    if item[0] == self.int_base.METHOD_DEF:
                        if item[1] in self.name_set:
                            self.int_base.error(ErrorType.NAME_ERROR)
                        if item[1] == self.int_base.MAIN_FUNC_DEF:
                            self.main_exists = True
                        self.methods.append(item)
                        self.name_set.add(item[1])
                        
    
        
    def instantiate_object(self): 
        obj = ObjectDefinition(self.int_base, copy.deepcopy(self.fields))
        for method in self.methods:
            obj.add_method(method)
        #print("hi my methods are", self.methods)
        return obj     


def create_value(int_base,value):
    if isinstance(value, int):
        value = str(value)

    if isinstance(value, str):
        try:
            value = int(value)
            return Value(Type.INT, value)
        except:
            if value == '""':
                return Value(Type.STRING, "")
            if value == int_base.TRUE_DEF or value == int_base.FALSE_DEF:
                return Value(Type.BOOL, value)
            elif value == int_base.NULL_DEF:
                return Value(Type.NULL,value)
            else:
                return Value(Type.STRING, value)
    else:
        print(f"value is not a string or int: {value}")
        int_base.error(ErrorType.TYPE_ERROR)

class ObjectDefinition:
    def __init__(self,int_base,fields):
        self.fields = fields
        self.methods = []
        self.int_base = int_base

    def print(self):
        print(self.fields, self.methods)

    def modify_field(self, field, value):
        self.fields[field] = value
    
    def add_method(self, method):
        self.methods.append(method)
    # Interpret the specified method using the provided parameters    
    def call_method(self, method_name):
        method = self.__find_method(method_name)
        b1 = BrewinMethod(self.int_base, method[1], method[2], method[3])        
        top_level_statement, params = b1.get_top_level_statement()
        result = statement_caller(self.int_base,top_level_statement,self.fields,params)
        return result

    
    def __find_method(self, method_name):
        for method in self.methods:
            if method[1] == method_name:
                return method
        return None

def add_param(params, key, value):
    params.append((key, value))

def set_param_value(params, key, value):
    for i, (param_key, param_value) in enumerate(params):
        if param_key == key:
            params[i] = (key, value)
            break

def has_key(params, key):
    for param_key, param_value in params:
        if param_key == key:
            return True
    return False

def get_value(params, key):
    for param_key, param_value in params:
        if param_key == key:
            return param_value
    return None


class BrewinMethod:
    def __init__(self, int_base,name, params, statement):
        self.name = name
        self.params = [(key, None) for key in params]
        self.statement = statement
        self.int_base = int_base
        #print(self.name, self.params, self.statement)
        #print("NAME ",self.name, "PARAMS ", self.params, "STATEMENT ",self.statement)

    def get_top_level_statement(self):
        return (self.statement, self.params)

def statement_caller(int_base, statement,fields,params):
    if statement[0] == "":
            pass
    elif statement[0] == int_base.PRINT_DEF:
        statement = BrewinPrintStatement(int_base,statement[1:],fields,params)
        #print(f"PRINT STATEMENT RESULT: {statement.get_return_string()}")
    elif statement[0] == int_base.IF_DEF:
        statement = BrewinIfStatement(int_base, statement[1:],fields,params)
    elif statement[0] == int_base.BEGIN_DEF:
        statement = BrewinBeginStatement(int_base, statement[1:],fields,params)
    elif statement[0] == int_base.INPUT_INT_DEF or statement[0] == int_base.INPUT_STRING_DEF:
        statement = BrewinInputiStatement(int_base, statement[1:],fields,params)
    elif statement[0] == int_base.SET_DEF:
        statement = BrewinSetStatement(int_base, statement[1:],fields,params)
    elif statement[0] == int_base.WHILE_DEF:
        statement = BrewinWhileStatement(int_base, statement[1:],fields,params)
    elif statement[0] == int_base.CALL_DEF:
        statement = BrewinCallStatement(int_base, statement[1:],fields,params)
    elif statement[0] == int_base.RETURN_DEF:
        statement = BrewinReturnStatement(int_base, statement[1:],fields,params)

    return statement

class BrewinBeginStatement:
    def __init__(self, int_base, args,fields,params):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.params = params
        self.__execute_begin_statement(args)

    def __execute_begin_statement(self,args):
        for statement in args:
            #print("IN BEGIN")
            #print(statement)
            evaluate_expression(self.int_base,statement,self.fields,self.params)
        
class BrewinWhileStatement:
    def __init__(self, int_base, args,fields,params):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.params = params
        self.__execute_while_statement(args)

    def __execute_while_statement(self,args):
        condition = evaluate_expression(self.int_base,args[0],self.fields,self.params)
        if condition != self.int_base.TRUE_DEF and condition != self.int_base.FALSE_DEF:
            self.int_base.error(ErrorType.TYPE_ERROR)
        while condition == self.int_base.TRUE_DEF:
            for statement in args[1:]:
                evaluate_expression(self.int_base,statement,self.fields,self.params)
            condition = evaluate_expression(self.int_base,args[0],self.fields,self.params)

class BrewinInputiStatement:
    def __init__(self, int_base, args,fields,params):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.params = params
        self.__execute_inputi_statement(args)

    def __execute_inputi_statement(self,args):
        if args[0] not in self.fields:
            self.int_base.error(ErrorType.NAME_ERROR)
        else:
            self.fields[args[0]] = create_value(self.int_base,self.int_base.get_input())

class BrewinSetStatement:
    def __init__(self, int_base, args,fields,params):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.params = params
        self.__execute_set_statement(args)

    def __execute_set_statement(self,args):
        #print("HERE",args)
        if has_key(self.params,args[0]):
            if isinstance(args[1], list):
                val = evaluate_expression(self.int_base,args[1],self.fields,self.params)
                #print("Val from expression",val)
                set_param_value(self.params,args[0],create_value(self.int_base,val))
                #print(args[0],self.params[args[0]].value())
            else:
                set_param_value(self.params,args[0],create_value(self.int_base,args[1]))
            return

        if args[0] not in self.fields:
            self.int_base.error(ErrorType.NAME_ERROR)
        else:
            if isinstance(args[1],list):
                val = evaluate_expression(self.int_base,args[1],self.fields,self.params)
                self.fields[args[0]] = create_value(self.int_base,val)
            else:
                self.fields[args[0]] = create_value(self.int_base,args[1])

class BrewinIfStatement:
    def __init__(self, int_base, args,fields,params):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.params = params
        self.__execute_if_statement(args)

    def __execute_if_statement(self,args):
        condition = evaluate_expression(self.int_base,args[0],self.fields,self.params)
        if condition != self.int_base.TRUE_DEF and condition != self.int_base.FALSE_DEF:
            self.int_base.error(ErrorType.TYPE_ERROR)
        if condition == self.int_base.TRUE_DEF:
            statement = args[1]
            status = evaluate_expression(self.int_base,statement,self.fields,self.params)
        else:
            if len(args) > 2:
                statement = args[2]
                status = evaluate_expression(self.int_base,statement,self.fields,self.params)
        
class BrewinPrintStatement:
    def __init__(self, int_base,args,fields,params):
        self.args = args
        self.int_base = int_base
        self.fields = fields
        self.params = params
        self.return_string = self.__execute_print(args)
    

    def get_return_string(self):
        return self.return_string
    
    def __execute_print(self,args):
        global output_var
        return_string = ""
        #print(args)
        if args[0] == '""':
            return
        for argument in args:
            #check for potential field
            if not isinstance(argument,list):
                if has_key(self.params,argument):
                    argument = str(get_value(self.params,argument).value())
                elif argument in self.fields:
                    argument = str(self.fields[argument].value())
    
                #print(f"ARGUMENT IS {argument}")
           

            if isinstance(argument,list):
                print("calling call here")
                res = evaluate_expression(self.int_base,argument,self.fields,self.params)
                if isinstance(res, BrewinCallStatement):
                    res = output_var
                print("res is",res)
                return_string += str(res)
            elif argument.lstrip('-').isdigit():
                return_string += argument
            elif argument == self.int_base.TRUE_DEF or argument == self.int_base.FALSE_DEF:
                return_string += argument
            elif argument != '""':
                if argument[0] == '\"' and argument[-1] == '\"':
                    return_string+= (argument[1:-1]) 
                else:
                    return_string += argument
        
        self.int_base.output(return_string)
        return return_string

class BrewinCallStatement:
    def __init__(self, int_base, args,fields,params):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.params = []
        self.object_definition = ObjectDefinition(self.int_base,fields)
        self.method = None
        self.statement = None
        self.__execute_call_statement(args)

    def __execute_call_statement(self,args):
        global parsed_program
        global output_var
        #print("What's up")
        #print(parsed_program)
        func_name = args[1]
        func_args = args[2:]
        for class_def in parsed_program:
            if class_def[0] == self.int_base.CLASS_DEF:
                for item in class_def:
                    if item[0] == self.int_base.METHOD_DEF:
                        if item[1] == func_name:
                            self.method = item

        if self.method == None:
            self.int_base.error(ErrorType.NAME_ERROR)
        for item in self.method[2]:
            add_param(self.params,item, create_value(self.int_base,0))
        self.statement = self.method[3]
        if len(func_args) != len(self.params):
            self.int_base.error(ErrorType.TYPE_ERROR)

        for i in range(len(self.params)):
            if isinstance(func_args[i],list):
                val = evaluate_expression(self.int_base,func_args[i],self.fields,self.params)
                set_param_value(self.params,self.params[i][0],create_value(self.int_base,val))
            else:
                set_param_value(self.params,self.params[i][0],create_value(self.int_base,func_args[i]))

        #for (x,y) in self.params:
            #print("updated param: ",x,y.value())
        #print(func_name,func_args,self.statement,self.params)
        result = statement_caller(self.int_base,self.statement,self.fields,self.params)
        print("result from call IS ",result)
        if isinstance(result, BrewinReturnStatement):
            return output_var
        return result

class BrewinReturnStatement:
    def __init__(self, int_base, args,fields,params):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.params = params
        self.output = None
        self.__execute_return_statement()

    def output(self):
        return self.output
    
    def __execute_return_statement(self):
        global output_var
        print("heyo")
        print(self.args)
        z = evaluate_expression(self.int_base,self.args[0],self.fields,self.params)
        print(z)
        self.output = z
        output_var = z
        return z



def evaluate_expression(int_base,expression_list,fields,params):

    if not isinstance(expression_list,list):
        if has_key(params,expression_list):
            expression_list =  str(get_value(params,expression_list).value())
        elif expression_list in fields:
            expression_list =  str(fields[expression_list].value())

    if isinstance(expression_list, str):  # base case: if the expression_list is a string, return it as an integer
        try:
            return int(expression_list)
        except ValueError:
            #print(f"Expression list is {expression_list}")
            if expression_list == int_base.TRUE_DEF or expression_list == int_base.FALSE_DEF or expression_list == int_base.NULL_DEF:
                return expression_list
            else:
                if expression_list[0] == '\"' and expression_list[-1] == '\"':
                    return expression_list[1:-1] 
                return expression_list
    
    if (expression_list[0] == int_base.RETURN_DEF) or expression_list[0] == int_base.CALL_DEF:
        return statement_caller(int_base, expression_list,fields,params)

    if (expression_list[0] == int_base.PRINT_DEF or expression_list[0] == int_base.BEGIN_DEF or expression_list[0] == int_base.IF_DEF 
        or expression_list[0] == int_base.INPUT_INT_DEF or expression_list[0] == int_base.INPUT_STRING_DEF or 
        expression_list[0] == int_base.SET_DEF or expression_list[0] == int_base.WHILE_DEF):
        statement_caller(int_base, expression_list,fields,params)
        return 
    
    
    
        
    operator = expression_list[0]
    string_int_ops = ['+', '-', '*', '/','%']
    comparison_ops = ['==', '!=', '<', '>', '<=', '>=']
    special_bool_ops = ['&', '|']
    if operator in string_int_ops:
        operand1 = evaluate_expression(int_base,expression_list[1],fields,params)
        operand2 = evaluate_expression(int_base,expression_list[2],fields,params)
        if operand1 == int_base.TRUE_DEF or operand1 == int_base.FALSE_DEF or operand2 == int_base.TRUE_DEF or operand2 == int_base.FALSE_DEF:
            int_base.error(ErrorType.TYPE_ERROR)
        elif not ((isinstance(operand1, str) and isinstance(operand2, str)) or
              (isinstance(operand1, int) and isinstance(operand2, int))):
                int_base.error(ErrorType.TYPE_ERROR)
        if operator == '+':
            #print(f"OPERANDS ARE: {operand1} and {operand2}")
            if isinstance(operand1, str) and isinstance(operand2, str):
                return (operand1 + operand2)
            else:
                return operand1 + operand2
        if (isinstance(operand1, str) or isinstance(operand2, str)):
                int_base.error(ErrorType.TYPE_ERROR)
        elif operator == '-':
            return evaluate_expression(int_base,expression_list[1],fields,params) - evaluate_expression(int_base,expression_list[2],fields,params)
        elif operator == '*':
            return evaluate_expression(int_base,expression_list[1],fields,params) * evaluate_expression(int_base,expression_list[2],fields,params)
        elif operator == '/':
            return evaluate_expression(int_base,expression_list[1],fields,params) // evaluate_expression(int_base,expression_list[2],fields,params)
        elif operator == '%':
            return evaluate_expression(int_base,expression_list[1],fields,params) % evaluate_expression(int_base,expression_list[2],fields,params)
    elif operator in comparison_ops or operator in special_bool_ops:
        operand1 = evaluate_expression(int_base,expression_list[1],fields,params)
        operand2 = evaluate_expression(int_base,expression_list[2],fields,params)
        bool_check = False
        #print(f"OPERANDS ARE: {operand1} and {operand2}")
        #print(f"operator 1 type is int {isinstance(operand1, int)}, operator 2 type is int {isinstance(operand2, int)}")
        #ERROR CHECKING, 1. FOR (1) Boolean Operand and (1) non boolean operand 2. For two operators that are both not strings or ints
        if (operand1 == int_base.TRUE_DEF or operand1 == int_base.FALSE_DEF) and (operand2 != int_base.TRUE_DEF and operand2 != int_base.FALSE_DEF):
            int_base.error(ErrorType.TYPE_ERROR)
        if (operand2 == int_base.TRUE_DEF or operand2 == int_base.FALSE_DEF) and (operand1 != int_base.TRUE_DEF and operand1 != int_base.FALSE_DEF):
            int_base.error(ErrorType.TYPE_ERROR)
        elif not ((isinstance(operand1, str) and isinstance(operand2, str)) or
              (isinstance(operand1, int) and isinstance(operand2, int))):
                int_base.error(ErrorType.TYPE_ERROR)


                
        if operand1 == int_base.TRUE_DEF or operand1 == int_base.FALSE_DEF:
            bool_check = True

        #These should only be run on two bools
        if operator in special_bool_ops:
            if not bool_check:
                int_base.error(ErrorType.TYPE_ERROR)
            if operator == '&':
                return int_base.TRUE_DEF if (operand1 == int_base.TRUE_DEF and operand2 == int_base.TRUE_DEF) else int_base.FALSE_DEF
            elif operator == '|':
                return int_base.TRUE_DEF if (operand1 == int_base.TRUE_DEF or operand2 == int_base.TRUE_DEF) else int_base.FALSE_DEF

        #These can be run on either bools or strings or ints or nulls
        if operator == '==':
            if (operand1 == int_base.NULL_DEF and operand2 != int_base.NULL_DEF) or (operand1 != int_base.NULL_DEF and operand2 == int_base.NULL_DEF):
                int_base.error(ErrorType.TYPE_ERROR)
            return int_base.TRUE_DEF if operand1 == operand2 else int_base.FALSE_DEF
        elif operator == '!=':
            return int_base.TRUE_DEF if operand1 != operand2 else int_base.FALSE_DEF
        
        #These can only be run on ints and strings
        
        if operator == '<':
            if bool_check:
                int_base.error(ErrorType.TYPE_ERROR)
            return int_base.TRUE_DEF if operand1 < operand2 else int_base.FALSE_DEF
        elif operator == '>':
            if bool_check:
                int_base.error(ErrorType.TYPE_ERROR)
            return int_base.TRUE_DEF if operand1 > operand2 else int_base.FALSE_DEF
        elif operator == '<=':
            if bool_check:
                int_base.error(ErrorType.TYPE_ERROR)
            return int_base.TRUE_DEF if operand1 <= operand2 else int_base.FALSE_DEF
        elif operator == '>=':
            if bool_check:
                int_base.error(ErrorType.TYPE_ERROR)
            return int_base.TRUE_DEF if operand1 >= operand2 else int_base.FALSE_DEF



def main():

    # program_source = ['(class main',
    #                 ' (method main ()',
    #                 '   (print "hello world!")',
    #                 ' ) # end of method',
    #                 ') # end of class']
    program_source = ['(class main',
                      ' (field num 0)',
                      '(field result 1)',
                      '(method main()',
                      '(begin',
                        '(print "Enter a number: ")',
                        '(inputi num)',
                        '(print num " factorial is " (call me factorial num))))',
                      '(method factorial (n)',
                        '(begin',
                            '(set result 1)',
                            '(while (> n 0)',
                            '(begin',
                                '(set result (* n result))',
                                '(set n (- n 1))))',
                            '(return result))))']

    lines = program_source
    numbered_lines = [StringWithLineNumber(line, i+1) for i, line in enumerate(lines)]
    result, parsed_program = BParser.parse(numbered_lines)

    if result:
        print(parsed_program)


#main()