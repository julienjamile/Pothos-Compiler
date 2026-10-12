# Decisions: where the PDF conflicts, and what the lexer does

Source of truth: the latest *Pothos Programming Language* PDF (sections and page numbers
below refer to it). The same items are marked in the annotated PDF we handed in.

* **Revisions (A1–A3)** change the TDs. They are applied in the code.
* **Rules (B1–B3)** fill gaps the TDs leave open.
* **Kept decisions (C, E1–E6)** are TD choices that the spec text does not match yet.
  The lexer follows the TD; the spec text should be updated.
* **Open decision (D)** has not been agreed by the group. The default is shown and can be
  switched in one line.
* **X1–X4** are extra issues found while building the lexer.

## Summary

| ID | Issue | Where in the PDF | What the lexer does |
|---|---|---|---|
| A1 | TD1 has no fallback to identifiers | TD1 p40–41; TD3 p43 | no edge in TD1 → restart at state **196** from the first letter |
| A2 | TD5 multi-line comment is ambiguous | TD5 p45 (282–285); IV.D p34 | 282 loops on `ml_char`; 283/284 have back-edges |
| A3 | `delim_escape` is undefined | TD5 p45 (274, 277); IV.E p34–35 | `delim_escape = { " ' \ n t 0 }` |
| B1 | no rule for a missing edge | all TDs | no matching edge = lexical error |
| B2 | state 154 `**` unexplained | TD2 p42 | `**` = retract 2, emit `/` |
| B3 | states 193 / 195 | TD2 p42 | unused; strings use 192 / 194 in TD5 |
| C | TD choices kept | see E1–E5 | negatives via 141; `/` uses `delim_minus`; case variants are `id`; first `--/` closes; IV.E sets win |
| C5 | clean examples listed as errors | p9, p11 | they lex cleanly; the parser rejects them |
| **D** | `belial{` | I.1 p19 | **open**: lexical error by default |
| E1 | negatives: spec text vs TD | II.9.a.i p6; III.C.2 p10; p31–33, p37; TD2 p42; TD4 p44 | `-5` is one `wharfa_lit` |
| E2 | case variants called "errors" | p9, p11, p19–21 | `Belial`, `TRUA`, `Innum` → `id` |
| E3 | Reserved Symbols table ≠ IV.E sets | p37–39 vs p34–35 | IV.E sets are used |
| E4 | `/` delimiter | p37; p34–35; TD2 p42 | `/` ends on `delim_minus` |
| E5 | nested-comment example | III.A p8 | `/-- nested /-- inner --/` is one valid comment |
| E6 | `innum` missing from `delim_flow` list | IV.E p35 | `innum` uses `delim_flow` (TD1 55→56) |
| X1 | regex repeat counts are exact | IV.D p33 | ids are 1–20 chars, integers 1–8 significant digits |
| X2 | `delim_scomment_start` lacks eof | IV.E p35; p39; TD5 | eof is included |
| X3 | curly quotes in IV.C | IV.C p33 | ASCII `"` and `'` only |
| X4 | III.C.2.5.a names the wrong phase | III.C.2.5.a p11 | `1.5`, `1_000`, `1e5` are lexical errors |

---

## A. Revisions applied to the TDs

### A1. TD1 falls back to identifiers (state 196)

*TD1 p40–41; TD3 p43.* A word that leaves a keyword path (`ant`, `stri`), or a whole
keyword followed by a letter, digit or `_` (`belial1`, `pass`), has no edge in TD1. So it
could never become an identifier.

**Lexer:** when a TD1 state has no matching edge, the lexer goes back to the first
letter and restarts at **state 196** (TD3). `ant`, `stri`, `pass`, `belial1` → `id`.
Code: `Lexer._restart_at_196`. With `--trace` it shows as `A1->196`:

```
'ant':     0 -> 1 -> 2 -> A1->196 -> 198 -> 200 -> 201*
'belial1': 0 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> A1->196 -> 198 -> ... -> 209*
```

### A2. TD5 multi-line comment edges

*TD5 p45 (282–285); IV.D regex p34.* The 282 loop said "ascii, newline". That set includes
`-`, so `-` both looped and went to 283. A lone `-` or `--` inside the body also had no
edge back (`/-- a-b --/` died at 283, `/-- x ---/` died at 284).

**Lexer:** 282 loops on `ml_char`; 283 −`ml_char`→ 282; 284 −`-`→ 284;
284 −`ml_char_ns`→ 282. The first `--/` closes the comment (III.A.2.c). This matches the
p34 regex.

```
'/-- a-b ---/': 0 -> 149 -> 153 -> 282 -> 282 -> 282 -> 283 -> 282 -> 282 -> 283 -> 284 -> 284 -> 285 -> 286*
```

### A3. `delim_escape` defined

