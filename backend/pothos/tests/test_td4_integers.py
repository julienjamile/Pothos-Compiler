"""TD4 Integer Literals, states 236-271 (negatives through the shared state 141)."""
import unittest

from tests.support import errors_of, pairs, types


class Positive(unittest.TestCase):
    def test_zeros(self):
        for src in ["0", "00", "000000000000"]:
            with self.subTest(src=src):
                self.assertEqual(pairs(src), [("wharfa_lit", src)])

    def test_leading_zeros_do_not_count(self):
        self.assertEqual(pairs("0100"), [("wharfa_lit", "0100")])            # II.9.a.ii: 0100 -> 100
        self.assertEqual(pairs("000099999999"), [("wharfa_lit", "000099999999")])

    def test_every_length_1_to_8(self):
        for k in range(1, 9):
            src = "9" * k
            with self.subTest(k=k):
                self.assertEqual(pairs(src), [("wharfa_lit", src)])
                self.assertEqual(pairs("1" + "0" * (k - 1)), [("wharfa_lit", "1" + "0" * (k - 1))])

    def test_eight_vs_nine_digits(self):
        self.assertEqual(pairs("99999999"), [("wharfa_lit", "99999999")])
        e = errors_of("999999999")
        self.assertEqual(len(e), 1)
        self.assertIn("exceeds 8 significant digits", e[0].message)
        self.assertEqual(e[0].text, "999999999")
        self.assertTrue(errors_of("0000123456789"))                           # 9 significant digits


class Negative(unittest.TestCase):
    def test_negative_literals(self):
        for src in ["-0", "-00", "-5", "-0100", "-99999999"]:
            with self.subTest(src=src):
                self.assertEqual(pairs(src), [("wharfa_lit", src)])

    def test_negative_nine_digits(self):
        e = errors_of("-100000000")
        self.assertEqual(len(e), 1)
        self.assertIn("exceeds 8", e[0].message)

    def test_minus_5_vs_a_minus_5(self):
        self.assertEqual(pairs("-5"), [("wharfa_lit", "-5")])
        self.assertEqual(pairs("a - 5"), [("id", "a"), ("-", "-"), ("wharfa_lit", "5")])
        self.assertEqual(pairs("a-5"), [("id", "a"), ("wharfa_lit", "-5")])
        self.assertEqual(pairs("a - -5"), [("id", "a"), ("-", "-"), ("wharfa_lit", "-5")])
        self.assertEqual(pairs("3-2"), [("wharfa_lit", "3"), ("wharfa_lit", "-2")])


class Delimiters(unittest.TestCase):
    def test_followers_in_delim_int(self):
        for follower in [" ", ";", ")", "]", "}", ",", ":", "+", "-", "*", "/", "%", "<", ">", "=", "!=", "(", "[", "{"]:
            with self.subTest(follower=follower):
                self.assertEqual(types("5" + follower + " x")[0], "wharfa_lit")

    def test_not_allowed_inside_a_literal(self):
        # '.', '_' and letters are not in delim_int (X4: lexical, not parser, errors)
        for src in ["1.5", "1_000", "1e5", "2ndName", "10abc", "0x1F", '5"a"']:
            with self.subTest(src=src):
                self.assertTrue(errors_of(src))

    def test_comma_and_plus_lex_fine(self):
        # C5: lexes OK, rejected later
        self.assertEqual(types("1,000"), ["wharfa_lit", ",", "wharfa_lit"])
        self.assertEqual(types("+25"), ["+", "wharfa_lit"])


if __name__ == "__main__":
    unittest.main()
