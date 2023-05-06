from bparser import BParser
from bparser import StringWithLineNumber
from intbase import InterpreterBase
from intbase import ErrorType
from enum import Enum
import re
import copy

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor

    def run(self, program):
        lines = program
        numbered_lines = [StringWithLineNumber(line, i+1) for i, line in enumerate(lines)]
        result, parsed_program = BParser.parse(numbered_lines)
        #print(parsed_program)
        if result == False:
            print("Parsing failed. There must have been a mismatched parenthesis.")
            return
        class_manager_obj = self.__discover_all_classes_and_track_them(parsed_program)
        class_def = class_manager_obj.get_class_info("main")
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
            self.brewin_class_cache[class_def[1]] = BrewinClass(self.int_base,parsed_program)
      #print(self.brewin_class_cache)

class BrewinClass:
    def __init__(self,int_base,parsed_program):
        self.fields = {}
        self.methods = []
        self.name = ""
        self.int_base = int_base
        self.find_brewin_class_data(parsed_program)

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
                        else:
                            self.int_base.error(ErrorType.NAME_ERROR)
                    if item[0] == self.int_base.METHOD_DEF:
                        self.methods.append(item)
        
        
    def instantiate_object(self): 
        obj = ObjectDefinition(self.int_base, copy.deepcopy(self.fields))
        for method in self.methods:
            obj.add_method(method)
        return obj     

def validate_field(field):
    return bool(re.match(r'^[_a-zA-Z][_a-zA-Z0-9]*$', field))

def create_value(int_base,value):
    if isinstance(value, int):
        value = str(value)

    if isinstance(value, str):
        try:
            value = int(value)
            return Value(Type.INT, value)
        except:
            if value == int_base.TRUE_DEF or value == int_base.FALSE_DEF:
                return Value(Type.BOOL, value)
            elif value == int_base.NULL_DEF:
                return Value(Type.NULL)
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
        top_level_statement = b1.get_top_level_statement()
        result = statement_caller(self.int_base,top_level_statement,self.fields)
        return result

    
    def __find_method(self, method_name):
        for method in self.methods:
            if method[1] == method_name:
                return method
        return None
  
class BrewinMethod:
    def __init__(self, int_base,name, params, statement):
        self.name = name
        self.params = params
        self.statement = statement
        self.int_base = int_base
        #print(self.name, self.params, self.statement)
        #print("NAME ",self.name, "PARAMS ", self.params, "STATEMENT ",self.statement)

    def get_top_level_statement(self):
        return self.statement

def statement_caller(int_base, statement,fields):
    if statement[0] == "":
            pass
    elif statement[0] == int_base.PRINT_DEF:
        statement = BrewinPrintStatement(int_base,statement[1:],fields)
        #print(f"PRINT STATEMENT RESULT: {statement.get_return_string()}")
    elif statement[0] == int_base.IF_DEF:
        statement = BrewinIfStatement(int_base, statement[1:],fields)
    elif statement[0] == int_base.BEGIN_DEF:
        statement = BrewinBeginStatement(int_base, statement[1:],fields)
    elif statement[0] == int_base.INPUT_INT_DEF or statement[0] == int_base.INPUT_STRING_DEF:
        statement = BrewinInputiStatement(int_base, statement[1:],fields)

    return statement

class BrewinBeginStatement:
    def __init__(self, int_base, args,fields):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.__execute_begin_statement(args)

    def __execute_begin_statement(self,args):
        for statement in args:
            evaluate_expression(self.int_base,statement,self.fields)
        
class BrewinInputiStatement:
    def __init__(self, int_base, args,fields):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.__execute_inputi_statement(args)

    def __execute_inputi_statement(self,args):
        print("HI in here")
        if args[0] not in self.fields:
            self.int_base.error(ErrorType.NAME_ERROR)
        else:
            self.fields[args[0]] = create_value(self.int_base,self.int_base.get_input())


class BrewinIfStatement:
    def __init__(self, int_base, args,fields):
        self.int_base = int_base
        self.args = args
        self.fields = fields
        self.__execute_if_statement(args)

    def __execute_if_statement(self,args):
        condition = evaluate_expression(self.int_base,args[0],self.fields)
        if condition != self.int_base.TRUE_DEF and condition != self.int_base.FALSE_DEF:
            self.int_base.error(ErrorType.TYPE_ERROR)
        if condition == self.int_base.TRUE_DEF:
            statement = args[1]
            status = evaluate_expression(self.int_base,statement,self.fields)
        else:
            if len(args) > 2:
                statement = args[2]
                status = evaluate_expression(self.int_base,statement,self.fields)
        print(status)

