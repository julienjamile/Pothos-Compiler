"""Every Valid / Invalid example from Pothos_ProgrammingLanguage.pdf.

Many "Invalid" examples are syntax, semantic or runtime errors. The lexer must
NOT report them (they lex cleanly and a later phase rejects them). Those are
marked LATER. Only the examples marked LEX are lexical errors.
"""
import unittest

from lexer import tokenize

OK = "ok"          # valid example: no lexical error
LATER = "later"    # invalid example, but not a lexical error: lexes OK, rejected later
LEX = "lex"        # invalid example that is a lexical error

# (section, source, expectation, expected text in the first error message)
EXAMPLES = [
    # I. Structure Overview (p.3-4)
    ("I", 'msg = "Hello, World!";\nprin(msg);\n\nwharfa add(wharfa a, wharfa b){\n   reor a + b;\n};\nprin(add(3, 4));', OK, None),

    # III.A Comments (p.8)
    ("III.A", "-- single line comment", OK, None),
    ("III.A", "/-- multi line comment --/", OK, None),
    ("III.A", "x = 5; -- trailing comment", OK, None),
    ("III.A", "/-- missing closer", LEX, "unterminated multi-line comment"),
    ("III.A", "/-- nested /-- inner --/", LATER, None),    # E5: one valid comment (first --/ closes)
    ("III.A", "--/", LEX, "without an opening '/--'"),

    # III.B Identifiers and Reserved Words (p.9)
    ("III.B", "A", OK, None),
    ("III.B", "score", OK, None),
    ("III.B", "userName", OK, None),
    ("III.B", "total_amount", OK, None),
    ("III.B", "add", OK, None),
    ("III.B", "2ndName", LEX, "cannot follow a wharfa literal"),
    ("III.B", "first name", LATER, None),                   # C5: id id
    ("III.B", "total$", LEX, "cannot follow an identifier"),
    ("III.B", "Belial", LATER, None),                       # E2: case variant lexes as id
    ("III.B", "_age", LEX, "must begin with a letter"),
    ("III.B", "studentRegistrationNumber2026", LEX, "exceeds 20 characters"),

    # III.C.1 Strina (p.10)
    ("III.C.1", 'title = "Pothos";', OK, None),
    ("III.C.1", "double_empty = \"\"; single_empty = '';", OK, None),
    ("III.C.1", 'message = "Line one\\nLine two";', OK, None),
    ("III.C.1", 'quote = "She said,\\"Hi.\\"";', OK, None),
    ("III.C.1", 'bad1 = "Hello;', LEX, "unterminated strina literal"),
    ("III.C.1", "bad2 = 'AB\";", LEX, "unterminated strina literal"),
    ("III.C.1", 'bad3 = "Newline\nhere";', LEX, "raw newline"),
    ("III.C.1", 'bad4 = "Hi\\x";', LEX, "invalid escape sequence"),

    # III.C.2 Wharfa (p.11)
    ("III.C.2", "a = 0; b = 100;", OK, None),
    ("III.C.2", "c = -99999999;", OK, None),
    ("III.C.2", "d = 0100;", OK, None),
    ("III.C.2", "x = 100000000;", LEX, "exceeds 8 significant digits"),
    ("III.C.2", "y = 1,000;", LATER, None),                 # C5: 1 , 000
    ("III.C.2", "z = +25;", LATER, None),                   # C5: + 25
    ("III.C.2", "w = 1.5;", LEX, "cannot follow a wharfa literal"),

    # III.C.3 Trua (p.11-12)
    ("III.C.3", "active = Trua; inactive = Inaccu;", OK, None),
    ("III.C.3", "trua flag;", OK, None),
    ("III.C.3", "result = 3 > 2;", OK, None),
    ("III.C.3", "active = true;", LATER, None),             # E2 / C5: id
    ("III.C.3", "locked = 0;", LATER, None),
    ("III.C.3", "flag = Trua", LATER, None),                # missing semicolon: parser

    # III.C.4 Lis (p.12)
    ("III.C.4", "nums = [1, 2, 3];", OK, None),
    ("III.C.4", 'strings = ["str", "strs"]; empty = [];', OK, None),
    ("III.C.4", "first = nums[0];", OK, None),
    ("III.C.4", 'belial (2 insid nums) { prin ("Found"); }', OK, None),
    ("III.C.4", "mixed = [1, 'two', 3];", LATER, None),
    ("III.C.4", "x = nums[3];", LATER, None),
    ("III.C.4", "y = nums[1.5];", LEX, "cannot follow a wharfa literal"),

    # III.C.5 Glossare (p.13)
    ("III.C.5", 'user = {"name": "Ana", "score": 95};', OK, None),
    ("III.C.5", 'name = user["name"];', OK, None),
    ("III.C.5", "emptyDict = {};", OK, None),
    ("III.C.5", 'x = user["age"];', LATER, None),
    ("III.C.5", 'dup = {"a": 1, "a": 2};', LATER, None),
    ("III.C.5", "v = user[random];", LATER, None),

    # III.D Variables and Constants (p.14)
    ("III.D", "age = 19;", OK, None),
    ("III.D", 'name = "Ana";', OK, None),
    ("III.D", "const LIMIT = 100;", OK, None),
    ("III.D", "total = age + 1;", OK, None),
    ("III.D", 'age = 19; age = "nineteen";', LATER, None),
    ("III.D", "const LIMIT;", LATER, None),
    ("III.D", "x = y + 1;", LATER, None),
    ("III.D", "LIMIT = 200;", LATER, None),

    # III.E Assignment and Augmented Assignment (p.15)
    ("III.E", "a = 5; b = 2;\nc = 10; d = 3;\ne = 8; f = 5;", OK, None),
    ("III.E", "b += 3; c -= 2; d*= 4;", OK, None),
    ("III.E", "e /= 2; f %= 3;", OK, None),
    ("III.E", "g -= 1;", LATER, None),
    ("III.E", 's = "X"; s -= 1;', LATER, None),
    ("III.E", "const K = 1; K += 1;", LATER, None),

    # III.F Operators (p.16)
    ("III.F", "x = 7 / 2;", OK, None),
    ("III.F", "y = 7 % 2;", OK, None),
    ("III.F", 'z = "Po" + "thos";', OK, None),
    ("III.F", "result = 3 > 2;", OK, None),
    ("III.F", "active = Trua; ready = Trua;\nboth = active an ready;", OK, None),
    ("III.F", "found = 2 insid [1, 2, 3];", OK, None),
    ("III.F", 'a = 5 + "a";', LATER, None),
    ("III.F", "b = 5 / 0;", LATER, None),
    ("III.F", 'c = "n = " + 5;', LATER, None),
    ("III.F", 'd = 3 > "a";', LATER, None),
    ("III.F", "e = 5 an 3;", LATER, None),
    ("III.F", 'f = 2 insid "hello";', LATER, None),

    # III.G Expressions (p.17)
    ("III.G", "a = 1 + 1;", OK, None),
    ("III.G", "b = (2 + 3) * 4;", OK, None),
    ("III.G", "c = nums[0] + 1;", OK, None),
    ("III.G", "d = 5 an 3;", LATER, None),
    ("III.G", "e = ghost + 1;", LATER, None),
    ("III.G", "f = nums[9] + 1;", LATER, None),

    # III.H Statements and Code Blocks (p.18)
    ("III.H", 'prin("Hello");', OK, None),
    ("III.H", "x = 1; pas;", OK, None),
    ("III.H", "belial ( x == 1) { prin(x); }", OK, None),
    ("III.H", 'prin("Hello")', LATER, None),
    ("III.H", '{ prin("Hi");', LATER, None),
    ("III.H", 'prin("Hi";', LATER, None),

    # III.I.1 prin() (p.19)
    ("III.I.1", 'prin("Hello, World!");', OK, None),
    ("III.I.1", "score = 90; prin(score);", OK, None),
    ("III.I.1", "prin(a + b); prin (1 + 1);", OK, None),
    ("III.I.1", 'prin"Hello";', LEX, "reserved word 'prin'"),       # D: '"' is not in delim_flow
    ("III.I.1", "prin(score;", LATER, None),
    ("III.I.1", "prin(Hello);", LATER, None),

    # III.I.2 inpub() (p.19-20)
    ("III.I.2", "name = inpub();", OK, None),
    ("III.I.2", "city = inpub();", OK, None),
    # PDF reason: unbalanced parenthesis. The lexer already rejects it because
    # ';' is not in delim_open_paren.
    ("III.I.2", "parenthesis = inpub(;", LEX, "cannot follow '('"),
    ("III.I.2", "capitalization = Inpub();", LATER, None),        # E2

    # III.I.3 formo() (p.20)
    ("III.I.3", 'varx = "Sean"; vary = 19;\ngreet = formo("I am {varx}, age {vary}.");', OK, None),
    ("III.I.3", 'varz = "Charles";\nhello = formo("I am {varz}. {{literal}}");', OK, None),
    ("III.I.3", 'greet = formo"I am {varx}.";', LEX, "reserved word 'formo'"),
    ("III.I.3", 'greet = formo("I am {varx}, age {vary}.;', LEX, "unterminated strina literal"),
    ("III.I.3", 'greet = formo("I am {nobody}.");', LATER, None),

    # III.I.4 innum() (p.20-21)
    ("III.I.4", "age = innum();", OK, None),
    ("III.I.4", "score = innum();", OK, None),
    ("III.I.4", "prin(age + 1);", OK, None),
    ("III.I.4", "x = innum(;", LEX, "cannot follow '('"),        # same as inpub(;
    ("III.I.4", "y = Innum();", LATER, None),                    # E2
    ("III.I.4", "z = innum();", LATER, None),                    # runtime

    # III.J Conditional Statements (p.22)
    ("III.J", 'score = 75;\nbelial (score >= 90) { prin("Excellent"); }\nbelsa (score >= 75) { prin("Good"); }\n'
              'elsa { prin("Needs improvement"); }', OK, None),
    ("III.J", 'inventory = ["apple", "banana", "cherry"];\ntarget = "banana";\n\n'
              'belial (target insid inventory) {\n   prin("Item is in stock.");\n}', OK, None),
    ("III.J", 'belial score > 70 { prin("Pass"); }', LATER, None),
    ("III.J", 'belial (score > 70) prin ("Pass");', LATER, None),
    ("III.J", 'belial (score) { prin("Pass"); }', LATER, None),
    ("III.J", 'elsa (score >= 74) { prin("Fail"); }', LATER, None),

    # III.K.1 Cycla (p.23)
    ("III.K.1", "count = 5;\ncycla (count > 0) { prin(count); count -= 1; }", OK, None),
    ("III.K.1", "cycla count > 0 { count -= 1; }", LATER, None),
    ("III.K.1", "cycla (count > 0) count -= 1;", LATER, None),

    # III.K.2 Lood (p.23)
    ("III.K.2", "nums = [1, 2, 3]; m = 0;\nlood (m insid nums) { prin(m); }", OK, None),
    ("III.K.2", 'word = "hi"; ch = "h";\nlood (ch insid word) { prin(ch); }', OK, None),
    ("III.K.2", "lood n insid nums { prin(n); }", LATER, None),
    ("III.K.2", "m = 0; lood (m insid undeclaredList) { }", LATER, None),

    # III.L Loop Control (p.24)
    ("III.L", "cycla (x < 10) {\nx += 1;\nbelial (x == 5) { paus; }\nprin(x);\n}", OK, None),
    ("III.L", "lood (m insid nums) {\nbelial (m == 0) { persis; }\nprin(m);\n}", OK, None),
    ("III.L", "cycla (x < 10) { x += 1; }\npaus;", LATER, None),
    ("III.L", "paus", LATER, None),

    # III.M.1 Function Declaration (p.25)
    ("III.M.1", "wharfa square(wharfa n){\n   reor n * n;\n};", OK, None),
    ("III.M.1", 'strina greet(){\n   reor "Hi";\n};', OK, None),
    ("III.M.1", 'prin("Hello") { prin("Invalid"); };', LATER, None),
    ("III.M.1", "wharfa ab(a) { reor a; };", LATER, None),

    # III.M.4 Function Calls (p.26)
    ("III.M.4", "prin(square(4));", OK, None),
    ("III.M.4", "msg = greet();", OK, None),
    ("III.M.4", "total = square(2) + 1;", OK, None),
    ("III.M.4", "total = square(3;", LATER, None),
    ("III.M.4", "mystery ();", LATER, None),
    ("III.M.4", 'square("Word");', LATER, None),

    # III.M.5 Recursion (p.26-27)
    ("III.M.5", "wharfa factorial(wharfa n){\n   belial(n <= 1){\n      reor 1;\n   }\n   elsa{\n"
                "      reor factorial(n - 1) * n;\n   }\n};", OK, None),
    ("III.M.5", "wharfa endless(wharfa n){\n   reor endless(n + 1);\n};", LATER, None),

    # III.N Object Removal (p.28)
    ("III.N", "temp = 1; deleo temp;", OK, None),
    ("III.N", "deleo ghost;", LATER, None),
    ("III.N", "deleo 5;", LATER, None),
    ("III.N", "const K = 1; deleo K;", LATER, None),
    ("III.N", "x = 1; deleo x; prin(x);", LATER, None),
]


class PdfExamples(unittest.TestCase):
    def test_every_example(self):
        for section, source, expect, message in EXAMPLES:
            with self.subTest(section=section, source=source):
                tokens, errors = tokenize(source)
                if expect in (OK, LATER):
                    self.assertEqual([str(e) for e in errors], [])
                    self.assertTrue(tokens)
                else:
                    self.assertTrue(errors, "expected a lexical error")
                    self.assertIn(message, errors[0].message)

    def test_single_mistake_gives_single_error(self):
        # recovery must not invent follow-up errors for these
        for section, source, expect, _ in EXAMPLES:
            if expect == LEX and "bad3" not in source:
                with self.subTest(section=section, source=source):
                    self.assertEqual(len(tokenize(source)[1]), 1)

    def test_example_counts(self):
        counts = {k: sum(1 for e in EXAMPLES if e[2] == k) for k in (OK, LATER, LEX)}
        self.assertEqual(counts[LEX], 18)
        self.assertEqual(len(EXAMPLES), counts[OK] + counts[LATER] + counts[LEX])


if __name__ == "__main__":
    unittest.main()
