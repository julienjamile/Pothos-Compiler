import pytest

from backend.pothos.compiler.serialize import token_to_dict
from backend.pothos.lexer import Lexer
from backend.pothos.lexer.charsets import (
    EOF, NEWLINE, delim_arithmetic, delim_augoper, delim_bool, delim_closeparen,
    assops, delim_closecurly, delim_comma, delim_const, delim_datatype,
    delim_deleo, delim_dqclose, delim_dqopen, delim_equal, delim_equality,
    delim_id, delim_insid, delim_io, delim_logic, delim_logic_newline,
    delim_num, delim_openbracket, delim_openparen, delim_oper, delim_plus,
    delim_scolon, delim_sqclose, delim_sqopen,
)


def lex(source):
    return Lexer(source).run()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("flo x = 12.5;", [("flo", "flo"), ("id", "x"), ("=", "="), ("flo_lit", "12.5"), (";", ";")]),
        ("wharfa n = 007;", [("wharfa", "wharfa"), ("id", "n"), ("=", "="), ("wharfa_lit", "7"), (";", ";")]),
        ("x=-3;", [("id", "x"), ("=", "="), ("-", "-"), ("wharfa_lit", "3"), (";", ";")]),
        ("0.5", [("flo_lit", "0.5")]),
        ("12345678.5", [("flo_lit", "12345678.5")]),
        ("1.12345", [("flo_lit", "1.1235")]),
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
        ("printx ", [("id", "printx")]),
        ("answer ", [("id", "answer")]),
        ("flox ", [("id", "flox")]),
        ("inflow ", [("id", "inflow")]),
        ("Trua ", [("trua_lit", "Trua")]),
        ("Inaccu ", [("trua_lit", "Inaccu")]),
        ("belsa {\n", [("belsa", "belsa"), ("{", "{"), ("newline", "\n")]),
        ("-- note", [("comment_sl", "-- note")]),
        ("--", [("comment_sl", "--")]),
        ("/-- a - b -- c ---/", [("comment_ml", "/-- a - b -- c ---/")]),
        ("x;\n", [("id", "x"), (";", ";"), ("newline", "\n")]),
        ("elsa {\n", [("elsa", "elsa"), ("{", "{"), ("newline", "\n")]),
        ("inpub()\n", [("inpub", "inpub"), ("(", "("), (")", ")"), ("newline", "\n")]),
        ("grid[0]\n", [("id", "grid"), ("[", "["), ("wharfa_lit", "0"), ("]", "]"), ("newline", "\n")]),
        ("prin\t(\"ok\")", [("prin", "prin"), ("tab", "\t"), ("(", "("), ("strina_lit", '"ok"'), (")", ")")]),
        ("a \t\nb ", [("id", "a"), ("tab", "\t"), ("newline", "\n"), ("id", "b")]),
        ("elsa {}", [("elsa", "elsa"), ("{", "{"), ("}", "}")]),
    ],
)
def test_valid_lexemes(source, expected):
    tokens, errors = lex(source)

    assert errors == []
    # These grammar examples focus on their non-space lexemes. Dedicated tests
    # below verify that every source space is emitted as a token too.
    assert [(token.type, token.lexeme) for token in tokens if token.type != "space"] == expected


@pytest.mark.parametrize(
    ("escape",),
    [(r"\n",), (r"\t",), (r"\0",), (r"\"",), (r"\'",), (r"\\",)],
)
def test_string_escape_is_accepted(escape):
    source = f'"a{escape}b"'

    tokens, errors = lex(source)

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == [("strina_lit", source)]


def test_leading_zero_integer_lexeme_and_value_are_normalized():
    tokens, errors = lex("wharfa n = 0007;")

    assert errors == []
    integer = next(token for token in tokens if token.type == "wharfa_lit")
    assert integer.lexeme == "7"
    assert token_to_dict(integer, 1)["value"] == 7


@pytest.mark.parametrize("source", ["000000000000", "000000000000;"])
def test_all_zero_integer_has_one_zero_lexeme(source):
    tokens, errors = lex(source)

    assert errors == []
    integer = next(token for token in tokens if token.type == "wharfa_lit")
    assert (integer.lexeme, integer.value) == ("0", 0)


def test_ninth_significant_integer_digit_errors_prefix_then_scans_excess_digit():
    tokens, errors = lex("123456789;")

    assert [(token.type, token.lexeme) for token in tokens] == [
        ("wharfa_lit", "9"), (";", ";")
    ]
    assert len(errors) == 1
    assert (errors[0].text, errors[0].column) == ("12345678", 1)


