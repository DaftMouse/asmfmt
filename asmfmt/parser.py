from .token import Tokenizer, TokenType, Token
from .items import *


class SyntaxErrorException(Exception):
    def __init__(self, unexpected_token: Token):
        super().__init__(f"Unexpected token {unexpected_token} at {unexpected_token.location}")

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
                raise SyntaxErrorException(self.cur_token)

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
        if self.cur_token.is_type(TokenType.INSTRUCTION_PREFIX):
            prefix = self.parse_prefix()

        ins = self.cur_token
        self.eat()

        # no operands
        if self.cur_token.is_type(TokenType.NEWLINE) or self.cur_token.is_type(TokenType.COMMENT):
            return Instruction(ins.ident, [], prefix)

        operands = []
        operands.append(self.parse_expression())
        while self.cur_token.is_type(TokenType.COMMA):
            self.eat()
            operands.append(self.parse_expression())

        return Instruction(ins.ident, operands, prefix)

    def parse_directive(self):
        assert self.cur_token.is_type(TokenType.DIRECTIVE)

        directive = self.cur_token.ident
        self.eat()

        arg = self.parse_expression()

        return Directive(directive, arg)

    def parse_line(self):
        if self.cur_token.is_type(TokenType.DIRECTIVE):
            return self.parse_directive()
        
        if self.cur_token.is_type(TokenType.NEWLINE):
            self.eat()
            return CodeLine(None, None, None)

        label = None
        if self.cur_token.is_type(TokenType.IDENT):
            label = self.cur_token.ident

            self.eat()
            if self.cur_token.is_type(TokenType.COLON):
                self.eat()

        instruction = None
        if self.cur_token.is_type(TokenType.INSTRUCTION) or self.cur_token.is_type(TokenType.INSTRUCTION_PREFIX):
            instruction = self.parse_instruction()

        comment = None
        if self.cur_token.is_type(TokenType.COMMENT):
            comment = Comment(self.cur_token.ident)
            self.eat()

        if self.cur_token.is_type(TokenType.NEWLINE):
            self.eat()

        if label is None and comment is None and instruction is None:
            raise SyntaxErrorException(self.cur_token)

        return CodeLine(label, instruction, comment)

    def parse(self):
        lines = []
        while not self.cur_token.is_type(TokenType.EOF):
            l = self.parse_line()
            lines.append(l)

        return lines
