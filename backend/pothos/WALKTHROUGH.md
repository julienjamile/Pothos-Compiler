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
| `wharfa(x;` / `strina(x;` / `trua(x;` / `lis(x;` / `flo(x;` / `glossare(x;` | Each datatype keyword accepts `(` through `delim_datatype`; the scanner emits the keyword and then scans the parenthesis normally | TD1 accepting states 81, 125, 130, 142, 43, 52; `delim_datatype` |
| `flo x;` | `flo("flo")`, `id("x")`, `;(";")` | `_td1_reserved_words`, `_td2_reserved_symbols`, `_td3_identifiers` |
| `a b;` | `id("a")`, `space(" ")`, `id("b")`, `;(";")`; an identifier ending at EOF is an error because EOF is not in `delim_id` | `Lexer.run` emits whitespace tokens; `_td3_identifiers` checks `delim_id` |
| `12.5;` | `flo_lit("12.5")`, `;(";")`; the serialized value is `12.5` | `_td4_integer_literals`, `_td2_reserved_symbols` |
| `1.23456` | One `flo_lit` has normalized lexeme/value `1.2346`; digits after the fourth are consumed and rounded half up | `_td4_integer_literals` supplemental state 300; `_accept`; `token_to_dict` |
| `000000` / `0.00000` | Lexemes normalize to `0` / `0.0`; float lexemes keep at least one fractional digit | `_accept` |
| `abcdefghijklmnopqrstu;` | Error text is the first 20 characters; the outer loop sends the 21st (`u`) through state 0, where it is scanned as `id("u")`, followed by `;` | `_td3_identifiers` state 239 and overflow recovery |
| `1+-2;` | `wharfa_lit("1")`, `+`, `-`, `wharfa_lit("2")`, `;`; `1--2` starts a line comment at `--` | `_td2_reserved_symbols`, numeric delimiters in `charsets.py` |
| `msg = "a\nb";` | `id("msg")`, `=("=")`, `strina_lit("\"a\\nb\"")`, `;(";")` | `_td2_reserved_symbols`, `_td3_identifiers`, `_td5_strings_comments` |
| `/-- note`<br>`inside --/` | one `comment_ml` token containing both lines | `_td5_strings_comments` |
| `5.` | `flo_lit("5.0")`; the diagram accepts the point with no fractional digit and normalization supplies `.0` | `_td4_integer_literals`, `_accept` |
| `123456789;` | Error text is `12345678`; the outer loop sends the excess `9` through state 0, where it is scanned as `wharfa_lit("9")`, followed by `;` | `_td4_integer_literals` state 257 and overflow recovery |
| `"bad\x"` | lexical error at line 1, column 5: invalid escape `\x` | `_td5_strings_comments` |

`_td1_reserved_words` recognizes keywords, `_td2_reserved_symbols` recognizes
operators and delimiters, `_td3_identifiers` scans names,
`_td4_integer_literals` scans numbers, and `_td5_strings_comments` scans
strings and comments. Shared transitions can pass through more than one
state function while a token is being scanned.
