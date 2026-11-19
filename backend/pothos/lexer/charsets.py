"""
charsets.py - Pothos character classes and delimiter sets.

EOF is represented by the sentinel string "<eof>", which cannot be confused
with a source character.

Current delimiter choices:
  Statement endings use the current delimiter sheet's letter, brace, and EOF followers.
  Curly blocks may open across lines and close before another block.
  Parenthesis and bracket delimiters allow adjacent calls and indexing.
  Numeric and identifier delimiters allow collection and argument syntax.
  Assignment, grouping, and closing delimiters allow adjacent expressions.
  Comments accept ASCII text and end at their closing marker or line ending.
  Relational operators are checked one character at a time.
"""

EOF = "<eof>"

SPACE = " "
NEWLINE = "\n"
TAB = "\t"

whitespace = {SPACE, NEWLINE, TAB}
caplet = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
lowlet = set("abcdefghijklmnopqrstuvwxyz")
letter = caplet | lowlet
digit = set("123456789")
numbers = {"0"} | digit
alphanum = letter | numbers
underscore = {"_"}
mathop = {"+", "-", "*", "/", "%"}
relop_ch = {"<", ">", "=", "!"}  # equality operators are checked one character at a time
assops = {"+=", "-=", "*=", "/=", "%="}
ascii = {chr(code) for code in range(32, 127)} | {TAB}
ml_char = (ascii | whitespace) - {"-"}

delim_space = {SPACE, TAB}
delim_quote = {"'", '"'}
delim_bool = delim_space | delim_quote | {NEWLINE, ")", "}", "]", ";", ","} | mathop | relop_ch
delim_block = delim_space | {NEWLINE, "{"}
delim_if = delim_space | {"(", NEWLINE}
delim_loop = delim_space | {"(", NEWLINE}
delim_switch = delim_space | {"(", NEWLINE}
delim_case = delim_space | {NEWLINE, "(", "'", "-", '"', "{", "["}
delim_default = delim_space | {NEWLINE, ":"}
delim_cyc = delim_space | {"(", NEWLINE}
delim_void = delim_space | {NEWLINE}
delim_stmt = delim_space | {NEWLINE, ";"}
delim_openparen = delim_space | {NEWLINE} | letter | numbers | delim_quote | {"(", "[", "-", ")", "{"}  # allows adjacent calls and blocks
delim_openbracket = delim_space | {NEWLINE} | letter | numbers | delim_quote | {"[", "{", "-"}
delim_opencurly = delim_space | letter | numbers | delim_quote | {NEWLINE}
delim_comma = delim_space | {NEWLINE} | letter | numbers | delim_quote | {"(", "[", "{", "-"}
delim_colon = delim_space | {NEWLINE, "-", "[", "{"} | letter | numbers | delim_quote
delim_id = delim_space | {NEWLINE, "[", "]", "}", ")", ";", "(", ",", ":"} | mathop | relop_ch
delim_num = delim_space | {NEWLINE, ";", "]", "}", ")", ","} | mathop | relop_ch

alphanum_us = alphanum | underscore

# Escape spellings shown in the string transition diagram.
escape = {'\\"', "\\'", "\\\\", "\\n", "\\t", "\\0", "\\{", "\\}"}
special_characters = {
    chr(code) for code in range(128, 0x110000) if chr(code).isprintable()
}
comment_char = {chr(code) for code in range(32, 126)} | {TAB, NEWLINE} | special_characters
delim_comments = delim_space | letter | {NEWLINE, EOF, "~"}
delim_datatype = delim_space | {NEWLINE}
delim_io = delim_space | {"(", NEWLINE}
delim_logic = delim_space | delim_quote | {"(", NEWLINE}
delim_struc = delim_space | {NEWLINE, ";", "(", "[", "{", "-"}
delim_deleo = delim_space | {NEWLINE}
delim_const = delim_space | {NEWLINE}
delim_insid = delim_space | {NEWLINE, "{", "[", '"', "'"}  # string delimiters use plain quotes
delim_logic_newline = delim_logic | {NEWLINE}
delim_plus = delim_space | {NEWLINE, "-", "="} | letter | numbers | delim_quote | {"("}
delim_arithmetic = delim_space | {NEWLINE, "-", "="} | letter | numbers | delim_quote | {"("}
delim_oper = delim_space | {NEWLINE, "=", "-"} | delim_quote | letter | numbers | {"("}
delim_equality = delim_space | {NEWLINE} | delim_quote | letter | numbers | {"(", "[", "{", "-"}
delim_equal = delim_space | {NEWLINE} | letter | numbers | delim_quote | {"(", "[", "{", "-"}  # allows a string immediately after =
delim_augoper = delim_equal  # augmented operators use the revised delim_equal set
delim_closeparen = delim_space | {NEWLINE, ")", "{", "}", ";", ","} | relop_ch | mathop  # allows an operator after a grouped expression
delim_closebracket = delim_space | {NEWLINE, ")", "]", "}", ";", ",", "["} | relop_ch | mathop
delim_closecurly = delim_space | delim_quote | {NEWLINE, ")", "]", "}", ";", ","} | relop_ch
delim_dqopen = delim_space | ascii | {NEWLINE}
delim_dqclose = delim_space | {NEWLINE, ",", ")", "]", "}", ";", ":"} | (relop_ch - {"<", ">"}) | (mathop - {"-", "*", "/"})
delim_sqopen = delim_space | ascii | {NEWLINE}
delim_sqclose = delim_space | {NEWLINE, ",", ")", "]", "}", ";", ":"} | (relop_ch - {"<", ">"}) | (mathop - {"-", "*", "/"})
delim_scolon = delim_space | letter | {NEWLINE, "}", EOF}
delim_slcomment = (ascii - {"/"}) | {NEWLINE, EOF}  # slash starts the closing marker
delim_mlcomment_open = delim_space | ascii | {NEWLINE}  # allowed content after a multi-line comment opener
delim_mlcomment_close = delim_space | letter | {NEWLINE, "}", EOF, "/"}  # closing marker and comment endings
