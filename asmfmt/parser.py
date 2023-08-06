from .token import Tokenizer, TokenType
from .items import *

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

    def parse_prefix(self):
        if self.cur_token.ident.upper() == "TIMES":
            self.eat()
            arg = self.parse_expression()
            return NASMTimesPrefix(arg)

        prefix = self.cur_token.ident
        self.eat()
        return InstructionPrefix(prefix)

    def parse_instruction(self):
        prefix = None
        if self.cur_token._type == TokenType.INSTRUCTION_PREFIX:
            prefix = self.parse_prefix()

        ins = self.cur_token
        self.eat()

        # no operands
        if self.cur_token._type in [TokenType.NEWLINE, TokenType.COMMENT]:
            return Instruction(ins.ident, [], prefix)

        operands = []
        operands.append(self.parse_expression())
        while self.cur_token._type == TokenType.COMMA:
            self.eat()
            operands.append(self.parse_expression())

        return Instruction(ins.ident, operands, prefix)

    def parse_directive(self):
        self.eat()  # [

        if self.cur_token._type != TokenType.IDENT:
            print(
                f"Expected identifier, found {self.cur_token} at {self.cur_token.location}")
            exit(1)

        directive = self.cur_token.ident
        self.eat()

        arg = self.parse_expression()

        if self.cur_token._type != TokenType.CLOSE_BRACKET:
            print(
                f"Expected ] found {self.cur_token} at {self.cur_token.location}")

        self.eat()  # ]
        return Directive(directive, arg)

    def parse_line(self):
        if self.cur_token._type == TokenType.OPEN_BRACKET:
            d = self.parse_directive()

            # Putting this in an if here because I'm not sure
            # if a newline is required by NASM after a directive
            if self.cur_token._type == TokenType.NEWLINE:
                self.eat()

            return DirectiveLine(d)
        elif self.cur_token._type == TokenType.NEWLINE:
            self.eat()
            return CodeLine(None, None, None)

        label = None
        if self.cur_token._type == TokenType.IDENT:
            label = self.cur_token.ident

            self.eat()
            if self.cur_token._type == TokenType.COLON:
                self.eat()

        instruction = None
        if self.cur_token._type in [TokenType.INSTRUCTION, TokenType.INSTRUCTION_PREFIX]:
            instruction = self.parse_instruction()

        comment = None
        if self.cur_token._type == TokenType.COMMENT:
            comment = Comment(self.cur_token.ident)
            self.eat()

        if self.cur_token._type == TokenType.NEWLINE:
            self.eat()

        if label is None and comment is None and instruction is None:
            print(
                f"Unexpected token {self.cur_token} at {self.cur_token.location}")
            exit(1)

        return CodeLine(label, instruction, comment)

    def parse(self):
        lines = []
        while self.cur_token._type != TokenType.EOF:
            l = self.parse_line()
            lines.append(l)

        return lines
