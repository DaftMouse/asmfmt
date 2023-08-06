import sys
from .items import CodeLine


class Writer:
    def __init__(self, lines):
        self.lines = lines
        self.formatted_lines = []
        self.longest_line_length = 0

    def format_lines(self):
        self.formatted_lines = []
        for l in self.lines:
            f = l.format()

            if len(f) > self.longest_line_length:
                self.longest_line_length = len(f)

            self.formatted_lines.append(f)

    def add_comments(self):
        comment_col = self.longest_line_length + 2

        assert len(self.formatted_lines) == len(self.lines)

        for i in range(0, len(self.formatted_lines)):
            if not isinstance(self.lines[i], CodeLine) or not self.lines[i].comment:
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
