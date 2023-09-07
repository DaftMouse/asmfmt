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

    def __str__(self):
        return str(self.prefix)

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

        p = ""
        if self.prefix:
            p += str(self.prefix) + " "

        return p + f"{self.instruction} {ops}"

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

class EffectiveAddressExpression:
    def __init__(self, _type, expr):
        self._type = _type
        self.expr = expr

    def __str__(self):
        return f"EffectiveAddressExpression({self._type}, {self.expr})"

class CharLiteralExpression(Expression):
    def __init__(self, char):
        self.char = char

    def __str__(self):
        return f"CharLiteralExpression({repr(self.char)})"

class BinaryExpression:
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return f"BinaryExpression({self.op}, {self.lhs}, {self.rhs})"
    
class UnaryExpression:
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def __str__(self):
        return f"UnaryExpression({self.op}, {self.expr})"

class ParenExpression:
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return f"ParenExpression({self.expr})"

class CodeLine:
    def __init__(self, label, instruction, comment):
        self.label = label
        self.instruction = instruction
        self.comment = comment

    def __str__(self):
        s = ""

        if self.label:
            s += self.label + ": "
        else:
            s += '\t'

        if self.instruction:
            s += str(self.instruction) + " "

        if self.comment:
            s += str(self.comment)

        return s

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

class MacroDefineLine:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return f"MacroDefine({self.name}, {self.value})"
        

class StructDefinition:
    def __init__(self, name: str, fields: [CodeLine]):
        self.name = name
        self.fields = fields

    def __str__(self):
        fields = map(lambda x: "\t" + str(x).strip(), self.fields)
        fields = ",\n".join(fields)
        return f"Struct({self.name},\n" \
            + fields \
            + "\n)"

class StructInstantiation:
    def __init__(self, name: str, fields: [(str, Instruction)]):
        self.name = name
        self.fields = fields

    def __str__(self):
        fields = map(lambda x: "\tat " + str(x[0]).strip() + ", " + str(x[1]), self.fields)
        fields = "\n".join(fields)
        return f"IStruct({self.name},\n" \
            + fields \
            + "\n)"
