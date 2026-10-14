"""
main.py - terminal front end for the Pothos lexer.

    python main.py program.pths            lex a file
    python main.py program.pths --no-comments
    python main.py program.pths --trace    also show the TD state path of each token
    python main.py                         interactive prompt

The lexer itself lives in the `lexer` package and has no terminal code, so a
graphical front end can call lexer.tokenize(source) directly.
"""
import argparse
import sys

from lexer import Lexer

MAX_LEXEME = 40      # longer lexemes (usually comments) are shortened in the table


def show_lexeme(text):
    shown = text.replace("\n", "\\n").replace("\t", "\\t")
    return shown if len(shown) <= MAX_LEXEME else shown[:MAX_LEXEME - 3] + "..."


def print_table(tokens):
    rows = [(str(t.line), str(t.column), show_lexeme(t.lexeme), t.type) for t in tokens]
    head = ("Line", "Col", "Lexeme", "Token")
    widths = [max([len(head[i])] + [len(r[i]) for r in rows]) for i in range(4)]

    def fmt(r):
        return (f"{r[0]:>{widths[0]}} | {r[1]:>{widths[1]}} | "
                f"{r[2]:<{widths[2]}} | {r[3]:<{widths[3]}}").rstrip()

    print(fmt(head))
    print("-+-".join("-" * w for w in widths))
    for r in rows:
        print(fmt(r))


def print_errors(errors):
    if not errors:
        print("No lexical errors.")
        return
    print(f"{len(errors)} lexical error{'s' if len(errors) != 1 else ''}:")
    for e in errors:
        print(f"  {e}")


def print_trace(paths):
    print("State paths (TD state numbers; * / ** = retract 1 / 2; restart->196 = restart as identifier):")
    for line, col, text, path in paths:
        print(f"  [{line}:{col}] {show_lexeme(text)!r}: {path}")


def lex_and_report(source, skip_comments, trace):
    lexer = Lexer(source, skip_comments=skip_comments, trace=trace)
    tokens, errors = lexer.run()
    print_table(tokens)
    print()
    if trace:
        print_trace(lexer.paths)
        print()
    print_errors(errors)
    return tokens, errors


def interactive(skip_comments, trace):
    print("Pothos lexer - interactive mode")
    print("Type Pothos code. An empty line lexes what you typed. Type :quit to exit.")
    buffer = []
    while True:
        try:
            line = input("pothos> " if not buffer else "   ...> ")
        except EOFError:
            print()
            line = ":quit"
        if line.strip() == ":quit":
            if buffer:
                lex_and_report("\n".join(buffer), skip_comments, trace)
            return 0
        if line == "" and buffer:
            print()
            lex_and_report("\n".join(buffer), skip_comments, trace)
            print()
            buffer = []
        elif line != "":
            buffer.append(line)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pothos lexical analyzer")
    parser.add_argument("file", nargs="?", help="Pothos source file (.pths); omit for the interactive prompt")
    parser.add_argument("--no-comments", action="store_true", help="do not list comment tokens")
    parser.add_argument("--trace", action="store_true", help="show the TD state path of every token")
    args = parser.parse_args(argv)

    if args.file is None:
        return interactive(args.no_comments, args.trace)

    try:
        # Text mode turns Windows line endings (\r\n) into \n.
        with open(args.file, encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError as exc:
        print(f"Cannot read {args.file}: {exc.strerror}", file=sys.stderr)
        return 2

    _, errors = lex_and_report(source, args.no_comments, args.trace)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
