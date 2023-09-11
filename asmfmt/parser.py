import traceback

from .token import Tokenizer, TokenType, Token, UnexpectedCharException
from .items import *


class SyntaxErrorException(Exception):
    def __init__(self, expected: TokenType, got: Token):
        super().__init__(f"Expected {expected}, got {got} at {got.location}")

class Parser:
    def __init__(self, input_file):
        self.tokenizer = Tokenizer(input_file)
        self.cur_token = self.tokenizer.next_token()
        self.peek_token = self.tokenizer.next_token()
        self.parsed_lines = []

    def eat(self):
        self.cur_token = self.peek_token
        self.peek_token = self.tokenizer.next_token()

    def expect(self, token_type: TokenType):
        if not self.cur_token.is_type(token_type):
            raise SyntaxErrorException(token_type, self.cur_token)

    def parse_effective_address(self):
        assert self.cur_token.is_type(TokenType.OPEN_BRACKET)
        self.eat() # [
        value = self.parse_expression()
        self.expect(TokenType.CLOSE_BRACKET)
        self.eat() # ]

        return value

    def parse_expression(self):
        lhs = None

        match self.cur_token._type:
            case TokenType.IDENT:
                ident = self.cur_token.ident

                if ident.lower() in ["byte", "word", "dword", "qword"]:
                    self.eat()
                    self.expect(TokenType.OPEN_BRACKET)
                    addr = self.parse_effective_address()
                    lhs = EffectiveAddressExpression(ident, addr)
                else:
                    lhs = IdentExpression(ident)
                    self.eat()
            case TokenType.OPEN_BRACKET:
                addr = self.parse_effective_address()
                lhs = EffectiveAddressExpression(None, addr)
            case TokenType.NUMBER:
                lhs = NumberExpression(self.cur_token.ident)
                self.eat()
            case TokenType.CHAR_LITERAL:
                lhs = CharLiteralExpression(self.cur_token.ident)
                self.eat()
            case TokenType.MINUS:
                self.eat()
                expr = self.parse_expression()
                lhs = UnaryExpression(TokenType.MINUS, expr)
            case TokenType.OPEN_PAREN:
                self.eat()
                expr = self.parse_expression()
                self.expect(TokenType.CLOSE_PAREN)
                self.eat()

                lhs = ParenExpression(expr)
            case TokenType.STRING_LITERAL:
                lhs = StringLiteralExpression(self.cur_token.ident)
                self.eat()
            case TokenType.DOLLAR_SIGN:
                lhs = IdentExpression("$")
                self.eat()
            case TokenType.DOUBLE_DOLLAR_SIGN:
                lhs = IdentExpression("$$")
                self.eat()
            case _:
                raise SyntaxErrorException("expression", self.cur_token)

        if self.cur_token._type in [TokenType.MINUS,
                                    TokenType.PLUS,
                                    TokenType.FORWARD_SLASH,
                                    TokenType.SHIFT_LEFT,
                                    TokenType.BITWISE_OR]:
            op = self.cur_token
            self.eat()
            rhs = self.parse_expression()
            return BinaryExpression(op, lhs, rhs)

        return lhs

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

    def parse_macro(self):
        self.eat() # %
        self.expect(TokenType.IDENT)

        match self.cur_token.ident:
            case "define":
                self.eat() # define

                self.expect(TokenType.IDENT)
                name = self.cur_token.ident
                self.eat()

                value = self.parse_expression()
                return MacroDefineLine(name, value)
            case "assign":
                self.eat() # assign

                self.expect(TokenType.IDENT)
                name = self.cur_token.ident
                self.eat()

                expr = self.parse_expression()
                return AssignMacro(name, expr)

        return None

    def parse_code_line(self):
        assert self.cur_token._type in [TokenType.IDENT, \
                                        TokenType.INSTRUCTION, \
                                        TokenType.INSTRUCTION_PREFIX, \
                                        TokenType.COMMENT]
        
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
        
        return CodeLine(label, instruction, comment)

    def parse_istruc(self):
        assert self.cur_token.is_type(TokenType.IDENT) \
               and self.cur_token.ident == "istruc"
        self.eat()

        self.expect(TokenType.IDENT)
        name = self.cur_token.ident
        self.eat()

        self.expect(TokenType.NEWLINE)
        self.eat()

        def endstruc():
            return self.cur_token.is_type(TokenType.IDENT) \
                and self.cur_token.ident == "iend"
        
        fields = []
        while not endstruc(): 
            self.expect(TokenType.IDENT)
            if self.cur_token.ident != "at":
                raise SyntaxErrorException("at", self.cur_token)

            self.eat()
            self.expect(TokenType.IDENT)
            field = self.cur_token.ident
            self.eat()

            self.expect(TokenType.COMMA)
            self.eat()

            data_definition = self.parse_instruction()

            self.expect(TokenType.NEWLINE)
            self.eat()
            
            fields.append((field, data_definition))

        self.eat() # endstruc

        return StructInstantiation(name, fields)

    def parse_struc(self):
        assert self.cur_token.is_type(TokenType.IDENT) \
               and self.cur_token.ident == "struc"
        self.eat()

        self.expect(TokenType.IDENT)
        name = self.cur_token.ident
        self.eat()

        self.expect(TokenType.NEWLINE)
        self.eat()

        def endstruc():
            return self.cur_token.is_type(TokenType.IDENT) \
                and self.cur_token.ident == "endstruc"
        
        fields = []
        while not endstruc(): 
            line = self.parse_line()
            fields.append(line)

        self.eat() # endstruc

        return StructDefinition(name, fields)

    def parse_line(self):
        # Empty line
        if self.cur_token.is_type(TokenType.NEWLINE):
            self.eat()
            return CodeLine(None, None, None)

        line = None
        
        match self.cur_token._type:
            case TokenType.PERCENT:
                line = self.parse_macro()
            case TokenType.DIRECTIVE:
                line = self.parse_directive()
            case TokenType.IDENT:
                match self.cur_token.ident:
                    case "struc":
                        line = self.parse_struc()
                    case "istruc":
                        line = self.parse_istruc()
                    case _:
                        line = self.parse_code_line()
            case _:
                line = self.parse_code_line()

        self.expect(TokenType.NEWLINE)
        self.eat()

        return line


    def parse(self):
        lines = []
        while not self.cur_token.is_type(TokenType.EOF):

            try:
                l = self.parse_line()
                lines.append(l)
            except SyntaxErrorException as e:
                lines.append("ERROR: " + str(e) + "\n" + traceback.format_exc())
                return lines
            except UnexpectedCharException as e:
                lines.append("ERROR: " + str(e) + "\n" + traceback.format_exc())
                return lines

        return lines
