"""
phases.py  –  Phase interface and the lexical analysis phase.

A Phase is a callable object with a well-known signature:

    result = phase(source, state, options)

where:
    source  : str               – the original Pothos source (already \n-normalised)
    state   : dict              – mutable accumulator shared across phases
                                  (see pipeline.py for the keys it starts with)
    options : dict              – request options (skipComments, trace, …)

A phase returns a dict with at least:
    "ok"     : bool             – True if the phase completed without errors
    "errors" : list[dict]       – zero or more serialised error dicts (see serialize.py)

Each phase is responsible for adding its own output to *state* so that later
phases (syntax, semantic) can read it.

──────────────────────────────────────────────────────────────────────────────
Current phases
──────────────────────────────────────────────────────────────────────────────
LexicalPhase   – runs the hand-written Pothos state-machine lexer.
               Adds state["tokens"] (list[Token]) and state["paths"]
               (list of (line, col, lexeme, path_str) tuples, only when
               trace=True) so later phases can consume the token list.

──────────────────────────────────────────────────────────────────────────────
Placeholder phases (not yet implemented)
──────────────────────────────────────────────────────────────────────────────
SyntaxPhase    – will receive state["tokens"] (list[Token]) produced by
               LexicalPhase and build a parse tree / AST, adding
               state["ast"] for SemanticPhase.  It should return a
               PhaseResult with ok=False and a non-empty errors list when
               a parse error is found, which will stop SemanticPhase from
               running.

SemanticPhase  – will receive state["ast"] produced by SyntaxPhase and
               perform type-checking and scope analysis.  It should add
               state["ir"] (intermediate representation) for any future
               code-generation phase.
"""
from __future__ import annotations

import sys
import os
from typing import Any

# ---------------------------------------------------------------------------
# Make sure the lexer package is importable from this file's location.
# This module lives at  back-end/pothos/compiler/phases.py, and the lexer is
# at  back-end/pothos/lexer/, so the parent directory (back-end/pothos) must
# be on sys.path.
# ---------------------------------------------------------------------------
_POTHOS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _POTHOS_DIR not in sys.path:
    sys.path.insert(0, _POTHOS_DIR)

from lexer import Lexer  # noqa: E402  (after sys.path adjustment)

from .serialize import error_to_dict, token_to_dict  # noqa: E402


class PhaseResult:
    """Lightweight value object returned by every phase."""

    __slots__ = ("ok", "errors")

    def __init__(self, ok: bool, errors: list[dict]) -> None:
        self.ok = ok
        self.errors = errors

    def to_dict(self) -> dict:
        return {"ok": self.ok, "errors": self.errors}


# ---------------------------------------------------------------------------
# Lexical phase
# ---------------------------------------------------------------------------

class LexicalPhase:
    """Runs the Pothos state-machine lexer.

    After running, state["tokens"] holds the list[Token] and, when
    options["trace"] is True, state["paths"] holds the per-token TD
    state-path strings (one entry per token in the same order).
    """

    name = "lexical"

    def __call__(
        self,
        source: str,
        state: dict[str, Any],
        options: dict[str, Any],
    ) -> PhaseResult:
        skip_comments: bool = bool(options.get("skipComments", False))
        trace: bool = bool(options.get("trace", False))

        lx = Lexer(source, skip_comments=skip_comments, trace=trace)
        tokens, lex_errors = lx.run()

        # Store raw objects for later phases.
        state["tokens"] = tokens

        # Build the serialised token list for the API response.
        if trace:
            paths_by_location = {(line, col): path for line, col, _, path in lx.paths}
            token_locations = {(token.line, token.column) for token in tokens}
            error_paths = {
                location: path
                for location, path in paths_by_location.items()
                if location not in token_locations
            }
            state["paths"] = [path for _, _, _, path in lx.paths]
            token_dicts = [
                token_to_dict(
                    token,
                    i + 1,
                    path=paths_by_location.get((token.line, token.column)),
                )
                for i, token in enumerate(tokens)
            ]
            error_dicts = [
                error_to_dict(
                    error,
                    phase=self.name,
                    path=error_paths.get((error.line, error.column)),
                )
                for error in lex_errors
            ]
        else:
            token_dicts = [token_to_dict(t, i + 1) for i, t in enumerate(tokens)]
            error_dicts = [error_to_dict(e, phase=self.name) for e in lex_errors]

        state["token_dicts"] = token_dicts

        return PhaseResult(ok=len(error_dicts) == 0, errors=error_dicts)


# ---------------------------------------------------------------------------
# Placeholder phases (not yet implemented)
# ---------------------------------------------------------------------------

class SyntaxPhase:
    """Syntax analysis phase (NOT YET IMPLEMENTED).

    When implemented, this phase will:
      * Receive state["tokens"] (list[Token]) produced by LexicalPhase.
      * Build a parse tree / AST and store it as state["ast"].
      * Return PhaseResult(ok=False, errors=[...]) on parse errors, which
        prevents SemanticPhase from running.

    Plug in by appending ``SyntaxPhase()`` to the ``_PHASES`` list in
    pipeline.py after the lexical phase.
    """

    name = "syntax"

    def __call__(
        self,
        source: str,
        state: dict[str, Any],
        options: dict[str, Any],
    ) -> PhaseResult:
        raise NotImplementedError(
            "SyntaxPhase is a placeholder.  "
            "Implement the Pothos LL/LR parser and uncomment it in pipeline.py."
        )


class SemanticPhase:
    """Semantic analysis phase (NOT YET IMPLEMENTED).

    When implemented, this phase will:
      * Receive state["ast"] produced by SyntaxPhase.
      * Perform type-checking, scope analysis, and any other semantic checks.
      * Store an intermediate representation as state["ir"] for a future
        code-generation phase.
      * Return PhaseResult(ok=False, errors=[...]) on semantic errors.

    Plug in by appending ``SemanticPhase()`` to ``_PHASES`` in pipeline.py
    after the syntax phase.
    """

    name = "semantic"

    def __call__(
        self,
        source: str,
        state: dict[str, Any],
        options: dict[str, Any],
    ) -> PhaseResult:
        raise NotImplementedError(
            "SemanticPhase is a placeholder.  "
            "Implement the Pothos type-checker and uncomment it in pipeline.py."
        )
