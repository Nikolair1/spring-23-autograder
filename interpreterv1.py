from bparser import BParser
from bparser import StringWithLineNumber
from intbase import InterpreterBase
from intbase import ErrorType
from enum import Enum

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
        self.fields = []
        self.methods = []
        self.name = ""
        self.int_base = int_base
        self.find_brewin_class_data(parsed_program)

    def print(self):
        print(self.name, self.fields, self.methods)

    def find_brewin_class_data(self, parsed_program):
        for class_def in parsed_program:
            if class_def[0] == "class":
                self.name = class_def[1]
                for item in class_def:
                    if item[0] == "field":
                        self.fields.append(item)
                    if item[0] == "method":
                        self.methods.append(item)
        
        
    def instantiate_object(self): 
        obj = ObjectDefinition(self.int_base)
        for method in self.methods:
            obj.add_method(method)
        for field in self.fields:
            obj.add_field(field)
        return obj     


class ObjectDefinition:
    def __init__(self,int_base):
        self.fields = []
        self.methods = []
        self.int_base = int_base

    def print(self):
        print(self.fields, self.methods)

    def add_field(self, field):
        self.fields.append(field)
    
    def add_method(self, method):
        self.methods.append(method)
    # Interpret the specified method using the provided parameters    
    def call_method(self, method_name):
        method = self.__find_method(method_name)
        b1 = BrewinMethod(self.int_base, method[1], method[2], method[3])        
        top_level_statement = b1.get_top_level_statement()
        result = statement_caller(self.int_base,top_level_statement)
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

def statement_caller(int_base, statement):
    if statement[0] == "":
            pass
    elif statement[0] == int_base.PRINT_DEF:
        statement = BrewinPrintStatement(int_base,statement[1:])
    elif statement[0] == int_base.IF_DEF:
        statement = BrewinIfStatement(int_base, statement[1:])

    return statement


class BrewinIfStatement:
    def __init__(self, int_base, args):
        self.int_base = int_base
        self.args = args
        self.__execute_if_statement(args)

    def __execute_if_statement(self,args):
        print(args)
        condition = evaluate_expression(self.int_base,args[0])
        if condition != self.int_base.TRUE_DEF and condition != self.int_base.FALSE_DEF:
            self.int_base.error(ErrorType.TYPE_ERROR)
        print(f"MADE IT, condition is: {condition}")

class BrewinPrintStatement:
    def __init__(self, int_base,args):
        self.args = args
        self.int_base = int_base
        self.__execute_print(args)

    def __execute_print(self,args):
        return_string = ""
        #print(args)
        if args[0] == '""':
            return
        for argument in args:
            if isinstance(argument,list):
                res = evaluate_expression(self.int_base,argument)
                return_string += str(res)
            elif argument.lstrip('-').isdigit():
                return_string += argument
            elif argument == self.int_base.TRUE_DEF or argument == self.int_base.FALSE_DEF:
                return_string += argument
            elif argument != '""':
                return_string+= (argument[1:-1]) 
        
        self.int_base.output(return_string)

def evaluate_expression(int_base,expression_list):
    #TODO:add an isinstance check to see if it's a variable name in our variable map
    #if it is, return the value of that variable
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
        operand1 = evaluate_expression(int_base,expression_list[1])
        operand2 = evaluate_expression(int_base,expression_list[2])
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
            return evaluate_expression(int_base,expression_list[1]) - evaluate_expression(int_base,expression_list[2])
        elif operator == '*':
            return evaluate_expression(int_base,expression_list[1]) * evaluate_expression(int_base,expression_list[2])
        elif operator == '/':
            return evaluate_expression(int_base,expression_list[1]) // evaluate_expression(int_base,expression_list[2])
        elif operator == '%':
            return evaluate_expression(int_base,expression_list[1]) % evaluate_expression(int_base,expression_list[2])
    elif operator in comparison_ops or operator in special_bool_ops:
        operand1 = evaluate_expression(int_base,expression_list[1])
        operand2 = evaluate_expression(int_base,expression_list[2])
        bool_check = False
        #print(f"OPERANDS ARE: {operand1} and {operand2}")
        #ERROR CHECKING, 1. FOR (1) Boolean Operand and (1) non boolean operand 2. For two operators that are both not strings or ints
        if (operand1 == int_base.TRUE_DEF or operand1 == 'false') and (operand2 != int_base.TRUE_DEF and operand2 != 'false'):
            int_base.error(ErrorType.TYPE_ERROR)
        if (operand2 == int_base.TRUE_DEF or operand2 == 'false') and (operand1 != int_base.TRUE_DEF and operand1 != 'false'):
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
                return int_base.TRUE_DEF if (operand1 == int_base.TRUE_DEF and operand2 == int_base.TRUE_DEF) else "false"
            elif operator == '|':
                return int_base.TRUE_DEF if (operand1 == int_base.TRUE_DEF or operand2 == int_base.TRUE_DEF) else "false"

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