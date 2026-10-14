# Pothos Lexer Behavior

This guide describes the language behavior currently implemented by the lexer.
As Pothos rules evolve, update the character sets, state transitions, examples,
and tests together.

## Token recognition

- The lexer starts each token at state 0 and dispatches to one of five state
  groups: reserved words, symbols, identifiers, integer literals, or strings
  and comments.
- A word that stops matching a reserved word can restart as an identifier from
  its first character. For example, `ant`, `stri`, `pass`, and `belial1` are
  identifiers.
- Identifiers begin with a letter and can contain letters, digits, and `_`.
  They may contain at most 20 characters.
- Integer literals may contain up to 8 significant digits. Leading zeroes do
  not count toward that limit. A minus sign followed immediately by digits is
  part of the integer literal, so `-5` is one token and `3-2` becomes `3` and
  `-2`.
- Reserved words and symbols use their own text as the token type, except
  `Trua` and `Inaccu`, which use `trua_lit`. Identifiers, integer literals,
  strings, and comments use the token types defined in `tokens.py`.
- Reserved words are case-sensitive. A differently cased spelling that is not
  itself a reserved word is treated as an identifier.

## Delimiters and symbols

- Character classes and delimiter sets are centralized in `lexer/charsets.py`.
  State branches use these named sets so a character-class change can be made
  in one place.
- `/` ends as a symbol when followed by a character in `delim_arithmetic`. The
  sequence `/-` uses state 154's two-character retraction behavior so the
  lexer emits `/` and processes the following characters again.
- `innum` uses the same delimiter set as the other flow-control words.
- A complete reserved word followed by a character outside its delimiter set
  is a lexical error by default. For example, `belial{` is an error. Set
  `COMPLETE_KEYWORD_FALLS_BACK_TO_ID = True` in `lexer/lexer.py` if the desired
  behavior is to treat `belial` as an identifier in this case.

## Strings and comments

- Strings may use either quote style. Backslash escapes are limited to `\"`,
  `\'`, `\\`, `\n`, `\t`, and `\0`.
- A raw newline inside a string, an unsupported escape, a non-ASCII character,
  or a missing closing quote produces a lexical error. An invalid string is
  not emitted as a token.
- Single-line comments begin with `--` and continue to a newline or end of
  input.
- Multi-line comments begin with `/--` and close at the first `--/`. Comments
  do not nest. A closer without a preceding opener is an error.
- `skip_comments=True` omits comment tokens while still recognizing comments.

## Errors and state tracing

- A character with no transition from the current state produces a lexical
  error. Outside a string or comment, recovery skips input to the next
  whitespace, bracket, separator, or quote so scanning can continue.
- Errors inside strings and comments are recorded while scanning continues to
  their end. The malformed string or comment is then omitted from the tokens.
- `Lexer(source, trace=True)` records the state path used to produce each token.
  `--trace` enables the same information in the command-line interface, and
  the API's `trace` option includes the path in each serialized token.
- `_accept` reads a delimiter and retracts it so the next token can consume it.
  A single `*` in a state path represents one-character retraction; state 154
  uses two-character retraction.

## Examples to keep aligned with the rules

| Source | Current behavior |
|---|---|
| `ant` | Identifier |
| `Trua` | `trua_lit` |
| `TRUA` | Identifier |
| `-5` | One integer literal |
| `/-- inner --/` | One multi-line comment |
| `/-- outer /-- inner --/` | Comment ends at the first `--/`; remaining text is lexed as source |
| `1.5` | Lexical error |
| `1,000` | Integer, comma, integer |

When a rule changes, revise this guide and add or update focused examples in
the lexer tests.
