"""
charsets.py - every character set and delimiter set used by the Pothos lexer.

Each set is defined once so lexer.py can use the same names as the transition
diagram edge labels, for example `if c in delim_flow:`.

EOF is not a real character, so it is represented by the sentinel string
EOF = "<eof>". It is longer than one character, so it can never be confused
with a character of the source file. Sets that include the end-of-file marker
contain this sentinel.
"""

EOF = "<eof>"

SPACE = " "
NEWLINE = "\n"
TAB = "\t"

# ---------------------------------------------------------------------------
# Pothos character classes
# ---------------------------------------------------------------------------
caplet = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
lowlet = set("abcdefghijklmnopqrstuvwxyz")
digit = set("123456789")                      # NOTE: no 0
numbers = {"0"} | digit
mathop = {"+", "-", "*", "/", "%"}
relop_ch = {"<", ">", "=", "!"}

# "any printable character, tab": printable ASCII is code 32 (space) .. 126 (~)
ascii = {chr(code) for code in range(32, 127)} | {TAB}

ascii_str_dq = ascii - {'"', "\\", NEWLINE}
ascii_str_sq = ascii - {"'", "\\", NEWLINE}
ascii_comment_sl = ascii - {NEWLINE}
ml_char = (ascii | {NEWLINE}) - {"-"}
ml_char_ns = (ascii | {NEWLINE}) - {"-", "/"}

# The six escape sequences, written as the two source characters.
# Escape sequences are represented by their two source characters.
escape = {'\\"', "\\'", "\\\\", "\\n", "\\t", "\\0"}

letter = caplet | lowlet
alphanum = letter | numbers
underscore = {"_"}
whitespace = {SPACE, NEWLINE, TAB}

# ---------------------------------------------------------------------------
# Delimiter sets used by the transition rules
# ---------------------------------------------------------------------------
delim_space = whitespace | {EOF}
delim_quote = {"'", '"'}
delim_dquote = ascii_str_dq | {"\\", '"'}
delim_squote = ascii_str_sq | {"\\", "'"}
delim_operand = delim_space | letter | numbers | delim_quote | {"(", "[", "{", "-"}

delim_id = delim_space | {"(", ")", "{", "}", "[", "]", ";", ",", ":"} | mathop | relop_ch
delim_int = delim_space | {"(", ")", "{", "}", "[", "]", ";", ",", ":"} | mathop | relop_ch
delim_str = delim_space | {"(", ")", "{", "}", "[", "]", ";", ",", ":"} | mathop | relop_ch
delim_close = delim_space | {"(", ")", "{", "}", "[", "]", ";", ",", ":"} | mathop | relop_ch
delim_rbrace = delim_close | {EOF}

delim_relop = delim_operand
delim_mathop = delim_operand
delim_minus = delim_space | letter | numbers | delim_quote | {"(", "[", "{"}   # no '-': -- starts a comment
delim_assops = delim_operand
delim_colon = delim_operand
delim_reor = delim_space | delim_quote | {"(", "[", "{", "-"}
delim_flow = delim_space | {"("}

# A single-line comment can end at a newline or at the end of the source.
delim_scomment_start = (ascii - {"/"}) | {NEWLINE, EOF}
delim_mcomment_start = ascii | {NEWLINE}
delim_mcomment_end = ascii | {NEWLINE, EOF}

delim_bool = delim_space | {"(", ")", "{", "}", "[", "]", ";", ",", ":"} | mathop | relop_ch
delim_block = delim_space | {"{"}
delim_stmt = delim_space | {";"}
delim_open_paren = delim_operand | {")"}
delim_open_brack = delim_operand | {"]"}
delim_open_brace = delim_operand | {"}"}
delim_comma = delim_operand
delim_term = delim_space | letter | {"}", "-", "/", EOF}

# Characters allowed after a backslash inside a string.
delim_escape = {'"', "'", "\\", "n", "t", "0"}

# ---------------------------------------------------------------------------
# Edge labels on the TDs that are set expressions, named once here.
# ---------------------------------------------------------------------------
alphanum_us = alphanum | underscore                     # TD3 label "alphanum, _"
delim_minus_no_numbers = delim_minus - numbers          # TD2 141 -> 142 "delim_minus − numbers"
ascii_comment_sl_no_slash = ascii_comment_sl - {"/"}    # TD5 278 -> 280 "ascii_comment_sl − {/}"
newline_eof = {NEWLINE, EOF}                            # TD5 278 -> 279, 280 -> 281 "newline, eof"
