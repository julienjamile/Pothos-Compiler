"""Small helpers shared by the tests."""
from lexer import tokenize


def pairs(source, **kw):
    """[(token_type, lexeme), ...] for `source`; fails if there are lexical errors."""
    tokens, errors = tokenize(source, **kw)
    if errors:
        raise AssertionError(f"unexpected lexical errors for {source!r}: {[str(e) for e in errors]}")
    return [(t.type, t.lexeme) for t in tokens]


def types(source, **kw):
    return [t for t, _ in pairs(source, **kw)]


def errors_of(source, **kw):
    """The list of LexicalError for `source` (tokens are ignored)."""
    return tokenize(source, **kw)[1]