def test_twenty_first_identifier_character_errors_prefix_then_scans_suffix():
    tokens, errors = lex("abcdefghijklmnopqrstu;")

    assert [(token.type, token.lexeme) for token in tokens] == [
        ("id", "u"), (";", ";")
    ]
    assert len(errors) == 1
    assert (errors[0].text, errors[0].column) == ("abcdefghijklmnopqrst", 1)


@pytest.mark.parametrize(
    ("source", "expected_value"),
    [
        ("1.00001", 1.0),
        ("0.00000", 0.0),
        ("1.2300", 1.23),
        ("1.23000", 1.23),
        ("1.23456", 1.2346),
        ("1.99999", 2.0),
    ],
)
def test_float_is_rounded_to_four_places_and_lexeme_is_normalized(source, expected_value):
    tokens, errors = lex(source)

    assert errors == []
    assert len(tokens) == 1
    assert tokens[0].type == "flo_lit"
    expected_lexeme = {
        "1.00001": "1.0",
        "0.00000": "0.0",
        "1.2300": "1.23",
        "1.23000": "1.23",
        "1.23456": "1.2346",
        "1.99999": "2.0",
    }[source]
    assert tokens[0].lexeme == expected_lexeme
    assert token_to_dict(tokens[0], 1)["value"] == expected_value


def test_float_without_fraction_digits_normalizes_to_one_decimal_place():
    tokens, errors = lex("5.")

    assert errors == []
    assert [(token.type, token.lexeme, token.value) for token in tokens] == [
        ("flo_lit", "5.0", 5.0)
    ]


def test_float_with_many_zero_fraction_digits_normalizes_to_zero_point_zero():
    tokens, errors = lex("000000.00000000000")

    assert errors == []
    assert [(token.type, token.lexeme, token.value) for token in tokens] == [
        ("flo_lit", "0.0", 0.0)
    ]


@pytest.mark.parametrize(
    ("source", "line", "column", "lexeme"),
    [
        (".5", 1, 1, ".5"),
        ("+25", 1, 1, "+25"),
        ('"bad\\x"', 1, 5, "\\x"),
            ('"unclosed\nnext', 1, 1, '"unclosed\nnext'),
        ("x --/", 1, 3, "--/"),
        ("/-- never closed", 1, 1, "/-- never closed"),
        ("café", 1, 4, "é"),
        ("-- café", 1, 7, "é"),
        ("_name", 1, 1, "_name"),
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
    assert (errors[0].line, errors[0].column, errors[0].text) == (1, 1, '"unclosed\nnext')
    assert tokens == []


def test_whitespace_token_paths_are_included_when_tracing():
    lexer = Lexer(" \t \n", trace=True)

    tokens, errors = lexer.run()

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == [
        ("space", " "),
        ("tab", "\t"),
        ("space", " "),
        ("newline", "\n"),
    ]
    assert [path[3] for path in lexer.paths] == [
        "whitespace -> space",
        "whitespace -> tab",
        "whitespace -> space",
        "whitespace -> newline",
    ]


def test_each_space_is_emitted_with_its_source_position():
    tokens, errors = lex("a  b ")

    assert errors == []
    assert [(token.type, token.lexeme, token.line, token.column) for token in tokens] == [
        ("id", "a", 1, 1),
        ("space", " ", 1, 2),
        ("space", " ", 1, 3),
        ("id", "b", 1, 4),
        ("space", " ", 1, 5),
    ]


def test_space_columns_restart_after_newline():
    tokens, errors = lex("   \n  x ")

    assert errors == []
    assert [(token.type, token.line, token.column) for token in tokens] == [
        ("space", 1, 1),
        ("space", 1, 2),
        ("space", 1, 3),
        ("newline", 1, 4),
        ("space", 2, 1),
        ("space", 2, 2),
        ("id", 2, 3),
        ("space", 2, 4),
    ]


def test_keyword_prefix_prinx_is_an_identifier():
    tokens, _ = lex("prinx(")

    assert tokens[0].type == "id"
    assert tokens[0].lexeme == "prinx"


def test_keyword_prefix_prin5_is_an_identifier():
    tokens, errors = lex("prin5;")

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == [("id", "prin5"), (";", ";")]


def test_keyword_followed_by_operator_is_an_error():
    tokens, errors = lex("prin+")

    assert tokens == []
    assert errors
    assert (errors[0].line, errors[0].column) == (1, 1)


@pytest.mark.parametrize(
    ("source", "expected_types"),
    [
        ("1+-2;", ["wharfa_lit", "+", "-", "wharfa_lit", ";"]),
        ("1*-2;", ["wharfa_lit", "*", "-", "wharfa_lit", ";"]),
        ("1/-2;", ["wharfa_lit", "/", "-", "wharfa_lit", ";"]),
        ("1%-2;", ["wharfa_lit", "%", "-", "wharfa_lit", ";"]),
        ("value<=-2;", ["id", "<=", "-", "wharfa_lit", ";"]),
        ("value==-2;", ["id", "==", "-", "wharfa_lit", ";"]),
        ("value=-2;", ["id", "=", "-", "wharfa_lit", ";"]),
        ("value+=-2;", ["id", "+=", "-", "wharfa_lit", ";"]),
    ],
)
def test_operator_can_be_followed_by_a_negative_operand(source, expected_types):
    tokens, errors = lex(source)

    assert errors == []
    assert [token.type for token in tokens if token.type != "space"] == expected_types


def test_subtraction_followed_by_negative_number_needs_a_space():
    tokens, errors = lex("1--2")

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == [("wharfa_lit", "1"), ("comment_sl", "--2")]


def test_identifier_at_eof_is_not_delimited():
    tokens, errors = lex("finalName")

    assert tokens == []
    assert [(error.text, error.line, error.column) for error in errors] == [("finalName", 1, 1)]


def test_identifier_delimiter_and_diagram_trace_use_updated_state_ids():
    lexer = Lexer("x;", trace=True)

    tokens, errors = lexer.run()

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == [("id", "x"), (";", ";")]
    assert lexer.paths[0][3] == "0 -> 200 -> 201*"


@pytest.mark.parametrize("quote", ['"', "'"])
def test_raw_newline_is_allowed_inside_strings(quote):
    source = f"{quote}first\nsecond{quote};"

    tokens, errors = lex(source)

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == [("strina_lit", source[:-1]), (";", ";")]


def test_delimiter_changes_allow_newline_and_negative_operator_boundaries():
    tokens, errors = lex("1+\n2; a,\nb;")

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens if token.type != "space"] == [
        ("wharfa_lit", "1"), ("+", "+"), ("newline", "\n"),
        ("wharfa_lit", "2"), (";", ";"), ("id", "a"), (",", ","),
        ("newline", "\n"), ("id", "b"), (";", ";"),
    ]


def test_keyword_parenthesis_and_newline_delimiters_are_applied():
    tokens, errors = lex("flo(x; inpub\n belial\n belsa (x;")

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens if token.type != "space"] == [
        ("flo", "flo"), ("(", "("), ("id", "x"), (";", ";"),
        ("inpub", "inpub"), ("newline", "\n"), ("belial", "belial"),
        ("newline", "\n"), ("belsa", "belsa"), ("(", "("),
        ("id", "x"), (";", ";"),
    ]


