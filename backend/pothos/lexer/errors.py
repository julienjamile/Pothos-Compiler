"""
errors.py - the record the lexer stores for every lexical error.

The lexer never stops at the first error. It records a LexicalError, recovers,
and continues, so one run reports every lexical error in the file.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class LexicalError:
    message: str    # what went wrong, e.g. "identifier exceeds 20 characters"
    line: int       # 1-based line where the offending text starts
    column: int     # 1-based column where the offending text starts
    text: str       # the offending source text that was skipped

    def __str__(self):
        shown = self.text.replace("\n", "\\n").replace("\t", "\\t")
        if len(shown) > 40:
            shown = shown[:37] + "..."
        message = self.message.replace("ASCII", "ascii")
        return f"Lexical Error [line {self.line}, col {self.column}]: {message}: '{shown}'"
