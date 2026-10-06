# Pothos Lexer

The lexical analyzer for **Pothos** (BSCS 3-2 Group 3, PLM: Automata Theory & Formal Languages).

It is a hand-written state machine in plain Python 3 (standard library only). Every
`state` number in the code is the state number in our transition diagrams TD1–TD5,
so you can follow the code on the diagrams line by line.

## Structure

```
pothos/
├── main.py                  CLI: lex a .pths file, or use the interactive prompt
├── lexer/
│   ├── __init__.py          exports tokenize, Lexer, Token, LexicalError
│   ├── charsets.py          every IV.B / IV.E set, named exactly as in the PDF
│   ├── tokens.py            Token(type, lexeme, line, column) + token-type names
│   ├── errors.py            LexicalError(message, line, column, text)
│   └── lexer.py             the state machine: one branch per TD state
├── samples/
│   ├── sample.pths          a valid program
│   └── errors.pths          11 lines, one lexical error each
├── tests/                   108 unittest tests (one file per TD + PDF examples + CLI)
├── README.md                this file
├── DECISIONS.md             every place the PDF conflicts, and what the lexer does
└── WALKTHROUGH.md           plain-language tour of the code, part by part
```

Pothos source files use the **`.pths`** extension.

## Requirements

Python 3.8 or newer. No packages to install.

## Running

Run these from inside the `pothos/` folder.

```bash
python main.py samples/sample.pths            # token table, then errors
python main.py samples/errors.pths            # shows all 11 errors
python main.py --no-comments samples/sample.pths   # hide comment tokens
python main.py --trace samples/sample.pths    # show each token's TD state path
python main.py                                 # interactive prompt
```

Interactive prompt: type or paste code. An **empty line** lexes what you typed so far.
Type `:quit` to exit.

Output looks like this:

```
Line | Col | Lexeme                                   | Token
-----+-----+------------------------------------------+-----------
   2 |   1 | msg                                      | id
   2 |   5 | =                                        | =
   2 |   7 | "Hello, World!"                          | strina_lit
```

Lexical errors come after the table:

```
Lexical Error [line 2, col 1]: identifier exceeds 20 characters (III.B.3): 'studentRegistrationNumber2026'
```

Exit codes: `0` = no lexical errors, `1` = lexical errors found, `2` = file cannot be read.

## Using it from Python

```python
from lexer import tokenize

tokens, errors = tokenize('lis x = -5;')
for t in tokens:
    print(t.line, t.column, t.lexeme, t.type)
for e in errors:
    print(e)                 # Lexical Error [line L, col C]: message: 'text'

tokens, errors = tokenize(source, skip_comments=True)    # drop comment tokens
```

* `Token` fields: `type`, `lexeme`, `line`, `column` (1-based).
* Token types: a reserved word or symbol is its own type (`belial`, `wharfa`, `==`, `;` …).
  Literals are `id`, `wharfa_lit`, `strina_lit`, `trua_lit` (`Trua` / `Inaccu`).
  Comments are `comment_sl` (`-- …`) and `comment_ml` (`/-- … --/`).
* Errors never stop the lexer. It records the error, skips to the next whitespace or
  delimiter, and keeps going, so one run reports every error.
* To get state paths: `Lexer(source, trace=True)`. After `.run()`, `.paths` has one
  path string per token.

## Tests

```bash
python -m unittest                              # quick: 108 tests, OK
python -m unittest discover -s tests -v         # verbose, one line per test
python -m unittest tests.test_td4_integers      # a single file
```

| File | Covers |
|---|---|
| `test_charsets.py` | the sets match IV.B / IV.E (and A3, X2) |
| `test_td1_reserved_words.py` | all 26 reserved words, delimiters, A1 fallback, D |
| `test_td2_symbols.py` | all 26 symbols, `/` retract 2 (state 154), negatives |
| `test_td3_identifiers.py` | 1–20 characters, `_` rules, delim_id |
| `test_td4_integers.py` | 1–8 significant digits, leading zeros, delim_int |
| `test_td5_strings_comments.py` | strings, escapes, both comment kinds |
| `test_pdf_examples.py` | 145 examples from the PDF, each labelled OK / LATER / LEX |
| `test_recovery_and_positions.py` | line/column numbers, many errors in one run |
| `test_cli.py` | `main.py` output, flags and exit codes |

In `test_pdf_examples.py`: **OK** = valid code, **LATER** = lexes cleanly but the
parser/semantic phase rejects it (e.g. `first name`, `y = 1,000;`), **LEX** = a
lexical error.

## Where to read next

* **DECISIONS.md**: every PDF conflict (A1–A3, B1–B3, C, D, E1–E6, X1–X4), with page and
  TD state numbers. **One decision is still open: D** (`belial{`).
* **WALKTHROUGH.md**: how each part works, in plain language.
