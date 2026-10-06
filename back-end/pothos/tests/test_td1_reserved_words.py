"""TD1 Reserved Words, states 1-136, plus revision A1 and open decision D."""
import unittest
from unittest import mock

from lexer import lexer as lexer_module
from lexer.tokens import RESERVED_WORDS
from tests.support import errors_of, pairs, types

# IV.A / Reserved Words table (p.36-37): the delimiter set of every word
DELIMITER_OF = {
    "strina": "delim_space", "wharfa": "delim_space", "trua": "delim_space", "lis": "delim_space",
    "glossare": "delim_space", "prin": "delim_flow", "inpub": "delim_flow", "formo": "delim_flow",
    "innum": "delim_flow", "Inaccu": "delim_bool", "Trua": "delim_bool", "an": "delim_flow",
    "othan": "delim_flow", "neve": "delim_flow", "belial": "delim_flow", "belsa": "delim_flow",
    "elsa": "delim_block", "lood": "delim_flow", "cycla": "delim_flow", "paus": "delim_stmt",
    "persis": "delim_stmt", "reor": "delim_reor", "deleo": "delim_space", "insid": "delim_space",
    "const": "delim_space", "pas": "delim_stmt",
}
# one follower (besides whitespace) that each set allows, and one it does not allow
EXTRA_OK = {"delim_flow": "(", "delim_block": "{", "delim_stmt": ";", "delim_reor": "(", "delim_bool": ";"}
NOT_OK = {"delim_space": "(", "delim_flow": "{", "delim_block": "(", "delim_stmt": ")",
          "delim_reor": ";", "delim_bool": "."}


def token_type(word):
    return "trua_lit" if word in ("Trua", "Inaccu") else word


class EveryReservedWord(unittest.TestCase):
    def test_table_covers_all_26_words(self):
        self.assertEqual(set(DELIMITER_OF), set(RESERVED_WORDS))
        self.assertEqual(len(RESERVED_WORDS), 26)

    def test_followed_by_space_newline_tab_eof(self):
        for word in RESERVED_WORDS:
            for follower in [" ", "\n", "\t", ""]:
                with self.subTest(word=word, follower=follower):
                    self.assertEqual(pairs(word + follower), [(token_type(word), word)])

    def test_followed_by_its_own_delimiter(self):
        for word, set_name in DELIMITER_OF.items():
            if set_name in EXTRA_OK:
                follower = EXTRA_OK[set_name]
                with self.subTest(word=word, follower=follower):
                    self.assertEqual(types(word + follower)[0], token_type(word))

    def test_reor_followers(self):
        for follower in ['"a"', "'a'", "(a)", "[1]", "{}", "-5", "-x"]:
            with self.subTest(follower=follower):
                self.assertEqual(types("reor" + follower)[0], "reor")

    def test_truth_literals_followers(self):
        for follower in [")", "]", "}", ";", ",", ":", "+", "==", "!=", "<"]:
            with self.subTest(follower=follower):
                self.assertEqual(types("Trua" + follower + " x")[0], "trua_lit")
                self.assertEqual(types("Inaccu" + follower + " x")[0], "trua_lit")


class A1FallbackToIdentifier(unittest.TestCase):
    def test_word_that_leaves_a_path(self):
        for word in ["ant", "stri", "bel", "bex", "In", "Inac", "cy", "gloss", "wharf", "pa", "per"]:
            with self.subTest(word=word):
                self.assertEqual(pairs(word), [("id", word)])

    def test_complete_word_followed_by_letter_digit_underscore(self):
        for word in ["belial1", "pass", "prints", "reorder", "lis1", "Trua2", "an_", "and", "elsa_x", "constant"]:
            with self.subTest(word=word):
                self.assertEqual(pairs(word), [("id", word)])

    def test_prefix_then_delimiter(self):
        self.assertEqual(pairs("bel(x)"), [("id", "bel"), ("(", "("), ("id", "x"), (")", ")")])

    def test_single_letters_are_identifiers(self):
        for ch in "abcdefgiIlnoprstTwxyzB":
            with self.subTest(ch=ch):
                self.assertEqual(pairs(ch), [("id", ch)])


class CaseSensitivity(unittest.TestCase):
    """Case variants lex as identifiers; the parser/semantic phase rejects them (E2)."""

    def test_case_variants_are_identifiers(self):
        for word in ["Belial", "BELIAL", "TRUA", "true", "trUa", "inaccu", "INACCU", "Inpub", "Innum", "Elsa", "Prin"]:
            with self.subTest(word=word):
                self.assertEqual(pairs(word), [("id", word)])

    def test_trua_keyword_vs_Trua_literal(self):
        self.assertEqual(pairs("trua flag;"), [("trua", "trua"), ("id", "flag"), (";", ";")])
        self.assertEqual(pairs("Trua;"), [("trua_lit", "Trua"), (";", ";")])
        self.assertEqual(pairs("Inaccu;"), [("trua_lit", "Inaccu"), (";", ";")])


class DCompleteWordWithInvalidDelimiter(unittest.TestCase):
    """D (open): belial{ is a lexical error by default (III.B.5)."""

    def test_keyword_followed_by_invalid_delimiter(self):
        for word, set_name in DELIMITER_OF.items():
            follower = NOT_OK[set_name]
            with self.subTest(word=word, follower=follower):
                e = errors_of(word + follower)
                self.assertEqual(len(e), 1)
                self.assertIn(f"reserved word '{word}'", e[0].message)
                self.assertIn(set_name, e[0].message)

    def test_belial_brace(self):
        tokens_and_errors = lexer_module.tokenize("belial{")
        tokens, e = tokens_and_errors
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0].text, "belial")
        self.assertEqual([(t.type, t.lexeme) for t in tokens], [("{", "{")])   # lexing continues

    def test_prin_quote_is_an_error_either_way(self):
        self.assertTrue(errors_of('prin"Hi";'))
        with mock.patch.object(lexer_module, "COMPLETE_KEYWORD_FALLS_BACK_TO_ID", True):
            self.assertTrue(errors_of('prin"Hi";'))          # '"' is not in delim_id either

    def test_switch_applies_A1_literally(self):
        with mock.patch.object(lexer_module, "COMPLETE_KEYWORD_FALLS_BACK_TO_ID", True):
            self.assertEqual(pairs("belial{"), [("id", "belial"), ("{", "{")])


if __name__ == "__main__":
    unittest.main()