@pytest.mark.parametrize("keyword", ["strina", "wharfa", "flo", "trua", "lis", "glossare"])
def test_each_datatype_keyword_accepts_open_parenthesis(keyword):
    tokens, errors = lex(f"{keyword}(x;")

    assert errors == []
    assert [(token.type, token.lexeme) for token in tokens] == [
        (keyword, keyword), ("(", "("), ("id", "x"), (";", ";")
    ]


def test_qa_lexer_delimiter_additions_and_removals_are_applied():
    assert "(" in delim_datatype
    assert NEWLINE in delim_io and NEWLINE in delim_logic
    assert NEWLINE in delim_plus and "-" in delim_plus
    assert NEWLINE in delim_arithmetic and "-" in delim_arithmetic
    assert NEWLINE in delim_oper and NEWLINE in delim_equality
    assert NEWLINE in delim_equal and NEWLINE in delim_augoper
    assert NEWLINE in delim_openparen and NEWLINE in delim_comma
    assert NEWLINE in delim_logic_newline and NEWLINE in delim_deleo and NEWLINE in delim_const
    assert {"+", "-", "*", "/", "%", "<", ">", "=", "!"} <= delim_id
    assert assops <= delim_id
    assert EOF not in delim_id
    assert EOF in delim_num
    assert {"(", "-"}.isdisjoint(delim_insid)
    assert NEWLINE in delim_openbracket and "(" not in delim_openbracket
    assert {"<", ">", "+", "-", "*", "/", "%", "=", "!"} <= delim_closeparen
    assert "]" not in delim_closeparen
    assert ";" not in delim_closecurly
    assert NEWLINE in delim_dqopen and NEWLINE in delim_sqopen
    assert {"<", ">", "-", "*", "/"}.isdisjoint(delim_dqclose)
    assert {"<", ">", "-", "*", "/"}.isdisjoint(delim_sqclose)
    assert {"<", ">", "=", "!", "+", "-", "*", "/", "%"} <= delim_closeparen
    assert "-" not in delim_scolon
    assert {":", "+", "-", "*", "/", "%", "<", ">", EOF}.isdisjoint(delim_bool)
