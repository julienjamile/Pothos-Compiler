"""
tokens.py - the Token record and token type names used by the Pothos lexer.

Token types:
  * reserved words use the word itself, e.g. "belial" and "wharfa".
  * reserved symbols use the symbol itself, e.g. "+=", "(", and ";".
  * identifiers, literals, and comments use id, wharfa_lit, flo_lit,
    strina_lit, trua_lit, comment_sl, and comment_ml.
  * Trua and Inaccu are both trua_lit, so the parser treats them
    like any other literal.
  * A minus sign is never part of a number; -5 is '-' then
    wharfa_lit '5'.

The tuples below are reference lists for the parser and the tests. The lexer
does NOT look identifiers up in them; reserved words are recognized only by
walking the TD1 states in lexer.py.
"""
from dataclasses import dataclass

# Literal and comment token types
ID = "id"
WHARFA_LIT = "wharfa_lit"
FLO_LIT = "flo_lit"
STRINA_LIT = "strina_lit"
TRUA_LIT = "trua_lit"
COMMENT_SL = "comment_sl"
COMMENT_ML = "comment_ml"

# Reserved words recognized by the lexer
RESERVED_WORDS = (
    # data types
    "strina", "wharfa", "flo", "trua", "lis", "glossare",
    # input / output
    "prin", "inpub", "formo", "innum", "inflo",
    # truth literals (token type trua_lit)
    "Trua", "Inaccu",
    # logical operators
    "an", "othan", "neve",
    # control flow
    "belial", "belsa", "elsa", "lood", "cycla", "paus", "persis", "pas",
    # structural
    "reor",
    # variable operations
    "deleo", "const",
    # membership
    "insid",
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
    lexeme: str     # exact source text, e.g. "0100", "\"Hi\\n\"", "12.5"
    line: int       # 1-based line of the first character
    column: int     # 1-based column of the first character

    def __str__(self):
        return f"{self.line}:{self.column} {self.type} {self.lexeme!r}"
