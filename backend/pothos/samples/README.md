# Pothos lexer samples

These files are source examples for the current lexer. They exercise tokenization and lexical errors; they do not claim that the syntax phase accepts every example.

- `01_keywords_and_control.pths` — revised reserved words, declarations, calls, conditionals, switch labels, loops, and return forms.
- `02_operators_and_grouping.pths` — arithmetic, relational, assignment, parentheses, lists, and indexing.
- `03_literals_and_identifiers.pths` — integer and float boundaries, identifier length, both quote styles, and escape sequences.
- `04_comments_and_whitespace.pths` — tilde comments, multiline comments, tabs, and newlines.
- `05_lexical_errors.pths` — representative invalid characters, overlong names/numbers, escape errors, and continued scanning.

`sample.pths` remains the compact walkthrough program. `valid.pth` is the reserved-word inventory exercise, and `errors.pths` is the older lexical-error collection updated for tilde comments.
