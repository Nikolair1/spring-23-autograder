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
        print(parsed_program)
        if result == False:
            print("Parsing failed. There must have been a mismatched parenthesis.")
            return
        self.__discover_all_classes_and_track_them(parsed_program)


    def __discover_all_classes_and_track_them(self, parsed_program):
        class_manager = ClassManager(self,parsed_program)
    

    


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
    if class_name not in self.class_cache:
      return None
    return self.class_cache[class_name]

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

    def find_brewin_class_data(self, parsed_program):
        for class_def in parsed_program:
            if class_def[0] == "class":
                self.name = class_def[1]
                for item in class_def:
                    if item[0] == "field":
                        self.fields.append(item)
                    if item[0] == "method":
                        self.methods.append(BrewinMethod(self.int_base,item[1], item[2], item[3]))
                          

class BrewinMethod:
    def __init__(self, int_base,name, params, statement):
        self.name = name
        self.params = params
        self.statement = statement
        self.int_base = int_base
        #print(self.name, self.params, self.statement)
        if self.statement == "":
            pass
        elif self.statement[0] == 'print':
           
            self.statement = BrewinPrintStatement(int_base,self.statement[1:])
        #print("NAME ",self.name, "PARAMS ", self.params, "STATEMENT ",self.statement)

class BrewinPrintStatement:
    def __init__(self, int_base,args):
        self.args = args
        self.int_base = int_base
        self.__execute_print(args)

    def __execute_print(self,args):
        if args[0] != '""':
            self.int_base.output(self.args[0][1:-1])
        

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


    """ if result:
        #print(parsed_program)
        for class_def in parsed_program:
            print(f"I am a class '{class_def[1]}'")
            for item in class_def:
                if item[0] == 'field':
                    print(f"I am a field '{item[1]}' with value '{item[2]}'")
                    print(f"Line number: {item[0].line_num}")
                    #print("HI")
                elif item[0] == 'method':
                    name = item[1]
                    print(f"I am a method '{name}'")
                    params = item[2]
                    print(f"I have {len(params)} parameters")
                    print(f"Line number: {item[0].line_num}")
    else:
        print("Parsing failed. There must have been a mismatched parenthesis.") """

#main()