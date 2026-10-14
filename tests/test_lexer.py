import pytest

from backend.pothos.compiler.serialize import token_to_dict
from backend.pothos.lexer import Lexer


def lex(source):
    return Lexer(source).run()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("flo x = 12.5;", [("flo", "flo"), ("id", "x"), ("=", "="), ("flo_lit", "12.5"), (";", ";")]),
        ("wharfa n = 007;", [("wharfa", "wharfa"), ("id", "n"), ("=", "="), ("wharfa_lit", "007"), (";", ";")]),
        ("x=-3;", [("id", "x"), ("=", "="), ("-", "-"), ("wharfa_lit", "3"), (";", ";")]),
        ("0.5", [("flo_lit", "0.5")]),
        ("12345678.5", [("flo_lit", "12345678.5")]),
        ("123456789", [("wharfa_lit", "12345678"), ("wharfa_lit", "9")]),
        ("1.12345", [("flo_lit", "1.1234"), ("wharfa_lit", "5")]),
        ("[1, 2]", [("[", "["), ("wharfa_lit", "1"), (",", ","), ("wharfa_lit", "2"), ("]", "]")]),
        ('{"a": 1}', [("{", "{"), ("strina_lit", '"a"'), (":", ":"), ("wharfa_lit", "1"), ("}", "}")]),
        ("add(3, 4)", [("id", "add"), ("(", "("), ("wharfa_lit", "3"), (",", ","), ("wharfa_lit", "4"), (")", ")")]),
        ("inpub()", [("inpub", "inpub"), ("(", "("), (")", ")")]),
        ("}", [("}", "}")]),
        ("[]", [("[", "["), ("]", "]")]),
        ("grid[0][1]", [("id", "grid"), ("[", "["), ("wharfa_lit", "0"), ("]", "]"), ("[", "["), ("wharfa_lit", "1"), ("]", "]")]),
        ("nums[0]+1", [("id", "nums"), ("[", "["), ("wharfa_lit", "0"), ("]", "]"), ("+", "+"), ("wharfa_lit", "1")]),
        ("(1 + 2)*3", [("(", "("), ("wharfa_lit", "1"), ("+", "+"), ("wharfa_lit", "2"), (")", ")"), ("*", "*"), ("wharfa_lit", "3")]),
        ('msg="Hi"', [("id", "msg"), ("=", "="), ("strina_lit", '"Hi"')]),
        ('s += "x"', [("id", "s"), ("+=", "+="), ("strina_lit", '"x"')]),
        ('prin("a\\nb");', [("prin", "prin"), ("(", "("), ("strina_lit", '"a\\nb"'), (")", ")"), (";", ";")]),
        ("printx", [("id", "printx")]),
        ("answer", [("id", "answer")]),
        ("flox", [("id", "flox")]),
        ("inflow", [("id", "inflow")]),
        ("Trua", [("trua_lit", "Trua")]),
        ("Inaccu", [("trua_lit", "Inaccu")]),
        ("belsa (x > 1)", [("belsa", "belsa"), ("(", "("), ("id", "x"), (">", ">"), ("wharfa_lit", "1"), (")", ")")]),
        ("-- note", [("comment_sl", "-- note")]),
        ("--", [("comment_sl", "--")]),
        ("/-- a - b -- c ---/", [("comment_ml", "/-- a - b -- c ---/")]),
        ("x;\n", [("id", "x"), (";", ";")]),
        ("elsa {\n", [("elsa", "elsa"), ("{", "{")]),
        ("inpub()\n", [("inpub", "inpub"), ("(", "("), (")", ")")]),
        ("grid[0]\n", [("id", "grid"), ("[", "["), ("wharfa_lit", "0"), ("]", "]")]),
        ("elsa {}", [("elsa", "elsa"), ("{", "{"), ("}", "}")]),
    ],
)
def test_valid_lexemes(source, expected):
    tokens, errors = lex(source)

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == expected


@pytest.mark.parametrize(
    ("escape",),
    [(r"\n",), (r"\t",), (r"\0",), (r"\"",), (r"\'",), (r"\\",)],
)
def test_string_escape_is_accepted(escape):
    source = f'"a{escape}b"'

    tokens, errors = lex(source)

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == [("strina_lit", source)]


def test_leading_zero_integer_value_is_dropped():
    tokens, errors = lex("wharfa n = 007;")

    assert errors == []
    integer = next(token for token in tokens if token.type == "wharfa_lit")
    assert integer.lexeme == "007"
    assert token_to_dict(integer, 1)["value"] == 7


@pytest.mark.parametrize(
    ("source", "line", "column", "lexeme"),
    [
        ("5.", 1, 1, "5."),
        (".5", 1, 1, ".5"),
        ("+25", 1, 1, "+25"),
        ('"bad\\x"', 1, 5, "\\x"),
        ('"unclosed\nnext', 1, 1, '"unclosed'),
        ("x --/", 1, 3, "--/"),
        ("/-- never closed", 1, 1, "/-- never closed"),
        ("café", 1, 4, "é"),
        ("-- café", 1, 7, "é"),
        ("_name", 1, 1, "_name"),
        ("abcdefghijklmnopqrstu", 1, 1, "abcdefghijklmnopqrstu"),
        ("prin+", 1, 1, "prin+"),
    ],
)
def test_lexical_error_location_and_lexeme(source, line, column, lexeme):
    tokens, errors = lex(source)

    assert errors
    assert (errors[0].line, errors[0].column, errors[0].text) == (line, column, lexeme)


def test_unclosed_string_recovers_on_next_line():
    tokens, errors = lex('"unclosed\nnext')

    assert len(errors) == 1
    assert (errors[0].line, errors[0].column, errors[0].text) == (1, 1, '"unclosed')
    assert [(token.type, token.lexeme, token.line, token.column) for token in tokens] == [
        ("id", "next", 2, 1)
    ]


def test_keyword_prefix_prinx_is_an_identifier():
    tokens, _ = lex("prinx(")

    assert tokens[0].type == "id"
    assert tokens[0].lexeme == "prinx"


def test_keyword_prefix_prin5_is_an_identifier():
    tokens, errors = lex("prin5")

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == [("id", "prin5")]


def test_keyword_followed_by_operator_is_an_error():
    tokens, errors = lex("prin+")

    assert tokens == []
    assert errors
    assert (errors[0].line, errors[0].column) == (1, 1)
