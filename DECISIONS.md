# Pothos decision log

This log records decisions evidenced by approved sources or explicitly approved by the student. Existing implementation choices are not automatically approved. Do not backdate undocumented choices. Dates below indicate when this inventory was made, not when an earlier choice was made.

## D-001 — Pothos paper is the language authority

- **Date:** 2026-11-11 (documentation record)
- **Topic:** Source hierarchy
- **Context:** Repository notes and implementation may differ from the language paper.
- **Options considered:** Treat implementation as definitive; treat paper as primary and code as implementation evidence.
- **Selected decision:** The current approved Pothos paper is the documented baseline for intended language behavior; verified compiler behavior is essential evidence when deciding whether the compiler should change or the paper should be revised. Neither side of a conflict is changed without the student's explicit choice.
- **Reasoning:** This preserves the paper as the current language reference while honoring the student's instruction that a correct existing implementation may justify a paper revision to reduce unnecessary compiler work.
- **Affected components/files:** All language rules, `AGENTS.md`, `DEVELOPMENT.md`, future lexer/parser/semantic work.
- **Specification references:** Project task and current paper; see SPECIFICATION_INDEX.md for its revision snapshot.
- **Status:** Approved (project instruction).

## D-002 — No unsupported compiler stages or language rules

- **Date:** 2026-11-11 (documentation record)
- **Topic:** Project scope
- **Context:** Conventional compiler designs include optional techniques and stages not necessarily required here.
- **Options considered:** Implement traditional features by default; implement only paper/course-approved requirements.
- **Selected decision:** Include only requirements supported by the Pothos paper, course/project requirements, or later approved decision.
- **Reasoning:** Project instructions explicitly prohibit scope expansion based only on convention.
- **Affected components/files:** Roadmap, pipeline, parser, semantic analysis, IR/code generation.
- **Specification references:** Project task; course rubric not present in repository.
- **Status:** Approved (project instruction).

## D-003 — Lexical discrepancies require review before behavior changes

- **Date:** 2026-11-11 (issue record)
- **Topic:** Lexer delimiter and error behavior
- **Context:** `backend/pothos/DECISIONS.md` records 34 current code/document differences. Initial tests fail on closing-delimiter EOF and disagree with the notes for `+25`.
- **Options considered:** Accept current implementation; make tests pass; resolve each case against paper and student intent.
- **Selected decision:** No behavior choice is made here. Treat cases as unresolved and defer implementation changes pending paper review and student approval.
- **Reasoning:** Neither source presence nor a test expectation alone establishes intended language behavior.
- **Affected components/files:** `backend/pothos/lexer/charsets.py`, `lexer.py`, `tests/test_lexer.py`, existing `backend/pothos/DECISIONS.md`.
- **Specification references:** Lexical delimiter tables and TDs, current paper pp. 74–84; compare exact page images. Prior index used pp. 73–83 before the current PDF fingerprint was checked.
- **Status:** Awaiting Approval.

## D-004 — Reusable compiler methodology is separate from Pothos rules

- **Date:** 2026-11-11 (documentation record)
- **Topic:** Documentation boundaries
- **Context:** Agents need reusable compiler guidance without duplicating the Pothos specification.
- **Options considered:** Put project roadmap and language rules into the skill; keep project instructions and generic methodology separate.
- **Selected decision:** `AGENTS.md` and `DEVELOPMENT.md` carry project workflow/roadmap; the skill carries reusable compiler methods. Paper remains authoritative for Pothos rules.
- **Reasoning:** Separation keeps project behavior traceable and methodology reusable.
- **Affected components/files:** `AGENTS.md`, `DEVELOPMENT.md`, `.agents/skills/compiler-design-methodology/SKILL.md`.
- **Specification references:** Project task sections 5–8.
- **Status:** Approved (project instruction).

## D-005 — Resolve paper/compiler behavior conflicts with the student

