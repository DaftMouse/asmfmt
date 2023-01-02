from asmfmt.token import Tokenizer, TokenType


class Directive:
    def __init__(self, directive, arg):
        self.directive = directive
        self.arg = arg

    def __str__(self):
        return f"Directive({self.directive}, [{self.arg}])"

    def format(self):
        return f"[{self.directive} {self.arg.format()}]"


class Instruction:
    def __init__(self, instruction, operands, prefix):
        self.instruction = instruction
        self.operands = operands
        self.prefix = prefix

    def __str__(self):
        # the __str__ method for lists calls __repr__ on the items instead
        # of __str__ so convert it here before passing it to the f string
        ops = []
        for op in self.operands:
            ops.append(str(op))

        return f"{self.instruction} {ops}"

    def format(self):
        prefix = ""

        if self.prefix:
            prefix = self.prefix.ident
            prefix += " "

        return f"{prefix}{self.instruction}"


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


class CodeLine:
    def __init__(self, label, instruction, comment):
        self.label = label
        self.instruction = instruction
        self.comment = comment

    def __str__(self):
        return f"{self.label}:\t{self.instruction}\t{self.comment}"

    def format(self):
        formatted = ""

        if self.label:
            formatted += self.label
            formatted += ':'

            if len(self.label) >= 8:
                formatted += "  "
            else:
                formatted += " " * (8 - (len(self.label) + 1))

        else:
            formatted += " " * 8

        if self.instruction:
            ins_text = self.instruction.format()

            formatted += ins_text
            if len(ins_text) < 8:
                formatted += " " * (8 - len(ins_text))
            else:
                formatted += "  "

            for i, op in enumerate(self.instruction.operands):
                formatted += op.format()

                if i + 1 < len(self.instruction.operands):
                    formatted += ", "

        return formatted


class DirectiveLine:
    def __init__(self, directive):
        self.directive = directive

    def format(self):
        return self.directive.format() + "\n"


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
        prefix = None
        if self.cur_token._type == TokenType.INSTRUCTION_PREFIX:
            prefix = self.cur_token
            self.eat()

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
