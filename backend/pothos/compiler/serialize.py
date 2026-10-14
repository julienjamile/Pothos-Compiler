"""
serialize.py  –  convert Pothos lexer objects to plain JSON-safe dicts.

The shapes here are the ones the frontend reads:

    Token dict:
        { "no": int, "lexeme": str, "token": str, "line": int, "column": int }
        (optional) "value": int | float -- included for numeric literals
        (optional) "path": str -- included only when trace=True

    Error dict:
        { "phase": str, "line": int, "column": int,
          "message": str, "text": str, "lexeme": str }
        (optional) "path": str -- included only when trace=True
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lexer import LexicalError, Token


def token_to_dict(token: "Token", no: int, path: str | None = None) -> dict:
    """Serialize a Token to a JSON-safe dict.

    Args:
        token: The Token dataclass instance from the lexer.
        no:    1-based position number used by the frontend table.
        path:  TD state-path string (e.g. "0 -> 72 -> 73*").  When provided,
               a ``"path"`` key is added.  Omit (None) for the normal case.

    Returns:
        A plain dict safe for ``json.dumps``.
    """
    d: dict = {
        "no": no,
        "lexeme": token.lexeme,
        "token": token.type,
        "line": token.line,
        "column": token.column,
    }
    if token.type == "wharfa_lit":
        d["value"] = int(token.lexeme)
    elif token.type == "flo_lit":
        d["value"] = float(token.lexeme)
    if path is not None:
        d["path"] = path
    return d


def error_to_dict(
    error: "LexicalError",
    phase: str = "lexical",
    path: str | None = None,
) -> dict:
    """Serialize a LexicalError to a JSON-safe dict.

    Args:
        error: The LexicalError dataclass instance from the lexer.
        phase: The compiler phase that produced the error.  Currently always
               ``"lexical"``; later phases will pass their own name.
        path: TD state-path string. Omit (None) for the normal case.

    Returns:
        A plain dict safe for ``json.dumps``.
    """
    result = {
        "phase": phase,
        "line": error.line,
        "column": error.column,
        "message": error.message,
        "text": error.text,
        "lexeme": error.text,
    }
    if path is not None:
        result["path"] = path
    return result