class GlobalPrint:
    def __init__(self, int_base):
        self.int_base = int_base
        self.return_string = ""
    
    def add_to_return_string(self, string):
        self.return_string += string
    
    def __execute_print(self):
        self.int_base.output(self.return_string)

class BrewinPrintStatement:
    def __init__(self, int_base,args,fields):
        self.args = args
        self.int_base = int_base
        self.fields = fields
        self.return_string = self.__execute_print(args)
    

    def get_return_string(self):
        return self.return_string
    
    def __execute_print(self,args):
        return_string = ""
        #print(args)
        if args[0] == '""':
            return
        for argument in args:
            #check for potential field
            if not isinstance(argument,list):
                if argument in self.fields:
                    argument = str(self.fields[argument].value())
                    #print(f"ARGUMENT IS {argument}")

            if isinstance(argument,list):
                res = evaluate_expression(self.int_base,argument,self.fields)
                return_string += str(res)
            elif argument.lstrip('-').isdigit():
                return_string += argument
            elif argument == self.int_base.TRUE_DEF or argument == self.int_base.FALSE_DEF:
                return_string += argument
            elif argument != '""':
                return_string+= (argument[1:-1]) 
        
        self.int_base.output(return_string)
        return return_string

def evaluate_expression(int_base,expression_list,fields):
    #TODO:add an isinstance check to see if it's a variable name in our variable map
    #if it is, return the value of that variable
    if not isinstance(expression_list,list):
        if expression_list in fields:
            expression_list =  str(fields[expression_list].value())
   
    if (expression_list[0] == int_base.PRINT_DEF or expression_list[0] == int_base.BEGIN_DEF or expression_list[0] == int_base.IF_DEF 
        or expression_list[0] == int_base.INPUT_INT_DEF or expression_list[0] == int_base.INPUT_STRING_DEF):
        statement_caller(int_base, expression_list,fields)
        return 
    
    
    if isinstance(expression_list, str):  # base case: if the expression_list is a string, return it as an integer
        try:
            return int(expression_list)
        except ValueError:
            #print(f"Expression list is {expression_list}")
            if expression_list == int_base.TRUE_DEF or expression_list == int_base.FALSE_DEF:
                return expression_list
            else:
                return expression_list[1:-1]
        
    operator = expression_list[0]
    string_int_ops = ['+', '-', '*', '/','%']
    comparison_ops = ['==', '!=', '<', '>', '<=', '>=']
    special_bool_ops = ['&', '|']
    if operator in string_int_ops:
        operand1 = evaluate_expression(int_base,expression_list[1],fields)
        operand2 = evaluate_expression(int_base,expression_list[2],fields)
        if operand1 == int_base.TRUE_DEF or operand1 == int_base.FALSE_DEF or operand2 == int_base.TRUE_DEF or operand2 == int_base.FALSE_DEF:
            int_base.error(ErrorType.TYPE_ERROR)
        elif not ((isinstance(operand1, str) and isinstance(operand2, str)) or
              (isinstance(operand1, int) and isinstance(operand2, int))):
                int_base.error(ErrorType.TYPE_ERROR)
        if operator == '+':
            return operand1 + operand2
        if (isinstance(operand1, str) or isinstance(operand2, str)):
                int_base.error(ErrorType.TYPE_ERROR)
        elif operator == '-':
            return evaluate_expression(int_base,expression_list[1],fields) - evaluate_expression(int_base,expression_list[2],fields)
        elif operator == '*':
            return evaluate_expression(int_base,expression_list[1],fields) * evaluate_expression(int_base,expression_list[2],fields)
        elif operator == '/':
            return evaluate_expression(int_base,expression_list[1],fields) // evaluate_expression(int_base,expression_list[2],fields)
        elif operator == '%':
            return evaluate_expression(int_base,expression_list[1],fields) % evaluate_expression(int_base,expression_list[2],fields)
    elif operator in comparison_ops or operator in special_bool_ops:
        operand1 = evaluate_expression(int_base,expression_list[1],fields)
        operand2 = evaluate_expression(int_base,expression_list[2],fields)
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

        #These can be run on either bools or strings or ints
        if operator == '==':
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