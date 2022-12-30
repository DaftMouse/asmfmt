import sys

class Writer:
    def __init__(self, lines):
        self.lines = lines
        self.formatted_lines = []
        self.longest_line_length = 0

    def format_instruction(self, instruction):
        prefix = ""

        if instruction.prefix:
            prefix = instruction.prefix.ident
            prefix += " "

        return f"{prefix}{instruction.instruction}"

    def format_expression(self, expr):
        return expr.format()

    def format_lines(self):
        self.formatted_lines = []
        for l in self.lines:
            f = self.format_line(l)

            if len(f) > self.longest_line_length:
                self.longest_line_length = len(f)

            self.formatted_lines.append(f)

    def format_directive(self, directive):
        return f"[{directive.directive} {self.format_expression(directive.arg)}]"

    def format_line(self, line):
        formatted = ""

#        print(line)
        if line.directive:
            return self.format_directive(line.directive)

        if line.label:
            formatted += line.label
            formatted += ':'

            if len(line.label) >= 8:
                formatted += "  "
            else:
                formatted += " " * (8 - (len(line.label) + 1))

        else:
            formatted += " " * 8

        if line.instruction:
            ins_text = self.format_instruction(line.instruction)

            formatted += ins_text
            if len(ins_text) < 8:
                formatted += " " * (8 - len(ins_text))
            else:
                formatted += "  "

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
