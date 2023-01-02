import sys

from asmfmt.parser import Parser
from asmfmt.writer import Writer


def main(args):
    file = args[0]

    with open(file) as f:
        p = Parser(f)
        lines = p.parse()
        w = Writer(lines)
        w.write_to_stdout()


if __name__ == '__main__':
    # Remove script name from argv and call main
    main(sys.argv[1:])
