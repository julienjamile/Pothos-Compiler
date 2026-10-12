# Walkthrough: how the Pothos lexer works

This guide follows the code in the order you would explain it in a defense:
**character sets → tokens and errors → the engine → TD2 → TD3 → TD1 → TD4 → TD5 → CLI → tests.**
Keep the TD diagrams open next to it. Every state number below is a TD state number.

---

## 1. Character sets: `lexer/charsets.py`

Every set from **IV.B** (characters) and **IV.E** (delimiters) is defined **once**, under
the same name as in the PDF:

```python
ascii        = {chr(code) for code in range(32, 127)} | {TAB}
ml_char      = (ascii | {NEWLINE}) - {"-"}
delim_minus  = delim_space | letter | numbers | delim_quote | {"(", "[", "{"}   # no '-'
delim_escape = {'"', "'", "\\", "n", "t", "0"}                                 # A3
```

* **eof** is not a real character, so it is a sentinel string `EOF = "<eof>"`. It is longer
  than one character, so it can never match a real character. Sets that "include eof" in the
  PDF simply contain it.
* A few helper sets have names that are TD edge labels, e.g.
  `delim_minus_no_numbers = delim_minus - numbers` (the TD2 141 → 142 edge) and
  `alphanum_us = alphanum | {"_"}`.

The lexer never writes a character list by hand. It always uses these names, so a change to
a set happens in one place.

## 2. Tokens and errors: `lexer/tokens.py`, `lexer/errors.py`

* `Token(type, lexeme, line, column)` is one token. `line` and `column` are 1-based.
* The **type** of a reserved word or symbol is the word or symbol itself (`belial`, `==`,
  `;`). Literals are `id`, `wharfa_lit`, `strina_lit`, `trua_lit`. Comments are `comment_sl`
  and `comment_ml`.
* `Trua` and `Inaccu` are reserved words, but their token type is `trua_lit` (IV.D).
* `LexicalError(message, line, column, text)` prints as
  `Lexical Error [line 2, col 1]: identifier exceeds 20 characters (III.B.3): 'studentReg…'`.

## 3. The engine: `lexer/lexer.py` (top part)

**The main loop (`run`)** skips whitespace, then calls `_scan_token` once per token. Whitespace
is not a token; it is only a delimiter that ends tokens.

**`_scan_token`** starts at **state 0** and keeps calling the method that owns the current
state, until a token is accepted or an error is recorded:

| States | Method | TD |
|---|---|---|
| 0 | `_state_0` | shared start state |
| 1–136 | `_td1_reserved_words` | TD1 |
| 137–195 | `_td2_reserved_symbols` | TD2 |
| 196–235 | `_td3_identifiers` | TD3 |
| 236–271 | `_td4_integer_literals` | TD4 |
| 272–286 (+ 192, 194) | `_td5_strings_comments` | TD5 |

Inside each method there is **one `if state == N:` branch per state**, and **one line per
outgoing edge**:

```python
if state == 196:                                  # 1 character
    if c in alphanum_us: return self._go(198)
    if c in delim_id:    return self._accept(start, 197, ID)  # 196 -> 197*
    return self._error(start, ...)                 # no edge = error (B1)
```

Three helpers do all the work:

* **`_go(N)`**: take an edge. Consume the current character and move to state N.
* **`_accept(start, N, type)`**: take the delimiter edge into final state N and emit the
  token.
* **`_error(start, message)`**: no matching edge. Record the error, skip ahead, continue.

### Why retraction happens (`*` and `**`)

A token only ends when the lexer sees the character **after** it. In `x=1`, the lexer knows
`x` is finished only when it reads `=`. That `=` belongs to the next token, so it is
**given back** (retract 1). That is what `*` on a final state means.

`_accept` reads the delimiter, then moves `pos` back by `retract`. The next token starts
exactly at the delimiter. eof counts as one virtual character, so retraction works at the end
of the file too.

`**` (only state 154) gives back **2** characters (B2, see TD2).

### Errors and recovery

