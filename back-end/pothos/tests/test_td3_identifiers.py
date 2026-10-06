"""TD3 Identifiers, states 196-235: letter (alphanum | _){0,19}."""
import unittest

from tests.support import errors_of, pairs, types


class Length(unittest.TestCase):
    def test_one_character(self):
        self.assertEqual(pairs("x"), [("id", "x")])

    def test_twenty_characters_is_the_maximum(self):
        name = "a" * 20
        self.assertEqual(pairs(name), [("id", name)])
        self.assertEqual(pairs(name + ";"), [("id", name), (";", ";")])

    def test_twenty_one_characters_is_an_error(self):
        name = "a" * 21
        e = errors_of(name + " = 1;")
        self.assertEqual(len(e), 1)
        self.assertIn("exceeds 20 characters", e[0].message)
        self.assertEqual(e[0].text, name)                      # the whole word is reported and skipped
        self.assertEqual((e[0].line, e[0].column), (1, 1))

    def test_every_length_1_to_20(self):
        for k in range(1, 21):
            name = "Q" + "_9" * ((k - 1) // 2) + ("z" if (k - 1) % 2 else "")
            with self.subTest(k=k):
                self.assertEqual(len(name), k)
                self.assertEqual(pairs(name), [("id", name)])


class Characters(unittest.TestCase):
    def test_letters_digits_underscore(self):
        for name in ["score", "userName", "total_amount", "a1", "A", "x_1_y", "Z9"]:
            with self.subTest(name=name):
                self.assertEqual(pairs(name), [("id", name)])

    def test_must_start_with_letter(self):
        self.assertIn("must begin with a letter", errors_of("_age")[0].message)
        self.assertTrue(errors_of("2ndName"))

    def test_special_symbol_is_error(self):
        e = errors_of("total$")
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0].text, "total$")
        self.assertTrue(errors_of("a.b"))
        self.assertTrue(errors_of("name#"))

    def test_space_splits_into_two_identifiers(self):
        self.assertEqual(types("first name"), ["id", "id"])     # lexes OK, rejected by the parser

    def test_followers_in_delim_id(self):
        for follower in [" ", "(", ")", "{", "}", "[", "]", ";", ",", ":", "+", "-", "*", "/", "%", "<", ">", "=", "!=", "\n", "\t"]:
            with self.subTest(follower=follower):
                tokens = types("x" + follower + (" y" if follower.strip() else ""))
                self.assertEqual(tokens[0], "id")

    def test_quote_after_identifier_is_error(self):
        self.assertTrue(errors_of('x"a"'))
        self.assertTrue(errors_of("x'a'"))


if __name__ == "__main__":
    unittest.main()
