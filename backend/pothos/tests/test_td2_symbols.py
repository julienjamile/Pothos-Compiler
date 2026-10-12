"""TD2 Reserved Symbols, states 137-195."""
import unittest

from lexer.tokens import RESERVED_SYMBOLS
from tests.support import errors_of, pairs, types


class EverySymbol(unittest.TestCase):
    def test_each_symbol_followed_by_space(self):
        for sym in RESERVED_SYMBOLS:
            with self.subTest(sym=sym):
                self.assertEqual(pairs(sym + " "), [(sym, sym)])

    def test_each_symbol_at_end_of_file(self):
        # every symbol delimiter set includes delim_space, which includes eof
        for sym in RESERVED_SYMBOLS:
            with self.subTest(sym=sym):
                self.assertEqual(pairs(sym), [(sym, sym)])

    def test_two_character_operators_win(self):
        self.assertEqual(types("a <= b >= c == d != e"), ["id", "<=", "id", ">=", "id", "==", "id", "!=", "id"])
        self.assertEqual(types("a += 1; a -= 1; a *= 1; a /= 1; a %= 1;"),
                         ["id", "+=", "wharfa_lit", ";", "id", "-=", "wharfa_lit", ";",
                          "id", "*=", "wharfa_lit", ";", "id", "/=", "wharfa_lit", ";",
                          "id", "%=", "wharfa_lit", ";"])
        self.assertEqual(types("x+=1"), ["id", "+=", "wharfa_lit"])


class Delimiters(unittest.TestCase):
    def test_operand_follows_operators(self):
        self.assertEqual(types("a+b"), ["id", "+", "id"])
        self.assertEqual(types("a*(b)"), ["id", "*", "(", "id", ")"])
        self.assertEqual(types('a+"s"'), ["id", "+", "strina_lit"])
        self.assertEqual(types("x=-5"), ["id", "=", "wharfa_lit"])            # '-' is in delim_operand (E3)
        self.assertEqual(types("a<-5"), ["id", "<", "wharfa_lit"])

    def test_invalid_follower_is_error(self):
        for src in ["a ++ b", "a +) b", "a =) b", "x === y", "a *; b", "a <) b"]:
            with self.subTest(src=src):
                self.assertTrue(errors_of(src))

    def test_bang_needs_equals(self):
        self.assertEqual(types("a != b"), ["id", "!=", "id"])
        e = errors_of("!a")
        self.assertEqual(len(e), 1)
        self.assertIn("'!' must be followed by '='", e[0].message)

    def test_grouping(self):
        self.assertEqual(types("f()"), ["id", "(", ")"])
        self.assertEqual(types("[]"), ["[", "]"])
        self.assertEqual(types("{}"), ["{", "}"])
        self.assertEqual(types("a[0][1]"), ["id", "[", "wharfa_lit", "]", "[", "wharfa_lit", "]"])
        self.assertEqual(types("){"), [")", "{"])
        self.assertTrue(errors_of("(;"))                      # ';' is not in delim_open_paren

    def test_terminator_uses_delim_term(self):
        self.assertEqual(types("x;y"), ["id", ";", "id"])
        self.assertEqual(types("};"), ["}", ";"])
        self.assertEqual(types("a;-- c"), ["id", ";", "comment_sl"])
        self.assertEqual(types("a;/-- c --/"), ["id", ";", "comment_ml"])
        self.assertTrue(errors_of(";;"))                      # ';' is not in delim_term
        self.assertTrue(errors_of("x;5"))                     # numbers are not in delim_term


class MinusState141(unittest.TestCase):
    def test_minus_token_only_before_non_number(self):
        self.assertEqual(pairs("a - 5"), [("id", "a"), ("-", "-"), ("wharfa_lit", "5")])
        self.assertEqual(pairs("-x"), [("-", "-"), ("id", "x")])
        self.assertEqual(pairs("-(x)"), [("-", "-"), ("(", "("), ("id", "x"), (")", ")")])
        self.assertEqual(pairs("-"), [("-", "-")])

    def test_minus_then_digit_is_negative_literal(self):
        self.assertEqual(pairs("-5"), [("wharfa_lit", "-5")])
        self.assertEqual(pairs("a-5"), [("id", "a"), ("wharfa_lit", "-5")])
        self.assertEqual(pairs("3-2"), [("wharfa_lit", "3"), ("wharfa_lit", "-2")])

    def test_double_minus_is_comment(self):
        self.assertEqual(types("x--5"), ["id", "comment_sl"])

    def test_minus_invalid_follower(self):
        self.assertTrue(errors_of("a -) b"))


class SlashStates149to154(unittest.TestCase):
    def test_plain_division(self):
        self.assertEqual(pairs("7 / 2"), [("wharfa_lit", "7"), ("/", "/"), ("wharfa_lit", "2")])
        self.assertEqual(pairs("7/2"), [("wharfa_lit", "7"), ("/", "/"), ("wharfa_lit", "2")])

    def test_slash_minus_retracts_two(self):
        # 149 -> 153 -> 154**: emit "/", give back "-" and the next character
        self.assertEqual(pairs("10/-2"), [("wharfa_lit", "10"), ("/", "/"), ("wharfa_lit", "-2")])
        self.assertEqual(pairs("a /- b"), [("id", "a"), ("/", "/"), ("-", "-"), ("id", "b")])
        self.assertEqual(pairs("a/-b"), [("id", "a"), ("/", "/"), ("-", "-"), ("id", "b")])

    def test_slash_minus_bad_follower(self):
        self.assertTrue(errors_of("a /-) b"))

    def test_slash_not_followed_by_minus_operand(self):
        self.assertTrue(errors_of("a // b"))
        self.assertTrue(errors_of("a /* b"))

    def test_slash_equals(self):
        self.assertEqual(types("e /= 2;"), ["id", "/=", "wharfa_lit", ";"])


if __name__ == "__main__":
    unittest.main()
