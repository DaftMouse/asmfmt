import sys
import os
from enum import Enum
import json
import math


class TokenType(Enum):
    IDENT = "IDENT"
    COMMA = "COMMA"
    COLON = "COLON"
    NUMBER = "NUMBER"
    INSTRUCTION = "INSTRUCTION"
    NEWLINE = "NEWLINE"
    EOF = "EOF"
    OPEN_BRACKET = "OPEN_BRACKET"
    CLOSE_BRACKET = "CLOSE_BRACKET"
    COMMENT = "COMMENT"

class Token:
    def __init__(self, _type, location, ident=""):
        self._type = _type
        self.ident = ident
        self.location = location

    def __str__(self):
        if self._type in [TokenType.IDENT, TokenType.NUMBER, TokenType.INSTRUCTION]:
            return f"{self._type}({self.ident})"

        return str(self._type)


class Tokenizer:
    def __init__(self, input_file):
        self.input_file = input_file
        self.cur_char = input_file.read(1)
        self.peek_char = input_file.read(1)
        self.cur_line = 1
        self.cur_col = 0

        ins_path = os.path.dirname(os.path.abspath(__file__))
        ins_path = os.path.join(ins_path, "instructions.json")
        with open(ins_path) as f:
            self.instruction_set = json.loads(f.read())

    def eat(self):
        """
        Replaces cur_char with peek_char and reads the next char into peek_char,
        if EOF is reached then peek_char is set to NULL
        """
        if self.cur_char == '\n':
            self.cur_line += 1
            self.cur_col = 0
        else:
            self.cur_col += 1

        self.cur_char = self.peek_char
        c = self.input_file.read(1)
        if not c:
            self.peek_char = '\0'
        else:
            self.peek_char = c

    def is_instruction(self, ident):
        return ident.upper() in self.instruction_set

    def current_location(self):
        return (self.cur_line, self.cur_col)

    def make_token(self, _type, ident=""):
        return Token(_type, self.current_location(), ident)

    def tokenize_number(self):
        ident = ""

        # $0 prefix
        if self.cur_char == '$' and self.peek_char == '0':
            ident += self.cur_char + self.peek_char
            self.eat()  # $
            self.eat()  # 0

        # prefix
        if self.cur_char == '0' and self.peek_char in ['d', 'x', 'h', 'o', 'q', 'b', 'y']:
            ident += self.cur_char + self.peek_char
            self.eat()  # 0
            self.eat()  # d | x | h | o | q | b | y

        while self.cur_char.isnumeric() or self.cur_char.upper() in ['A', 'B', 'C', 'D', 'E', 'F', '_']:
            ident += self.cur_char
            self.eat()

        # postfix
        if self.cur_char in ['d', 'h', 'q', 'o', 'b', 'y']:
            ident += self.cur_char
            self.eat()  #  d | h | q | o | b | y

        return self.make_token(TokenType.NUMBER, ident)

    def next_token(self):
        if self.cur_char == '\0':
            return self.make_token(TokenType.EOF)
        elif self.cur_char == '\n':
            self.eat()
            return self.make_token(TokenType.NEWLINE)

        # skip whitespaces
        while self.cur_char.isspace():
            self.eat()

        # tokenize identifiers and instructions
        if self.cur_char.isalpha():
            ident = ""
            while self.cur_char.isalnum():
                ident += self.cur_char
                self.eat()

            if self.is_instruction(ident):
                return self.make_token(TokenType.INSTRUCTION, ident)

            return self.make_token(TokenType.IDENT, ident)

        # tokenize numbers
        if self.cur_char.isnumeric() or (self.cur_char == '$' and self.peek_char == '0'):
            return self.tokenize_number()

        # single char tokens
        tok = None
        match self.cur_char:
            case ':':
                tok = self.make_token(TokenType.COLON)
            case ',':
                tok = self.make_token(TokenType.COMMA)
            case '[':
                tok = self.make_token(TokenType.OPEN_BRACKET)
            case ']':
                tok = self.make_token(TokenType.CLOSE_BRACKET)

        # comments
        if self.cur_char == ';':
            comment = ""
            self.eat()  # ;
            while self.cur_char != '\n':
                comment += self.cur_char
                self.eat()

            tok =  self.make_token(TokenType.COMMENT, comment)
            self.eat()  # \n
            return tok

        if tok:
            self.eat()
            return tok

        print(
            f"Unexpected {self.cur_char} on line {self.cur_line}, col {self.cur_col}")
        exit(1)


class Directive:
    def __init__(self, directive, args):
        self.directive = directive
        self.args = args

    def __str__(self):
        args = []
        for a in self.args:
            args.append(str(a))

        return f"Directive({self.directive}, [{args}])"


class Instruction:
    def __init__(self, instruction, operands):
        self.instruction = instruction
        self.operands = operands

    def __str__(self):
        # the __str__ method for lists calls __repr__ on the items instead
        # of __str__ so convert it here before passing it to the f string
        ops = []
        for op in self.operands:
            ops.append(str(op))

        return f"{self.instruction} {ops}"

class Comment:
    def __init__(self, comment):
        self.comment = comment

    def __str__(self):
        return f"Comment({self.comment})"

    def format(self):
        return f"; {self.comment}"