* **No matching edge = lexical error** (B1). The error is recorded, the lexer skips at
  least one character up to the next whitespace or one of `( ) { } [ ] ; , : " '`, and
  restarts at state 0. One run reports **every** error.
* **Inside a string or comment** (bad escape, non-ASCII character), `_error_inside` records
  the error but keeps reading to the end of that literal, then drops it. The rest of the
  line is not misread as code.

## 4. TD2: Reserved Symbols (states 137–195)

State 0 sends each symbol's first character to its own state:
`+`→137, `-`→141, `*`→145, `/`→149, `%`→155, `<`→159, `>`→163, `=`→167, `!`→171,
`(`→174, `)`→176, `[`→178, `]`→180, `{`→182, `}`→184, `,`→186, `:`→188, `;`→190.

Each symbol state either reads a second character (`<` then `=` → `<=`) or accepts on its
delimiter set:

```
'<=': 0 -> 159 -> 161 -> 162*        delimiter: delim_relop
```

**Shared states.** Some states belong to more than one TD. They are **one state** with
**one branch**, containing every TD's edges:

```python
if state == 141:                                  # read "-"  (shared: TD2, TD4, TD5)
    if c == "=":                    return self._go(143)   # TD2: -=
    if c == "-":                    return self._go(278)   # TD5: -- comment
    if c == "0":                    return self._go(254)   # TD4: -0...
    if c in digit:                  return self._go(256)   # TD4: -digit...
    if c in delim_minus_no_numbers: return self._accept(start, 142, "-")
```

* **141 (`-`)**: `-=`, a `--` comment, a negative number (`-5`), or the minus token.
  `-` followed by a digit becomes part of `wharfa_lit` (E1), so `3-2` → `3` `-2`.
* **149 (`/`)**: `/=`, the `/` token (delimiter `delim_minus`, E4), or `/-`.
* **153 (`/-`)**: a second `-` starts a `/--` comment (TD5). Otherwise it is **state 154,
  `**`**: the lexer gives back the `-` and the next character and emits only `/`. So
  `x/-y` → `x` `/` `-` `y`.
* **192 (`"`) and 194 (`'`)** are numbered in TD2, but their edges are in TD5 (strings).
  States 193 / 195 are unused (B3).

## 5. TD3: Identifiers (states 196–235)

Any letter that does not start a reserved word goes to **196**. Each following state counts
one more character:

```
196 (1 char) -> 198 (2) -> 200 (3) -> ... -> 234 (20 chars)
```

* Each counting state reads a letter, digit or `_` (`alphanum_us`) to go on, or a
  **`delim_id`** character to accept (retract 1).
* State 234 has no edge for a 21st character, so that is the
  "identifier exceeds 20 characters" error (III.B.3).
* An identifier must start with a letter: `_age` has no edge from state 0 (III.B.1.a).

```
'x': 0 -> 196 -> 197*
```

## 6. TD1: Reserved Words (states 1–136)

State 0 sends the first letter of each reserved word into TD1 (`a`→1, `b`→4, … `w`→130).
Then each state reads one more letter of the word:

```
'lis': 0 -> 72 -> 73 -> 74 -> 75*            delimiter: delim_space
```

When the whole word is read, its **delimiter set** must follow (e.g. `delim_flow` for `belial`,
`innum`; `delim_block` for `elsa`). Then the word is accepted (retract 1).

**A1: fallback to identifiers.** Many words start like a keyword but are not one (`ant`,
`stri`, `pass`, `belial1`). TD1 has no edge for them, so the lexer **goes back to the first
letter and restarts at state 196**. The trace shows this as `A1->196`:

```
'ant':     0 -> 1 -> 2 -> A1->196 -> 198 -> 200 -> 201*
'belial1': 0 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> A1->196 -> ... -> 209*
```

Case variants are identifiers too (E2). `TRUA` and `Innum` leave the TD1 path at the
wrong-case letter and fall back through A1. `Belial` never enters TD1, because no reserved
word starts with `B`, so state 0 sends it straight to 196.

