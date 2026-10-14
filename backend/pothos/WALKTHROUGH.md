# Lexer panel walkthrough

## Run the app and tests

From the repository root, start the web app:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open the local address printed by Flask. Run the lexer regression tests in a
second terminal:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_lexer.py
```

Choose **Run** in the panel after entering an example. Enable **Show TD states**
to display each token's path.

## Live examples

Enter each source snippet separately. Token names and lexemes below are the
expected lexical output; the lexer does not check whether the snippet is a
complete program.

| Input | Expected output | State function |
|---|---|---|
| `flo x;` | `flo("flo")`, `id("x")`, `;(";")` | `_td1_reserved_words`, `_td2_reserved_symbols`, `_td3_identifiers` |
| `12.5;` | `flo_lit("12.5")`, `;(";")`; the serialized value is `12.5` | `_td4_integer_literals`, `_td2_reserved_symbols` |
| `msg = "a\nb";` | `id("msg")`, `=("=")`, `strina_lit("\"a\\nb\"")`, `;(";")` | `_td2_reserved_symbols`, `_td3_identifiers`, `_td5_strings_comments` |
| `/-- note`<br>`inside --/` | one `comment_ml` token containing both lines | `_td5_strings_comments` |
| `5.` | lexical error at line 1, column 1: `5.` needs a digit after the point | `_td4_integer_literals` |
| `"bad\x"` | lexical error at line 1, column 5: invalid escape `\x` | `_td5_strings_comments` |

`_td1_reserved_words` recognizes keywords, `_td2_reserved_symbols` recognizes
operators and delimiters, `_td3_identifiers` scans names,
`_td4_integer_literals` scans numbers, and `_td5_strings_comments` scans
strings and comments. Shared transitions can pass through more than one
state function while a token is being scanned.
