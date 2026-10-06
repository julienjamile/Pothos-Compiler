"""main.py: file mode, --no-comments, exit codes, interactive prompt."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(ROOT, "main.py")


def run(args, stdin=None):
    return subprocess.run([sys.executable, MAIN] + args, input=stdin, capture_output=True, text=True, cwd=ROOT)


class FileMode(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.dir.cleanup()

    def write(self, text):
        path = os.path.join(self.dir.name, "prog.pths")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        return path

    def test_table_and_no_errors(self):
        result = run([self.write("x = 5; -- c\n")])
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.splitlines()
        self.assertEqual([c.strip() for c in lines[0].split("|")], ["Line", "Col", "Lexeme", "Token"])
        self.assertIn("comment_sl", result.stdout)
        self.assertIn("No lexical errors.", result.stdout)

    def test_no_comments_flag(self):
        result = run([self.write("x = 5; -- c\n/-- m --/\n"), "--no-comments"])
        self.assertNotIn("comment_sl", result.stdout)
        self.assertNotIn("comment_ml", result.stdout)

    def test_errors_and_exit_code(self):
        result = run([self.write("x = 1;\ny = 123456789;\n")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("Lexical Error [line 2, col 5]: wharfa literal exceeds 8 significant digits", result.stdout)

    def test_windows_line_endings(self):
        result = run([self.write("x = 1;\r\ny = 2;\r\n")])
        self.assertEqual(result.returncode, 0)

    def test_trace(self):
        result = run([self.write("belial1"), "--trace"])
        self.assertIn("0 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> A1->196", result.stdout)

    def test_missing_file(self):
        result = run([os.path.join(self.dir.name, "nope.pths")])
        self.assertEqual(result.returncode, 2)


class InteractiveMode(unittest.TestCase):
    def test_prompt(self):
        result = run([], stdin="x = 1;\n\n:quit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("interactive mode", result.stdout)
        self.assertIn("wharfa_lit", result.stdout)

    def test_multi_line_input(self):
        result = run([], stdin="/-- a\nb --/ y = 2;\n\n")
        self.assertIn("comment_ml", result.stdout)
        self.assertIn("No lexical errors.", result.stdout)


if __name__ == "__main__":
    unittest.main()
