"""TD5 String Literals and Comments, states 272-286 (+ shared 141, 149, 153, 192, 194)."""
import unittest

from lexer import tokenize
from tests.support import errors_of, pairs, types

ESCAPES = ['\\"', "\\'", "\\\\", "\\n", "\\t", "\\0"]


class Strings(unittest.TestCase):
    def test_empty_strings(self):
        self.assertEqual(pairs('""'), [("strina_lit", '""')])
        self.assertEqual(pairs("''"), [("strina_lit", "''")])

    def test_every_escape_in_both_quote_styles(self):
        for esc in ESCAPES:
            for q in ['"', "'"]:
                src = q + "a" + esc + "b" + q
                with self.subTest(src=src):
                    self.assertEqual(pairs(src), [("strina_lit", src)])

    def test_all_escapes_together(self):
        src = '"' + "".join(ESCAPES) + '"'
        self.assertEqual(pairs(src), [("strina_lit", src)])

    def test_invalid_escape(self):
        e = errors_of('"Hi\\x";')
        self.assertEqual(len(e), 1)
        self.assertIn("invalid escape sequence '\\x'", e[0].message)
        self.assertEqual(e[0].text, "\\x")
        self.assertEqual((e[0].line, e[0].column), (1, 4))
        tokens, _ = tokenize('"Hi\\x";')
        self.assertEqual([t.type for t in tokens], [";"])      # the bad literal is dropped, ';' still lexed

    def test_other_quote_inside_needs_no_escape(self):
        self.assertEqual(types('"it\'s"'), ["strina_lit"])
        self.assertEqual(types("'say \"hi\"'"), ["strina_lit"])

    def test_printable_ascii_and_tab_inside(self):
        body = "".join(chr(c) for c in range(32, 127) if chr(c) not in '"\\') + "\t"
        self.assertEqual(types('"' + body + '"'), ["strina_lit"])

    def test_unterminated_at_eof(self):
        e = errors_of('x = "Hello;')
        self.assertEqual(len(e), 1)
        self.assertIn("unterminated strina literal", e[0].message)
        self.assertEqual(e[0].column, 5)

    def test_unescaped_newline(self):
        e = errors_of('"Newline\nhere";')
        self.assertIn("raw newline", e[0].message)
        self.assertEqual(e[0].line, 1)

    def test_mismatched_quotes(self):
        self.assertIn("unterminated", errors_of("'AB\";")[0].message)
        self.assertIn("unterminated", errors_of("\"AB';")[0].message)

    def test_followers_in_delim_str(self):
        for follower in [" ", ";", ")", "]", "}", ",", ":", "+", "==", "("]:
            with self.subTest(follower=follower):
                self.assertEqual(types('"a"' + follower + " x")[0], "strina_lit")
        self.assertTrue(errors_of('"a"x'))
        self.assertTrue(errors_of('"a""b"'))

    def test_non_ascii_is_an_error(self):
        e = errors_of('"caf\u00e9";')
        self.assertEqual(len(e), 1)
        self.assertIn("only ASCII", e[0].message)


class SingleLineComments(unittest.TestCase):
    def test_comment_forms(self):
        self.assertEqual(pairs("-- single line comment"), [("comment_sl", "-- single line comment")])
        self.assertEqual(pairs("--"), [("comment_sl", "--")])
        self.assertEqual(pairs("---"), [("comment_sl", "---")])
        self.assertEqual(pairs("-- a --/ b"), [("comment_sl", "-- a --/ b")])

    def test_comment_ends_at_newline(self):
        self.assertEqual(pairs("-- c\nx"), [("comment_sl", "-- c"), ("id", "x")])
        self.assertEqual(pairs("--\nx"), [("comment_sl", "--"), ("id", "x")])

    def test_trailing_comment(self):
        self.assertEqual(types("x = 5; -- trailing comment"), ["id", "=", "wharfa_lit", ";", "comment_sl"])

    def test_stray_closer(self):
        e = errors_of("--/")
        self.assertEqual(len(e), 1)
        self.assertIn("without an opening '/--'", e[0].message)
        self.assertEqual(e[0].text, "--/")

    def test_skip_comments(self):
        self.assertEqual(types("x; -- c\ny;", skip_comments=True), ["id", ";", "id", ";"])


class MultiLineComments(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(pairs("/-- multi line comment --/"), [("comment_ml", "/-- multi line comment --/")])
        self.assertEqual(pairs("/----/"), [("comment_ml", "/----/")])

    def test_spans_lines_and_keeps_positions(self):
        tokens, errors = tokenize("/-- a\nb\nc --/ x")
        self.assertEqual(errors, [])
        self.assertEqual([(t.type, t.line, t.column) for t in tokens], [("comment_ml", 1, 1), ("id", 3, 7)])

    def test_first_closer_wins(self):
        # III.A.2.c: nested comments are not supported; the first --/ closes
        self.assertEqual(types("/-- nested /-- inner --/"), ["comment_ml"])
        tokens, errors = tokenize("/-- a /-- b --/ c --/")
        self.assertEqual([(t.type, t.lexeme) for t in tokens], [("comment_ml", "/-- a /-- b --/"), ("id", "c")])
        self.assertEqual(len(errors), 1)
        self.assertIn("without an opening", errors[0].message)

    def test_A2_dashes_inside(self):
        for src in ["/-- a-b --/", "/-- -x --/", "/-- --x --/", "/-- x ---/", "/-- x ----/", "/-- -/ --/"]:
            with self.subTest(src=src):
                self.assertEqual(pairs(src), [("comment_ml", src)])

    def test_unclosed(self):
        for src in ["/--", "/-- missing closer", "/-- x -", "/-- x --", "/---/", "/-- x -/"]:
            with self.subTest(src=src):
                e = errors_of(src)
                self.assertEqual(len(e), 1)
                self.assertIn("unterminated multi-line comment", e[0].message)

    def test_token_right_after_closer(self):
        self.assertEqual(types("/-- c --/x"), ["comment_ml", "id"])

    def test_skip_comments(self):
        self.assertEqual(types("/-- c --/ x", skip_comments=True), ["id"])


if __name__ == "__main__":
    unittest.main()