- **Date:** 2026-11-11 (conflict recorded; no resolution selected)
- **Topic:** Language behavior and authority when the specification conflicts with the running compiler
- **Context:** The current paper (`Latest_Pothos_ProgrammingLanguage.pdf`) gives behavior that differs from the lexer and at least one lexer test. The student clarified that either the compiler may need a change or the paper may be adjusted to match a correct, simpler existing implementation.
- **Options considered:** Change compiler behavior to match the paper; revise the paper after verifying existing compiler behavior is correct and preferable; retain current behavior pending more evidence; choose another interpretation based on project requirements.
- **Selected decision:** None yet. First verify the relevant paper text visually and inspect/execute the affected compiler path. Then present the evidence, cost and behavior consequences of each viable option and obtain explicit student confirmation before changing compiler logic or paper rules.
- **Reasoning:** Neither the paper nor current code should be changed reflexively; the intended language and appropriate implementation need to be agreed from evidence.
- **Affected components or files:** `backend/pothos/lexer/lexer.py`, `charsets.py`, `tests/test_lexer.py`, future parser/semantic phases, the current paper, `SPECIFICATION_INDEX.md`.
- **Specification references:** Paper pp. 6, 17, 19–20, 42–43, 67–84; OCR navigation in SPECIFICATION_INDEX.md. Inspect the PDF page image before relying on ambiguous glyphs.
- **Status:** Awaiting Approval.

## D-006 — Emit whitespace as visible lexer tokens

- **Date:** 2026-11-12
- **Topic:** Lexer output and student-facing token display
- **Context:** Ordinary spaces were skipped by `Lexer.run`; tabs and newlines already appeared as tokens. A literal space would also be visually blank in the frontend token table.
- **Options considered:** Keep spaces as ignored separators; show whitespace only as a frontend overlay; emit whitespace tokens and render spaces with a visible marker.
- **Selected decision:** Per the student's explicit instruction, emit every currently recognized source whitespace character (space, tab, newline) as a lexer token. Preserve the actual whitespace character as the token lexeme and render the space lexeme as a literal blank in the frontend table.
- **Reasoning:** The student wants to see that spaces are tokenized in the lexer output. Retaining the actual lexeme keeps source positions and token data accurate; the UI marker makes the space visible.
- **Affected components or files:** `backend/pothos/lexer/lexer.py`, `backend/pothos/lexer/tokens.py`, `frontend/script.js`, lexer tests, lexer documentation, and the future parser's input contract.
- **Specification references:** Student-approved output requirement. The scanned Pothos paper's exact whitespace treatment has not been visually verified; this decision does not claim the paper defines a whitespace token class.
- **Status:** Approved (student instruction); paper conformance and future parser handling remain to be verified.

## D-007 — Resolve zero-leading fractional digits and fractional truncation

- **Date:** 2026-11-12
- **Topic:** Flo literal lexical rules
- **Context:** Current `digit` is `1`–`9`, which correctly counts significant integer digits, but state 254 also uses it for the first fractional digit. Therefore `1.00001` and `0.00000` currently report “needs a digit after '.'”. The current four-fraction-digit state also accepts a fifth digit by retracting it, so `1.23456` becomes `flo_lit("1.2345")` followed by `wharfa_lit("6")`.
- **Paper evidence:** Current fingerprinted paper pp. 20–21 says a flo literal requires a digit on both sides of the decimal point; the fractional part is capped at four digits; trailing fractional zeros count toward that cap and are only trimmed when printed/formatted; and fifth-and-later fractional digits are discarded by truncation, without rounding or a lexer error. Page 22 lists `1.23456` as an invalid example (“fractional cap exceeded”), conflicting with p. 21.
- **Options considered:** (1) Fix the clear zero-digit defect, then follow p. 21 by accepting/truncating excess fraction digits without rounding and revise p. 22's contrary example/test after confirming the scan. (2) Fix the clear zero-digit defect, but follow p. 22 by rejecting a literal with more than four fractional digits, updating p. 21/test to match. (3) Adopt the student's suggested trailing-zero/rounding interpretation and revise the paper only after specifying exactly which zeros count and whether literals truncate or round. (4) Keep current behavior pending a different interpretation.
- **Selected decision:** **Approved — option 1 (2026-11-12).** Follow p. 21: require at least one digit on both sides of `.`, count all fractional digits including zeroes, retain at most the first four fractional digits in the numeric value, and silently truncate later digits without rounding. The lexer keeps the complete source lexeme for display and separately supplies the truncated numeric value. This approval resolves implementation direction while retaining the p. 22 inconsistency as a paper issue to review in a future revision.
- **Affected components or files:** `backend/pothos/lexer/lexer.py`, `backend/pothos/lexer/tokens.py`, `backend/pothos/compiler/serialize.py`, `tests/test_lexer.py`, `LEXER_AUDIT.md`, `PROGRESS.md`, `DEVELOPMENT.md`.
- **Specification references:** Current paper pp. 19–22; OCR-derived rule map in SPECIFICATION_INDEX.md. Current PDF SHA-256: `6439B2D9A778B226A7AA80FFCE6699B3DE9B5545B3D7D7E7930298E7D3D40F2F`.
- **Status:** Approved; implementation complete, regression suite has known unrelated failures.

