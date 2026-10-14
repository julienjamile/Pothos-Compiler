"""
tokens.py - the Token record and token type names used by the Pothos lexer.

Token types:
  * reserved words use the word itself, e.g. "belial" and "wharfa".
    Trua and Inaccu use the shared type "trua_lit".
  * reserved symbols use the symbol itself, e.g. "+=", "(", and ";".
  * identifiers, literals, and comments use id, wharfa_lit, strina_lit,
    trua_lit, comment_sl, and comment_ml.

The tuples below are reference lists for the parser and the tests. The lexer
does NOT look identifiers up in them; reserved words are recognized only by
walking the TD1 states in lexer.py.
"""
from dataclasses import dataclass

# Literal and comment token types
ID = "id"
WHARFA_LIT = "wharfa_lit"
STRINA_LIT = "strina_lit"
TRUA_LIT = "trua_lit"
COMMENT_SL = "comment_sl"
COMMENT_ML = "comment_ml"

# Reserved words recognized by the lexer
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

# Reserved symbols that become tokens. Quotes and comment markers are part of
# their respective string or comment tokens.
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
