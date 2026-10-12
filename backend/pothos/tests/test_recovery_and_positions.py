"""Line/column tracking, error recovery, and the tokenize() API."""
import unittest

from lexer import LexicalError, Token, tokenize


class Positions(unittest.TestCase):
    def test_line_and_column_of_every_token(self):
        tokens, errors = tokenize("x = 1;\n  prin(x);\n\ty")
        self.assertEqual(errors, [])
        self.assertEqual([(t.lexeme, t.line, t.column) for t in tokens], [
            ("x", 1, 1), ("=", 1, 3), ("1", 1, 5), (";", 1, 6),
            ("prin", 2, 3), ("(", 2, 7), ("x", 2, 8), (")", 2, 9), (";", 2, 10),
            ("y", 3, 2),                                   # a tab counts as one column
        ])

    def test_token_record(self):
        tokens, _ = tokenize("wharfa")
        self.assertEqual(tokens[0], Token("wharfa", "wharfa", 1, 1))


class Recovery(unittest.TestCase):
    SOURCE = (
        "ok1 = 1;\n"
        "studentRegistrationNumber2026 = 1;\n"
        "x = 100000000;\n"
        "_age = 2; total$ = 3;\n"
        'bad = "Hi\\x";\n'
        "ok2 = 2;\n"
        '/-- never closed\n'
    )

    def test_one_run_reports_every_error(self):
        tokens, errors = tokenize(self.SOURCE)
        self.assertEqual([(e.line, e.column) for e in errors], [(2, 1), (3, 5), (4, 1), (4, 11), (5, 10), (7, 1)])
        self.assertTrue(all(isinstance(e, LexicalError) for e in errors))

    def test_lexing_continues_after_errors(self):
        tokens, _ = tokenize(self.SOURCE)
        lexemes = [t.lexeme for t in tokens]
        self.assertIn("ok1", lexemes)
        self.assertIn("ok2", lexemes)
        self.assertEqual(lexemes.count(";"), 7)

    def test_offending_text_is_reported(self):
        _, errors = tokenize(self.SOURCE)
        self.assertEqual([e.text for e in errors][:4], ["studentRegistrationNumber2026", "100000000", "_age", "total$"])

    def test_error_format(self):
        _, errors = tokenize("\n\n      abcdefghijklmnopqrstuvwxyz = 1;")
        self.assertEqual(str(errors[0]),
                         "Lexical Error [line 3, col 7]: identifier exceeds 20 characters (III.B.3): "
                         "'abcdefghijklmnopqrstuvwxyz'")

    def test_invalid_characters_at_state_0(self):
        for ch in ["$", "@", "#", "?", ".", "&", "|", "^", "~", "`", "\\", "\u00e9", "\r"]:
            with self.subTest(ch=ch):
                tokens, errors = tokenize(f"a {ch} b")
                self.assertEqual(len(errors), 1)
                self.assertEqual([t.lexeme for t in tokens], ["a", "b"])

    def test_empty_and_blank_sources(self):
        self.assertEqual(tokenize(""), ([], []))
        self.assertEqual(tokenize(" \n\t\n"), ([], []))


if __name__ == "__main__":
    unittest.main()
