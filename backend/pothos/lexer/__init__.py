"""Pothos lexical analyzer package.

    from lexer import tokenize
    tokens, errors = tokenize(source_text)
"""
from .errors import LexicalError
from .lexer import Lexer, tokenize
from .tokens import Token

__all__ = ["tokenize", "Lexer", "Token", "LexicalError"]