class Expression:
    def format(self):
        raise NotImplementedError


class IdentExpression(Expression):
    def __init__(self, ident):
        self.ident = ident

    def __str__(self):
        return f"IdentExpression({self.ident})"

    def format(self):
        return self.ident


class NumberExpression(Expression):
    def __init__(self, number):
        self.number = number

    def __str__(self):
        return f"NumberExpression({self.number})"

    def format(self):
        return self.number


class SourceLine:
    def __init__(self, label, instruction, comment):
        self.label = label
        self.instruction = instruction
        self.comment = comment

    def __str__(self):
        return f"{self.label}:\t{self.instruction}\t{self.comment}"


class Parser:
    def __init__(self, input_file):
        self.tokenizer = Tokenizer(input_file)
        self.cur_token = self.tokenizer.next_token()
        self.peek_token = self.tokenizer.next_token()
        self.parsed_lines = []

    def eat(self):
        self.cur_token = self.peek_token
        self.peek_token = self.tokenizer.next_token()

    def parse_expression(self):
        expr = None

        match self.cur_token._type:
            case TokenType.IDENT:
                expr = IdentExpression(self.cur_token.ident)
                self.eat()
            case TokenType.NUMBER:
                expr = NumberExpression(self.cur_token.ident)
                self.eat()
            case _:
                print(
                    f"Unexpected token {self.cur_token} at {self.cur_token.location}")
                exit(1)

        return expr

    def parse_instruction(self):
        # TODO
        ins = self.cur_token
        self.eat()

        # no operands
        if self.cur_token._type in [TokenType.NEWLINE, TokenType.COMMENT]:
            return Instruction(ins.ident, [])

        operands = []
        operands.append(self.parse_expression())
        while self.cur_token._type == TokenType.COMMA:
            self.eat()
            operands.append(self.parse_expression())

        return Instruction(ins.ident, operands)

    def parse_directive(self):
        self.eat()  # [

        if self.cur_token._type != TokenType.IDENT:
            print(
                f"Expected identifier, found {self.cur_token} at {self.cur_token.location}")
            exit(1)

        directive = self.cur_token.ident
        self.eat()

        args = []
        while self.cur_token._type not in [TokenType.CLOSE_BRACKET, TokenType.EOF, TokenType.NEWLINE]:
            args.append(self.cur_token)
            self.eat()

        self.eat()  # ]
        return Directive(directive, args)

    def parse_line(self):
        if self.cur_token._type == TokenType.OPEN_BRACKET:
            d = self.parse_directive()

            # Putting this in an if here because I'm not sure
            # if a newline is required by NASM after a directive
            if self.cur_token._type == TokenType.NEWLINE:
                self.eat()

            return d

        instruction = None
        if self.cur_token._type == TokenType.INSTRUCTION:
            instruction = self.parse_instruction()

        comment = None
        if self.cur_token._type == TokenType.COMMENT:
            comment = Comment(self.cur_token.ident)
            self.eat()

        if self.cur_token._type == TokenType.NEWLINE:
            self.eat()

        if not instruction and not comment:
            print(f"Unexpected token {self.cur_token} at {self.cur_token.location}")
            exit(1)

        return SourceLine(None, instruction, comment)

    def parse(self):
        lines = []
        while self.cur_token._type != TokenType.EOF:
            l = self.parse_line()
            lines.append(l)

        return lines


class Writer:
    def __init__(self, lines):
        self.lines = lines
        self.formatted_lines = []
        self.longest_line_length = 0

    def format_instruction(self, instruction):
        return f"{instruction.instruction}"

    def format_expression(self, expr):
        return expr.format()

    def format_lines(self):
        self.formatted_lines = []
        for l in self.lines:
            f = self.format_line(l)

            if len(f) > self.longest_line_length:
                self.longest_line_length = len(f)

            self.formatted_lines.append(f)

    def format_line(self, line):
        formatted = " " * 8

        if line.instruction:
            ins_text = self.format_instruction(line.instruction)

            formatted += ins_text
            formatted += " " * (8 - len(ins_text))

            for i, op in enumerate(line.instruction.operands):
                formatted += self.format_expression(op)

                if i + 1 < len(line.instruction.operands):
                    formatted += ", "

        return formatted

    def add_comments(self):
        comment_col = self.longest_line_length + 2

        assert len(self.formatted_lines) == len(self.lines)

        for i in range(0, len(self.formatted_lines)):
            if not self.lines[i].comment:
                continue

            extra_spaces = comment_col - len(self.formatted_lines[i])
            extra_spaces = ' ' * extra_spaces
            self.formatted_lines[i] += extra_spaces

            self.formatted_lines[i] += self.lines[i].comment.format()

    def write_to_stdout(self):
        self.format_lines()
        self.add_comments()

        for l in self.formatted_lines:
            sys.stdout.write(l)
            sys.stdout.write('\n')


def main(args):
    file = args[0]

    with open(file) as f:
        p = Parser(f)
        lines = p.parse()
        w = Writer(lines)
        w.write_to_stdout()


if __name__ == '__main__':
    # Remove script name from argv and call main
    main(sys.argv[1:])
