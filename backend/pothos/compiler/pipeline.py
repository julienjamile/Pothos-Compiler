"""
pipeline.py  –  compile_source: runs all enabled compiler phases in order.

    from compiler import compile_source

    result = compile_source(source, options)

``source`` must be a str with \\n line endings (no \\r).  Callers are
responsible for normalising line endings before calling this function
(app.py does this).

``options`` is a plain dict (usually the parsed JSON request body):
    skipComments : bool   – drop comment tokens from the response
    trace        : bool   – include TD state-path string in each token dict

Return value is a JSON-safe dict:

    {
        "tokens"   : list[dict],   # serialised Token objects
        "errors"   : list[dict],   # serialised errors from ALL phases
        "phases"   : {             # per-phase status: "ok" | "error" | "skipped"
            "lexical"  : "ok",
            "syntax"   : "skipped",
            "semantic" : "skipped",
        },
        "stopped_at": str | null,  # name of first failing phase, or null
    }

Adding a new phase
──────────────────
1.  Create a class in phases.py with a `name` attribute and a ``__call__``
    matching the Phase protocol (see phases.py docstring).
2.  Import it here and append an instance to _PHASES.
3.  That is all.  The pipeline will automatically run it, collect its errors,
    and stop subsequent phases if it fails.
"""
from __future__ import annotations

from typing import Any

from .phases import LexicalPhase

# ── Phase registry ────────────────────────────────────────────────────────────
# Phases run in list order.  To add syntax / semantic phases uncomment the
# relevant import and append the instance here.
#
# from .phases import SyntaxPhase, SemanticPhase
#
_PHASES = [
    LexicalPhase(),
    # SyntaxPhase(),    # uncomment when the parser is ready
    # SemanticPhase(),  # uncomment when the type-checker is ready
]

# Status strings used in the "phases" dict of the response.
_STATUS_OK = "ok"
_STATUS_ERROR = "error"
_STATUS_SKIPPED = "skipped"


def compile_source(source: str, options: dict[str, Any] | None = None) -> dict:
    """Run all enabled compiler phases on *source* and return the API dict.

    Args:
        source:  Pothos source code, already \\r\\n / \\r → \\n normalised.
        options: Request options (skipComments, trace, …).  If None, all
                 options default to False.

    Returns:
        A JSON-safe dict as described in the module docstring.
    """
    if options is None:
        options = {}

    # Shared mutable accumulator; phases add their results here.
    state: dict[str, Any] = {}

    all_errors: list[dict] = []
    phase_statuses: dict[str, str] = {p.name: _STATUS_SKIPPED for p in _PHASES}
    stopped_at: str | None = None

    for phase in _PHASES:
        if stopped_at is not None:
            # A previous phase failed; leave this phase as "skipped".
            break

        result = phase(source, state, options)
        phase_statuses[phase.name] = _STATUS_OK if result.ok else _STATUS_ERROR
        all_errors.extend(result.errors)

        if not result.ok:
            stopped_at = phase.name

    return {
        "tokens": state.get("token_dicts", []),
        "errors": all_errors,
        "phases": phase_statuses,
        "stopped_at": stopped_at,
    }
