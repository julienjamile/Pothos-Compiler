"""charsets.py must match IV.B (p.31) and IV.E (p.34-35) of the PDF."""
import unittest

from lexer import charsets as cs
from lexer.charsets import EOF


class RegularDefinitions(unittest.TestCase):
    def test_digit_has_no_zero(self):
        self.assertEqual(cs.digit, set("123456789"))
        self.assertEqual(cs.numbers, set("0123456789"))

    def test_letters(self):
        self.assertEqual(len(cs.caplet), 26)
        self.assertEqual(len(cs.lowlet), 26)
        self.assertEqual(cs.letter, cs.caplet | cs.lowlet)
        self.assertEqual(cs.alphanum, cs.letter | cs.numbers)

    def test_ascii_is_printable_plus_tab(self):
        self.assertEqual(len(cs.ascii), 95 + 1)
        self.assertIn("\t", cs.ascii)
        self.assertNotIn("\n", cs.ascii)
        self.assertNotIn("\u00e9", cs.ascii)

    def test_string_and_comment_sets(self):
        self.assertEqual(cs.ascii_str_dq, cs.ascii - {'"', "\\"})
        self.assertEqual(cs.ascii_str_sq, cs.ascii - {"'", "\\"})
        self.assertIn("'", cs.ascii_str_dq)
        self.assertIn('"', cs.ascii_str_sq)
        self.assertEqual(cs.ascii_comment_sl, cs.ascii)          # ascii has no newline already
        self.assertEqual(cs.ml_char, (cs.ascii | {"\n"}) - {"-"})
        self.assertEqual(cs.ml_char_ns, cs.ml_char - {"/"})

    def test_mathop_relop_whitespace(self):
        self.assertEqual(cs.mathop, set("+-*/%"))
        self.assertEqual(cs.relop_ch, set("<>=!"))
        self.assertEqual(cs.whitespace, {" ", "\n", "\t"})


class DelimiterSets(unittest.TestCase):
    def test_delim_space_has_eof(self):
        self.assertEqual(cs.delim_space, {" ", "\n", "\t", EOF})

    def test_value_end_sets_are_identical(self):
        # delim_id, delim_int, delim_str, delim_close, delim_bool have the same definition in IV.E
        expected = cs.delim_space | set("(){}[];,:") | cs.mathop | cs.relop_ch
        for s in (cs.delim_id, cs.delim_int, cs.delim_str, cs.delim_close, cs.delim_bool):
            self.assertEqual(s, expected)
        self.assertNotIn('"', cs.delim_id)
        self.assertNotIn(".", cs.delim_int)
        self.assertNotIn("_", cs.delim_int)

    def test_operand_sets(self):
        self.assertIn("-", cs.delim_operand)
        for s in (cs.delim_mathop, cs.delim_relop, cs.delim_assops, cs.delim_colon, cs.delim_comma):
            self.assertEqual(s, cs.delim_operand)
        self.assertEqual(cs.delim_open_paren, cs.delim_operand | {")"})
        self.assertEqual(cs.delim_open_brack, cs.delim_operand | {"]"})
        self.assertEqual(cs.delim_open_brace, cs.delim_operand | {"}"})

    def test_delim_minus_has_no_minus(self):
        self.assertNotIn("-", cs.delim_minus)
        self.assertEqual(cs.delim_minus, cs.delim_operand - {"-"})
        self.assertEqual(cs.delim_minus_no_numbers & cs.numbers, set())

    def test_keyword_sets(self):
        self.assertEqual(cs.delim_flow, cs.delim_space | {"("})
        self.assertEqual(cs.delim_block, cs.delim_space | {"{"})
        self.assertEqual(cs.delim_stmt, cs.delim_space | {";"})
        self.assertEqual(cs.delim_reor, cs.delim_space | cs.delim_quote | set("([{-"))
        self.assertEqual(cs.delim_rbrace, cs.delim_close)       # delim_close already contains eof
        self.assertIn(EOF, cs.delim_rbrace)

    def test_delim_term(self):
        self.assertEqual(cs.delim_term, cs.delim_space | cs.letter | {"}", "-", "/"})
        self.assertNotIn(";", cs.delim_term)

    def test_quote_sets(self):
        self.assertEqual(cs.delim_quote, {"'", '"'})
        self.assertEqual(cs.delim_dquote, cs.ascii_str_dq | {"\\", '"'})
        self.assertEqual(cs.delim_squote, cs.ascii_str_sq | {"\\", "'"})

    def test_comment_sets(self):
        self.assertNotIn("/", cs.delim_scomment_start)
        self.assertIn(EOF, cs.delim_scomment_start)               # X2
        self.assertEqual(cs.delim_mcomment_start, cs.ascii | {"\n"})
        self.assertEqual(cs.delim_mcomment_end, cs.ascii | {"\n", EOF})

    def test_delim_escape(self):                                  # A3
        self.assertEqual(cs.delim_escape, {'"', "'", "\\", "n", "t", "0"})
        self.assertEqual(len(cs.escape), 6)


if __name__ == "__main__":
    unittest.main()
