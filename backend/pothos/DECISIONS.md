# Lexer decisions

This table records how the current lexer resolves rules and delimiter
differences. The lexer reports lexical errors and leaves syntax and semantic
checks to later stages.

| # | rule | what the documentation says | what the lexer does | why |
|---:|---|---|---|---|
| 1 | semicolon delimiter | `delim_scolon` has no newline or numbers | adds newline and numbers | accepts lines ending with `;` and loop headers |
| 2 | open curly delimiter | `delim_opencurly` has no newline or `}` | adds newline and `}` | accepts multi-line blocks and empty blocks |
| 3 | open parenthesis delimiter | `delim_openparen` has no `)` or `{` | adds `)` and `{` | accepts empty calls and block headers |
| 4 | open bracket delimiter | `delim_openbracket` has no `]` | adds `]` | accepts empty lists |
| 5 | number delimiter | `delim_num` has no comma or colon | adds comma and colon | accepts lists, mappings, and argument lists |
| 6 | identifier delimiter | `delim_id` has no `(` or `,` | adds `(` and `,` | accepts calls and parameter lists |
| 7 | equal delimiter | `delim_equal` has no quotes | adds both quote characters | accepts a string immediately after `=` |
| 8 | close bracket delimiter | `delim_closebracket` has no `[` or math operators | adds `[` and math operators, but not eof | accepts chained indexing and arithmetic; a final `]` at eof still errors |
| 9 | close parenthesis delimiter | `delim_closeparen` has no math operators | adds math operators, but not eof | accepts arithmetic after grouped expressions; a final `)` at eof still errors |
| 10 | close curly delimiter | `delim_closecurly` has no math operators, comma, or eof | adds math operators, comma, and eof | accepts expressions, collections, and a final block |
| 11 | augmented operators | the delimiter table omits quotes | keeps quotes in `delim_augoper` | accepts a string after an augmented assignment |
| 12 | membership delimiter | the name is `delim_insit` in older code and `delim_insid` in the current names | uses `delim_insid` | aligns the set name with the membership operator |
| 13 | structural delimiter | the name is `delim_struct` in older code and `delim_struc` in the current names | uses `delim_struc` | aligns the set name with the documented name |
| 14 | membership quotes | the character definitions use typographic quotes | uses straight ASCII quotes | matches source characters accepted by the lexer |
| 15 | comment character sets | comment delimiters include non-ASCII characters | removes non-ASCII characters from comment sets | non-ASCII is an error in every context |
| 16 | single-line comment | `--` reads through the line; a separate rule defines `--/` as a closer | a single-line comment cannot be followed by `/`; `--` followed by newline is empty | reports stray closers and accepts empty comments |
| 17 | multi-line opener | the opener set is used but not separately defined | defines `delim_mlcomment_open` as space, printable ASCII, and newline | gives the opener an explicit set for the transition |
| 18 | relational characters | the regular definition lists `==` | `relop_ch` contains the single character `=` | a character set cannot contain a two-character operator |
| 19 | `belsa` | delimiter table maps it to `delim_block` | uses `delim_logic` | permits a condition after the keyword |
| 20 | `const` | delimiter table maps it to a generic delimiter | uses `delim_const` | follows the variable-operation delimiter set |
| 21 | `glossare` | delimiter table maps it to an I/O delimiter | uses `delim_datatype` | permits a declared function name after the keyword |
| 22 | sign and numbers | a minus may appear with a numeric literal | minus is a separate operator token | keeps signs outside number lexemes |
| 23 | leading zeros | leading zeros do not count as significant digits | accepts them and converts the lexeme to its integer value | preserves source spelling while producing the numeric value |
| 24 | integer length | the integer part allows eight significant digits | ends the token after eight; a following digit starts another token | implements the state diagram's split |
| 25 | fractions | a float has one to four digits after the decimal point | accepts one to four digits; extra digits start a new integer token | enforces the fractional limit |
| 26 | decimal point placement | both sides of the point require digits | reports `5.` and `.5` as lexical errors | rejects incomplete float spellings |
| 27 | escapes | strings allow `\n`, `\t`, `\0`, `\"`, `\'`, and `\\` | accepts those six escapes and reports other escapes at the backslash | keeps string contents explicit and recoverable |
| 28 | unterminated strings | a string must end with its matching quote | reports one error through the end of the line, then resumes on the next line | avoids treating the remainder of the line as code |
| 29 | keyword boundary | recognize reserved words and identifiers | scans the whole word before deciding whether it is a keyword | keeps keyword prefixes such as `printx` as identifiers |
| 30 | truth literals | `Trua` and `Inaccu` are reserved words | emits both with token type `trua_lit` | gives truth values one literal token type |
| 31 | non-ASCII | comments and strings may include their character classes | reports non-ASCII as an error in source, strings, and comments | keeps the accepted alphabet consistent |
| 32 | function-name length | function names must have at least three characters | does not check the minimum length in the lexer | leaves the rule to the parser |
| 33 | conflicting rule order | specific rules/examples, general rules, regular definitions, transition diagrams, delimiter tables | follows that priority when those sources disagree | selects one consistent interpretation |
| 34 | plus sign before a number | `+25` is listed as an error case | tokenizes `+25` as `+` and `wharfa_lit("25")` without an error | the lexer recognizes the plus symbol separately and does not reject this token sequence |
