from enum import Enum
import json
import os

class UnexpectedCharException(Exception):
    def __init__(self, unexpected_char: str, location: (int, int)):
        super().__init__(f"Unexpected {unexpected_char} at line {location[0]}, col {location[1]}")

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
    INSTRUCTION_PREFIX = "INSTRUCTION_PREFIX"
    DIRECTIVE = "DIRECTIVE"
    PERCENT = 'PERCENT'


class Token:
    def __init__(self, _type, location, ident=""):
        self._type = _type
        self.ident = ident
        self.location = location

    def __str__(self):
        if self._type in [TokenType.IDENT, TokenType.NUMBER, TokenType.INSTRUCTION]:
            return f"{self._type}({self.ident})"

        return str(self._type)

    def is_type(self, _type: TokenType) -> bool:
        return self._type == _type


class Tokenizer:
    def __init__(self, input_file):
        self.input_file = input_file
        self.cur_char = input_file.read(1)
        self.peek_char = input_file.read(1)
        self.cur_line = 1
        self.cur_col = 0

        ins_path = os.path.dirname(os.path.abspath(__file__))
        ins_path = os.path.join(ins_path, "..", "instructions.json")
        with open(ins_path) as f:
            j = json.loads(f.read())
            self.instruction_set = j["instructions"] + j["nasm_instructions"]
            self.prefix_set = j["prefixes"] + j["nasm_prefixes"]
            self.directive_set = j["directives"]

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

    def is_instruction_prefix(self, ident):
        return ident.upper() in self.prefix_set

    def is_directive(self, ident):
        return ident.upper() in self.directive_set

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
            self.eat()  # d | h | q | o | b | y

        return self.make_token(TokenType.NUMBER, ident)

    def is_ident_stater(self, char):
        return char.isalpha() or char == '.'

    def is_ident_char(self, char):
        return char.isalnum() or char == '_'

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
        if self.is_ident_stater(self.cur_char):
            ident = ""
            ident += self.cur_char
            self.eat()

            while self.is_ident_char(self.cur_char):
                ident += self.cur_char
                self.eat()

            if self.is_instruction(ident):
                return self.make_token(TokenType.INSTRUCTION, ident)
            elif self.is_instruction_prefix(ident):
                return self.make_token(TokenType.INSTRUCTION_PREFIX, ident)
            elif self.is_directive(ident):
                return self.make_token(TokenType.DIRECTIVE, ident)

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
            case '%':
                tok = self.make_token(TokenType.PERCENT)

        # tokenize comments
        if self.cur_char == ';':
            comment = ""
            self.eat()  # ;

            # Skip whitespaces between ; and start of comment
            # FIXME: this might break some fancy multiline comments that
            # build some sort of ascii art to explain things, the way to
            # avoid that would be having special coments that can turn the
            # formatter on/off like clang-format's // clang-format on/off
            while self.cur_char == ' ':
                self.eat()

            while self.cur_char != '\n':
                comment += self.cur_char
                self.eat()

            tok = self.make_token(TokenType.COMMENT, comment)
            return tok

        if tok:
            self.eat()
            return tok

        raise UnexpectedCharException(self.cur_char, (self.cur_line, self.cur_col))
