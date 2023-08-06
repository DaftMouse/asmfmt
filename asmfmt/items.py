class Directive:
    def __init__(self, directive, arg):
        self.directive = directive
        self.arg = arg

    def __str__(self):
        return f"Directive({self.directive}, [{self.arg}])"

    def format(self):
        return f"{self.directive} {self.arg.format()}"


class InstructionPrefix:
    def __init__(self, prefix):
        self.prefix = prefix

    def format(self):
        return self.prefix


class NASMTimesPrefix(InstructionPrefix):
    def __init__(self, arg):
        super().__init__("times")
        self.arg = arg

    def format(self):
        return f"times {self.arg.format()}"


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
            prefix = self.prefix.format()
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
        return self.directive.format()
