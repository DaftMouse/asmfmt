import sys
import os
from enum import Enum
import json


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


def parse_file(file):
    t = Tokenizer(file)

    tok = t.next_token()
    while tok._type != TokenType.EOF:
        print(tok)
        tok = t.next_token()


def main(args):
    file = args[0]

    with open(file) as f:
        ast = parse_file(f)


if __name__ == '__main__':
    # Remove script name from argv and call main
    main(sys.argv[1:])
