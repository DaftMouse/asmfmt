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


class Token:
    def __init__(self, _type, ident=""):
        self._type = _type
        self.ident = ident

    def __str__(self):
        if self._type in [TokenType.IDENT, TokenType.NUMBER, TokenType.INSTRUCTION]:
            return f"{self._type}({self.ident})"

        return str(self._type)


class Tokenizer:
    def __init__(self, input_file):
        self.input_file = input_file
        self.cur_char = input_file.read(1)
        self.peek_char = input_file.read(1)

        ins_path = os.path.dirname(os.path.abspath(__file__))
        ins_path = os.path.join(ins_path, "instructions.json")
        with open(ins_path) as f:
            self.instruction_set = json.loads(f.read())

    def eat(self):
        """
        Replaces cur_char with peek_char and reads the next char into peek_char,
        if EOF is reached then peek_char is set to NULL
        """
        self.cur_char = self.peek_char
        c = self.input_file.read(1)
        if not c:
            self.peek_char = '\0'
        else:
            self.peek_char = c

    def is_instruction(self, ident):
        return ident.upper() in self.instruction_set

    def next_token(self):
        if self.cur_char == '\0':
            return Token(TokenType.EOF)
        elif self.cur_char == '\n':
            self.eat()
            return Token(TokenType.NEWLINE)

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
                return Token(TokenType.INSTRUCTION, ident)

            return Token(TokenType.IDENT, ident)

        # tokenize numbers
        if self.cur_char.isnumeric():
            # TODO: actually parse it into a number
            ident = ""
            while self.cur_char.isnumeric():
                ident += self.cur_char
                self.eat()

            return Token(TokenType.NUMBER, ident)

        # single char tokens
        tok = None
        match self.cur_char:
            case ':':
                tok = Token(TokenType.COLON)
            case ',':
                tok = Token(TokenType.COMMA)

        if tok:
            self.eat()
            return tok

        print(f"Unexpected {self.cur_char}")
        exit(1)


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

        return f"{self.instruction.ident} {ops}"


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
                print(f"Unexpected {self.cur_token}")
                exit(1)

        return expr

    def parse_instruction(self):
        # TODO
        ins = self.cur_token
        self.eat()

        operands = []
        while self.cur_token._type not in [TokenType.NEWLINE, TokenType.EOF]:
            operands.append(self.parse_expression())

            if self.cur_token._type == TokenType.COMMA:
                self.eat()

        return Instruction(ins.ident, operands)

    def parse_line(self):
        label = None
        instruction = None
        comment = None

        while True:
            match self.cur_token._type:
                case TokenType.IDENT:
                    label = self.cur_token
                    self.eat()
                case TokenType.INSTRUCTION:
                    instruction = self.parse_instruction()
                case TokenType.NEWLINE | TokenType.EOF:
                    self.eat()
                    break
                case _:
                    print(f"Unexpected token {self.cur_token}")
                    exit(1)

        return SourceLine(label, instruction, comment)

    def parse(self):
        lines = []
        while self.cur_token._type != TokenType.EOF:
            lines.append(self.parse_line())

        return lines


class Writer:
    def __init__(self, lines):
        self.lines = lines

    def format_instruction(self, instruction):
        return f"{instruction.instruction}"

    def format_expression(self, expr):
        return expr.format()

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

    def write_to_stdout(self):
        for l in self.lines:
            sys.stdout.write(self.format_line(l))
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