*TD5 p45 (274→192, 277→194); IV.E p34–35; escape p31.* TD5 uses `delim_escape` after `\`,
but no table defines it. The p31 escape set also says "tab" instead of `\t`.

**Lexer:** `delim_escape = { " ' \ n t 0 }` (from III.C.1.6, p10), in `charsets.py`.
`"Hi\x"` is a lexical error because `x` has no edge from 274.

## B. Rules the TDs leave open

### B1. No matching edge = lexical error

*All TDs.* The diagrams never say what happens when a state has no matching edge.

**Lexer:** a lexical error (besides the A1 fallback in TD1). This also covers a stray
`--/`: state 278 has no `/` edge (III.A.2.b).

### B2. State 154 is `**` (retract 2)

*TD2 p42 (149 → 153 → 154).* `**` is not defined in the PDF.

**Lexer:** `**` = retract 2, emit `/`. After `/` and `-`, a `delim_minus` character
(not `-`) takes 153 → 154. The lexer gives back the `-` and that character, and emits `/`.
So `x/-y` → `x`, `/`, `-`, `y`.

```
'/': 0 -> 149 -> 153 -> 154**
```

### B3. States 193 / 195 are unused

*TD2 p42; Reserved Symbols table p39.* 193 / 195 would end a lone quote as its own
token. TD5 uses 192 / 194 as the inside-of-string states, so no quote token is emitted.

**Lexer:** 193 and 195 do not exist. 192 (`"`) and 194 (`'`) are numbered in TD2 and
their edges come from TD5. They are one state each, with one branch in the code.

## C. TD decisions kept (spec text to be updated)

These were decided for the TDs. The lexer follows them (details in E1–E5):

1. Negatives go through shared **state 141**: `-` followed by a digit is part of `wharfa_lit`.
2. `/` uses **`delim_minus`**, not `delim_mathop`.
3. **Case variants** of reserved words lex as **`id`**.
4. The **first `--/`** closes a multi-line comment (no nesting).
5. When the expanded Reserved Symbols table and the **IV.E sets** disagree, the IV.E sets win.

### C5. Examples that lex cleanly are listed as errors

*p9 `first name`; p11 `y = 1,000;`, `z = +25;`, `active = true;`.*

**Lexer:** none of these is a lexical error. `first name` → `id id`; `1,000` → `1 , 000`;
`+25` → `+ 25`; `true` → `id`. The parser or semantic phase rejects them.
`test_pdf_examples.py` labels them **LATER**.

## D. OPEN DECISION: `belial{`

*I.1 invalid example p19.*

* `prin"Hello"` is a lexical error. `"` is in neither `delim_flow` nor `delim_id`, so TD1
  and TD3 both fail. This matches the spec, and the lexer does it.
* `belial{`: `{` is not in `delim_flow`, but it **is** in `delim_id`. If A1 is applied
  literally, `belial{` lexes as identifier `belial` + `{`. That turns a reserved word into
  an identifier, which III.B.5 forbids.

**Default (current):** a **complete** reserved word followed by a character that is not
in its delimiter set and is not a letter, digit or `_` is a **lexical error**:

```
Lexical Error [line 1, col 1]: '{' cannot follow reserved word 'belial' (not in delim_flow): 'belial'
```

This also applies to `elsa(`, `reor;`, `lis[` and similar cases. A letter, digit or `_`
after the keyword still goes to A1 (`belial1` → `id`).

**To switch:** in `lexer/lexer.py` set

```python
COMPLETE_KEYWORD_FALLS_BACK_TO_ID = True
```

Then `belial{` → `id` `belial`, `{` (A1 applied literally), and the parser must reject it.
Code: `Lexer._keyword_not_delimited`. The tests for D are in `test_td1_reserved_words.py`.

## E. Spec text that disagrees with the TDs

### E1. Negative numbers

*II.9.a.i p6; III.C.2.1–2 p10; IV.C `-` row p31–32; IV.D integer regex p33; `-` row p37;
TD2 p42; TD4 p44.*

The TD puts a `-` followed by a digit inside `wharfa_lit` (shared state 141 → TD4). TD2's
minus exit is `delim_minus − numbers`. Those sections say the lexer never puts `-` inside
`wharfa_lit`, and the p37 `-` row still includes numbers.

**Lexer (follows the TD):**

| Input | Tokens |
|---|---|
| `x=-5` | `x` `=` `-5` |
| `a -5` | `a` `-5` |
| `a - 5` | `a` `-` `5` |
| `3-2` | `3` `-2` (no minus token) |

**Parser consequence:** `3-2` reaches the parser as two literals with no operator. The
parser must handle this, or write `3 - 2`. F.1.2 (p15) and the precedence table (p17)
still apply to `-x` and `-( … )`.

```
'-5': 0 -> 141 -> 256 -> 257*
'-':  0 -> 141 -> 142*
```

### E2. Case variants

*III.B.6.a + `Belial` example p9; III.C.3.2.a p11; I.2.4.a p19 + example p20; I.4.4.a +
example p21.*

**Lexer:** `Belial`, `inaccu`, `true`, `TRUA`, `Inpub`, `Innum` → `id` (TD3 via A1). The
parser or semantic phase rejects them. `Trua` and `Inaccu` (exact case) → `trua_lit`.
Note: `Belial` is not a reserved word, so "reserved word as identifier" is the wrong reason
in the p9 example; the reason is "case variant of a reserved word".

### E3. Reserved Symbols table vs IV.E sets

*pp37–39 vs IV.E pp34–35.* **Lexer:** the named IV.E sets are used, and the expanded column
is ignored.

1. The operator rows (`+ * / %`, relational, assignment) omit `-`. But
   `delim_mathop / relop / assops = delim_operand`, which includes `-`, so `x=-5` is legal.
2. The `;` row differs from `delim_term` = delim_space, letter, `}`, `-`, `/`, eof.
3. The `}` row omits eof, but `delim_rbrace = delim_close, eof`.

### E4. `/` delimiter

*`/` row p37; `delim_mathop` p34; `delim_minus` p35; TD2 p42 (149→150, 153→154).* The tables
list `/` under `delim_mathop`. That set includes `-`, which would clash with 149 −`-`→ 153.

**Lexer:** `/` ends on `delim_minus` (149 → 150).

### E5. Nested-comment example

*III.A invalid examples p8.* `/-- nested /-- inner --/` is listed as invalid, but the
first `--/` closes it, so it is one valid comment. TD5 agrees.

**Lexer:** one `comment_ml`. For a real error, use `/-- a /-- b --/ c --/`. The comment
closes at the first `--/`, `c` is an `id`, and the last `--/` is a stray closer (III.A.2.b).

### E6. `innum` missing from `delim_flow`

*IV.E `delim_flow` p35.* The "Terminates" list omits `innum`, but TD1 (55 → 56) and the
Reserved Words table (p36) use `delim_flow` for it. **Lexer:** `innum` uses `delim_flow`.

## X. Additional issues found while building

### X1. Regex repeat counts are exact

*IV.D p33.* `letter(alphanum|_)^19` means exactly 20 characters, and `(0)*digit(numbers)^7`
means exactly 8 significant digits. TD3 allows 1–20 characters and TD4 allows 1–8 digits.

**Lexer:** follows the TDs: identifiers 1–20 characters; integers 1–8 significant digits
(leading zeros do not count). Suggested regex: `{0,19}` and `{0,7}`.

### X2. `delim_scomment_start` lacks eof

*IV.E p35 vs `--` row p39 and TD5 (278 → 279 on newline, eof).*

**Lexer:** `delim_scomment_start = ascii − {/}, newline, eof`. So a `--` at the very end of
a file is a valid empty comment.

### X3. Curly quotes in IV.C

*IV.C "Others" p33.* The quote rows show typographic quotes (U+201C, U+2018).
**Lexer:** only ASCII `"` and `'` start strings. Curly quotes are invalid characters.

### X4. III.C.2.5.a names the wrong phase

*III.C.2.5.a p11.* It says decimals, commas, underscores, spaces and exponents are
parser errors. Under TD4 and `delim_int`, `.`, `_` and a letter after digits are
**lexical** errors.

**Lexer:** `1.5`, `1_000`, `1e5` → lexical errors. `1,000` and `1 000` lex cleanly (the
parser rejects them).

---

## Implementation notes (not conflicts)

* **Whitespace** (space, tab, newline) is skipped at state 0 between tokens. Inside a
  token it is read as a delimiter, so it ends the token.
* **eof** is a sentinel value (`EOF = "<eof>"` in `charsets.py`). It is part of the sets
  that the PDF says include eof (e.g. `delim_term`, `delim_rbrace`, `delim_id`).
* **Error recovery** (outside literals): record the error, then skip at least one
  character and keep skipping up to the next whitespace or one of
  `( ) { } [ ] ; , :` `"` `'`. Lexing then restarts at state 0.
  `RECOVERY_STOP` in `lexer.py`.
* **Errors inside a string or comment** (bad escape, non-ASCII character): the error is
  recorded, the lexer keeps reading to the end of the literal, and the literal is
  dropped. The rest of the line is not misread as code.
* An unterminated string (raw newline, or eof before the closing quote) and an
  unterminated `/--` comment are each one error.
* **Non-ASCII characters** (e.g. `é`) are invalid everywhere, even inside strings and
  comments, because IV.B defines `ascii` as the printable ASCII characters plus tab.
* **Line endings:** `main.py` reads files in text mode, so Windows `\r\n` becomes `\n`.
  If you call `tokenize()` directly, pass text with `\n` line endings.
* **Columns** are 1-based and count each character once (a tab counts as 1).
* Message text names the section it comes from, e.g. `(III.B.3)`.
* The lexer was checked against an independent simulator built from the TD edge tables:
  0 differences on 60,000 random inputs, and no overlapping edges outside state 0.