## D-008 — Withhold an unterminated final token in auto-run preview

- **Date:** 2026-11-12
- **Topic:** Live lexer table and delimiter lookahead
- **Context:** Auto-run submits the editor snapshot to the normal lexer. The lexer treats EOF as a delimiter for identifiers (`ID_DELIMITER = delim_id | {EOF}`), so typing `M` immediately displays an `id` token even though no source delimiter has been entered. The Pothos paper's category-specific delimiter tables are the authority for typed delimiters; manual whole-file lexing still needs its existing EOF behavior.
- **Options considered:** (1) In auto-run presentation only, withhold a final identifier, reserved word, boolean, numeric literal, or string literal ending exactly at the current editor boundary; keep compiler/CLI/manual Run EOF semantics. (2) Remove EOF acceptance from compiler rules, changing complete-file behavior and requiring a separate language decision.
- **Selected decision:** **Approved — option 1 (2026-11-12).** Auto-run hides a final token from those delimited token categories while it ends exactly at the editor boundary. Typing a valid following delimiter moves it out of the pending position and makes it visible. Whitespace and comment tokens remain visible. Manual Run and compiler behavior continue to treat EOF as before.
- **Reasoning:** This provides the requested delimiter-aware live table without changing Pothos source acceptance or the compiler's whole-file contract.
- **Affected components or files:** `frontend/script.js`, `PROGRESS.md`, `DEVELOPMENT.md`.
- **Specification references:** Paper delimiter tables pp. 74–77; scanner's EOF handling in `backend/pothos/lexer/lexer.py` and `backend/pothos/lexer/charsets.py`.
- **Status:** Approved; implementation recorded, browser behavior not yet manually verified.

## Awaiting decisions

- Parser strategy and whether FIRST, FOLLOW, PREDICT, or parsing tables are required: see P-08.
- Semantic checks, symbol table/scope rules and any IR/code generation: see P-10.
- All unresolved lexer discrepancies beyond the examples in D-003: audit P-03 and existing `backend/pothos/DECISIONS.md`.



## D-009 ? Follow the user-approved lexer diagrams and delimiter QA CSV

