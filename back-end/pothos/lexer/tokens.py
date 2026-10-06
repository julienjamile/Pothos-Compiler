"""
tokens.py - the Token record and the token type names from the PDF.

Token types (Pothos_ProgrammingLanguage.pdf):
  * reserved words (IV.A, p.28-30): the token type is the word itself,
    e.g. "belial", "wharfa". Exception: Trua and Inaccu are "trua_lit" (IV.D).
  * reserved symbols (IV.C, p.31-33): the token type is the symbol itself,
    e.g. "+=", "(", ";".
  * literals (IV.D, p.33-34): id, wharfa_lit, strina_lit, trua_lit,
    comment_sl, comment_ml.

The tuples below are reference lists for the parser and the tests. The lexer
does NOT look identifiers up in them; reserved words are recognized only by
walking the TD1 states in lexer.py.
"""
from dataclasses import dataclass

# IV.D Reserved Literals
ID = "id"
WHARFA_LIT = "wharfa_lit"
STRINA_LIT = "strina_lit"
TRUA_LIT = "trua_lit"
COMMENT_SL = "comment_sl"
COMMENT_ML = "comment_ml"

# IV.A Reserved Words, in table order (26 words)
RESERVED_WORDS = (
    "strina", "wharfa", "trua", "lis", "glossare",          # 1. data types
    "prin", "inpub", "formo", "innum",                      # 2. I/O functions
    "Inaccu", "Trua",                                       # 3. truth literals -> trua_lit
    "an", "othan", "neve",                                  # 4. logical operators
    "belial", "belsa", "elsa", "lood", "cycla", "paus", "persis",   # 5. control flow
    "reor",                                                 # 6. structural definitions
    "deleo",                                                # 7. variable operations
    "insid", "const", "pas",                                # 8. membership / misc
)

# IV.C Reserved Symbols that become tokens (the quotes and comment markers are
# part of strina_lit / comment_sl / comment_ml tokens instead, see B3).
RESERVED_SYMBOLS = (
    "+", "-", "*", "/", "%",
    "<", ">", "<=", ">=", "==", "!=",
    "=", "+=", "-=", "*=", "/=", "%=",
    "(", ")", "[", "]", "{", "}",
    ",", ":", ";",
)


@dataclass(frozen=True)
class Token:
    type: str       # token type name, e.g. "id", "wharfa_lit", "belial", "+="
    lexeme: str     # exact source text, e.g. "0100", "\"Hi\\n\"", "-5"
    line: int       # 1-based line of the first character
    column: int     # 1-based column of the first character

    def __str__(self):
        return f"{self.line}:{self.column} {self.type} {self.lexeme!r}"