**Open decision D.** A **complete** keyword followed by a character that is not in its
delimiter set **and** is not a letter, digit or `_` (e.g. `belial{`) is a lexical error by
default. Set `COMPLETE_KEYWORD_FALLS_BACK_TO_ID = True` at the top of `lexer.py` to make it
fall back to an identifier instead. See DECISIONS.md, D.

## 7. TD4: Integer Literals (states 236–271)

* `0` → **236**, which loops on more `0`s. Leading zeros do not count toward the limit.
* `1`–`9` → **238** (1 significant digit) → 240 → … → **252** (8 significant digits).
* Each state accepts on **`delim_int`** (retract 1).
* State 252 has no edge for a 9th digit: "wharfa literal exceeds 8 significant digits".
* Negative numbers come in from **141**: `-0` → 254, `-digit` → 256 → … → 270.

```
'007': 0 -> 236 -> 236 -> 238 -> 239*
'-5':  0 -> 141 -> 256 -> 257*
```

`.`, `_` and letters are not in `delim_int`, so `1.5`, `1_000`, `1e5` are lexical errors
(X4). `,` and space are in `delim_int`, so `1,000` lexes as `1 , 000`, and the parser
rejects it.

## 8. TD5: Strings and Comments (states 272–286, plus 192 / 194)

**Strings.** `"` → 192 (inside the string). 192 loops on `ascii_str_dq`, `\` → 274 (escape),
and `"` → 272 (closed), which accepts on `delim_str`. Single quotes work the same way with
194 / 277 / 275.

```
'"Hi\n"': 0 -> 192 -> 192 -> 192 -> 274 -> 192 -> 272 -> 273*
```

* After `\`, only `delim_escape` = `" ' \ n t 0` is allowed (A3). `"Hi\x"` is an error.
* A raw newline or eof before the closing quote is an "unterminated strina literal" error.

**Single-line comment.** `-` → 141, `-` → **278**. Then it loops in **280** until a newline
or eof (279 / 281, retract 1, so the newline is not part of the comment).
`--/` here is a **stray closer** error (III.A.2.b).

```
'-- note': 0 -> 141 -> 278 -> 280 -> ... -> 281*
```

**Multi-line comment** (with the A2 edges). `/` → 149, `-` → 153, `-` → **282** (inside).

* 282 loops on `ml_char` (anything but `-`); `-` → 283.
* 283: `-` → 284; anything else → back to 282 (a lone `-` is just text).
* 284: `/` → 285 (**closed**: the first `--/` wins); `-` stays in 284; anything else → 282.
* eof inside the comment is an "unterminated multi-line comment" error.

```
'/-- a-b ---/': 0 -> 149 -> 153 -> 282 -> 282 -> 282 -> 283 -> 282 -> 282 -> 283 -> 284 -> 284 -> 285 -> 286*
```

## 9. The CLI: `main.py`

* `python main.py file.pths` prints the token table (`Line | Col | Lexeme | Token`), then
  the errors.
* `--no-comments` hides comment tokens. `--trace` adds each token's state path.
* No file opens an interactive prompt: an empty line lexes the buffer, `:quit` exits.
* Exit code 0 = clean, 1 = lexical errors, 2 = the file cannot be read.

### Using `--trace` to check a TD by hand

```
python main.py --trace samples/sample.pths
```

Every token gets a line like `[1:5] 'ant': 0 -> 1 -> 2 -> A1->196 -> 198 -> 200 -> 201*`:

* `[1:5]`: line 1, column 5.
* The numbers are TD states, in order. Follow them on the diagram.
* `*` / `**` on the last state = retract 1 / 2.
* `A1->196` = the word left TD1 and restarted as an identifier.

## 10. Tests: `tests/`

Run `python -m unittest` from `pothos/` (108 tests). There is one file per TD, plus:

* `test_pdf_examples.py`: 145 examples from the PDF. Each is labelled **OK** (valid),
  **LATER** (lexes cleanly; the parser rejects it), or **LEX** (lexical error).
* `test_recovery_and_positions.py`: line/column numbers, and several errors in one run.
* `test_cli.py`: the CLI output, flags and exit codes.