- **Date:** 2026-11-13
- **Topic:** Lexer transitions, delimiter sets, numeric normalization, and overflow
- **Context:** The user added transition-diagram images and a delimiter QA CSV in `Documentation/`, clarified that ?characters? means identifiers, and explicitly chose to follow the CSV where it conflicts with prior code/diagram behavior.
- **Approved behavior:** Use diagram state IDs in lexer traces. Identifiers remain limited to 20 characters; an identifier ending at EOF is an error because EOF is absent from the approved `delim_id`. Accept raw newlines inside quoted strings. Normalize integer lexemes by removing leading zeroes (`00012` ? `12`, all zeroes ? `0`). Normalize float lexemes by trimming fractional trailing zeroes but retaining at least one fractional digit (`0.0000` ? `0.0`); accept the diagram?s `5.` path as `5.0`. Consume fractional precision beyond four places and round half up to four digits. When a ninth significant digit arrives, report the first eight digits as the overflow error text, then the outer run loop continues by invoking the normal scanner at state 0 on the ninth digit; that suffix may become a token (for example, `123456789;` errors on `12345678` and emits `9`, `;`). Apply the same recovery at identifier length 20: error on the first 20 characters, then the outer run loop invokes the normal scanner at state 0 on character 21. Permit adjacency for `+-`, `*-`, `/-`, and `%-` where the operator delimiter rules allow it; `--` remains a line-comment opener, so subtraction followed by unary minus needs a separating space.
- **Delimiter inputs:** Apply the current CSV ?Lexer? entries to `charsets.py`; its ?Paper? column is not a paper revision decision. The submitted PDF has a different fingerprint from the previously indexed snapshot, so paper reconciliation remains separate and this task does not edit the paper or `SPECIFICATION_INDEX.md`.
- **Implementation note:** Diagram state IDs are retained; supplemental states 300 (fraction rounding) and 301?302 (escape handling) cover implementation paths not shown as named diagram states.
- **Affected files:** `backend/pothos/lexer/lexer.py`, `backend/pothos/lexer/charsets.py`, `backend/pothos/main.py`, `tests/test_lexer.py`, lexer references, `DEVELOPMENT.md`, `PROGRESS.md`, and `LEXER_AUDIT.md`.
- **Verification:** `.venv/Scripts/python.exe -m pytest tests/test_lexer.py -q --tb=no` ? 79 passed, 7 failed. Remaining failures are six pre-existing EOF expectations after `]`/`)` and the pre-existing `+25` lexical-error expectation. Focused smoke checks covered normalized numbers, overflow, operator combinations, identifier EOF, raw newlines, reserved-word/symbol inventory, and trace IDs.
- **Status:** Approved and implemented for this scoped task; unrelated paper and lexer discrepancies remain open.


## D-010 ? Apply the student?s explicit delimiter additions and removals

- **Date:** 2026-11-13
- **Topic:** QA delimiter corrections
- **Context:** The student supplied an explicit add/remove list from the delimiter QA sheet and authorized updating `charsets.py`.
- **Approved changes:** Add `(` after datatype words (`strina`, `wharfa`, `flo`, `trua`, `lis`, `glossare`); add newline to the named I/O, logic, statement, `deleo`, `const`, arithmetic/relational/assignment, open grouping, comma, and opening-quote delimiter sets; add `-` after `+`, `*`, `/`, `%` where listed. Remove the listed colon/mathop/`<`/`>`/EOF entries from boolean delimiters; remove `(` and `-` from `delim_insid`; remove `]` from `delim_closeparen`; remove `(` from `delim_openbracket`; remove `;` from `delim_closecurly`; remove `>`, `<`, `-`, `*`, `/` from closing quote sets; remove `-` from semicolon delimiters. Add assignment operators to `delim_id` and EOF to `delim_num`.
- **Keyword wiring:** `belsa` and `neve` use the newline-enabled logic delimiter set; datatype keywords use the datatype set. Numeric accepting transitions use `delim_num`, including its EOF member.
- **Affected files:** `backend/pothos/lexer/charsets.py`, `backend/pothos/lexer/lexer.py`, `tests/test_lexer.py`, `LEXER_AUDIT.md`, `PROGRESS.md`, and lexer walkthrough/reference notes.
- **Verification:** `.venv/Scripts/python.exe -m pytest tests/test_lexer.py -q --tb=no` ? 86 passed, 7 failed after the datatype accepting-state fix. Failures remain the six existing EOF-after-`)`/`]` cases and `+25` lexical-error expectation. `git diff --check` and Python compilation passed.
- **Status:** Approved and implemented.
