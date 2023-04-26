from bparser import BParser
from bparser import StringWithLineNumber
from intbase import InterpreterBase



class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor

    def run(self, program):
        self.output("Hello world!")
        print("What's up?")
        result, parsed_program = BParser.parse(program)
        if result == False:
            print("Parsing failed. There must have been a mismatched parenthesis.")
            return
        self.__discover_all_classes_and_track_them(parsed_program)



    def __discover_all_classes_and_track_them(self, parsed_program):
        for class_def in parsed_program:
            self.__discover_class(class_def)


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
        print("Parsing failed. There must have been a mismatched parenthesis.")

#main()