# Pothos project progress

**As of:** 2026-11-20
**Overall status:** P-01's paper snapshot/index and P-02 are complete. Lexer work remains active. P-03's audit is being refreshed against the new Documentation materials, with the reserved-word image treated as the primary transition reference. P-05 remains in progress for approved lexer behavior. The indexed paper is absent from the worktree; a different paper copy is present under Documentation and is not treated as an approved specification revision. Syntax implementation remains deferred.

## Completed

- P-01 — Identified current paper as `Latest_Pothos_ProgrammingLanguage.pdf`, 118 pages, academic year 2026–2027; verified SHA-256 `6439B2D9A778B226A7AA80FFCE6699B3DE9B5545B3D7D7E7930298E7D3D40F2F` and updated SPECIFICATION_INDEX.md. This differs from the previous 117-page snapshot; lexical page references shifted by one according to OCR/navigation, with visual rule comparison still pending.
- Inspected OCR text for language rules, regular definitions, token rules, delimiter tables, transition diagrams, grammar, and FIRST/FOLLOW material. OCR limitations and visual verification needs are recorded.
- P-02 — Confirmed current structure, samples, CLI invocation, and Flask test-client GET/POST API invocation. Full evidence and limitations are in DEVELOPMENT.md.
- 2026-11-20 lexical revision: added the five reserved words shown in the updated reserved-word image (`swil`, `cas`, `defal`, `repec`, `voia`) to the lexer reference list and TD1 handling. Applied the revised delimiter sheet to the corresponding character sets and accepting transitions; see D-011 and LEXER_AUDIT.md for details. The image uses `trua`; the reserved-word list, regular-expression list, delimiter sheet, and CFG use `truta`. The image is treated as primary for the lexical token spelling, so `truta` is recorded as an unresolved document inconsistency, not added as a second token. The symbol list has no clear new token; its `+=` token-label typo was not adopted because the image shows the augmented operator.
- Read the new `Documentation/Transition Diagram in text.txt` as a search aid and checked it against the images. Its transcription contains apparent inconsistencies (`beliasa`/`belsa`, `insub`/`innum`, `trula`/`trua`, `void`/`voia`); the images remain the lexical reference as requested. Added the `\\{` and `\\}` string escapes shown in the updated strings image. Updated comments to use the image's tilde opener/closer, including its EOF edge. The CFG was inspected for context only; no parser or syntax code was changed.
- Updated the original `backend/pothos/samples/` examples and added five focused `.pths` lexer examples covering revised reserved words, operators and delimiters, literals and escapes, comments and whitespace, and lexical errors. `samples/README.md` describes the coverage; these are lexer examples rather than syntax acceptance tests.
- Frontend editor highlighting now takes its reserved-word, literal, symbol, delimiter, and valid-escape tables from the revised `frontend/language.json`; the five added words and `flo`/`inflo` are included, and obsolete `&&`, `||`, standalone `!`, dot, `true`/`false`, and null literal entries were removed. String escapes have a separate color; raw `{...}` placeholders are separately colored only inside a direct string argument to `formo(...)`. The escape spellings `\\{` and `\\}` remain escape-colored rather than placeholder-colored. This is editor presentation only; no lexer/parser behavior changed.
- The deployed frontend is built into `dist/`, which is the directory served by Flask. The current build includes the revised highlighting bundle and favicon; an earlier isolated build did not update the page the application serves.
- Follow-up configuration audit corrected stale comment metadata from `--` and `/--…--/` to the backend's paired `~…~` marker, changed the integer limit label to `maxSignificantDigits`, retained the documented function-name minimum, and updated the editor comment tokenizer to follow the configured tilde marker. The isolated frontend build succeeded again after this correction.
- Added `logo_light.png` as the browser tab favicon in `frontend/index.html` and wired the served `dist/index.html` to the existing emitted asset with a cache-busting query; Flask serves `dist/` directly.
- Fixed the custom escape and `formo` placeholder styles: CodeMirror now maps named stream tokens through its token table to the dedicated highlight tags. The prior code returned tag objects from the stream tokenizer, so those two colors could not be applied. `npm run build` completed successfully after the fix; Flask test-client checks confirmed the served page references the new bundle and returns that bundle and the favicon with HTTP 200.

## Current task

- **P-05 — Lexer/editor usability refinements:** D-006 covers whitespace tokens and editor display. Current fixes make the space lexeme literally blank, avoid stale notices during auto-run, set Enter to column 1, and increase the API input-size limit. D-009 diagram/CSV lexer behavior is implemented per student approval: normalized numbers, half-up float rounding to four places, and the requested identifier/operator/string/delimiter transitions. D-008 remains the frontend preview rule; D-009 changes backend identifier EOF behavior to match the QA CSV. D-011 applies the 2026-11-20 reserved-word and delimiter revision; its revised regression suite passes.
- **P-03 — Audit lexer state transitions and token recognition:** current implementation map, rule-to-code-to-test matrix, conflicts and remaining checks are in LEXER_AUDIT.md. New reserved words, revised delimiter sets, brace escapes, tilde comments, and sample updates are implemented and covered by focused tests. Trace output maps revised TD2–TD5 IDs and the new TD1 paths; legacy TD1 path-number reconciliation remains open.

## Pending

- Remaining P-05 lexer audit/regression tasks; D-006 and D-009 approved changes are implemented. The 2026-11-20 reserved-word and delimiter changes passed the updated lexer suite.
- P-06 API/pipeline/frontend consistency audit; the editor highlight tables are aligned, while API/pipeline contract checks remain.
- P-09 syntax phase implementation.
- P-11 semantic phase implementation.
- P-12 integration and deliverable validation, including the paper's statement that the compiler produces an executable.
- P-13 final documentation and demonstration.

## Blocked

- **P-04** remains open for unrelated lexer discrepancies. D-009 is approved for the scoped diagram and CSV behavior; other paper/compiler discrepancies still need separate decisions.
- P-07, P-08, and P-10 remain **Needs Verification**: the paper contains a grammar (pp. 85–97), FIRST-set material (pp. 98–108), FOLLOW-related material (pp. 108–118), and extensive semantic rules (pp. 17–65), but these have not yet been validated against one another and the current code.
- Textbook-based technical references await access to the two course textbooks. No textbook files were found in the repository.

## Known issues and evidence

- `.venv/Scripts/python.exe -m pytest tests/test_lexer.py -q -k 'float_fraction or valid_lexemes and 12345'` on 2026-11-12: **9 passed, 59 deselected**.
- `.venv/Scripts/python.exe -m pytest tests/test_lexer.py -q --tb=no` on 2026-11-13: **7 failed, 86 passed**. The remaining failures are six existing valid-example expectations at EOF after `]`/`)` and the existing `+25` lexical-error expectation; baseline was 8 failed, 54 passed. New approved behavior cases pass.
- Flask test-client POST `/api.json` with `{"code":"a b"}` returned 200 and serialized `id("a")`, `space(" ")`, `id("b")` at columns 1, 2, and 3.
- Normal float inputs `0.5`, `1.2`, `12.5`, and `flo amount = 12.5;` returned no lexical errors through Flask. A dot without a following digit still correctly errors. Frontend now ignores late responses for old source and marks prior results stale when the editor changes, avoiding confusion between an intermediate `1.` error and the current complete literal.
- D-009 implementation: integers normalize leading zeroes (`00012` ? `12`, all zeroes ? `0`); floats normalize trailing fractional zeroes and round half up to four places (`1.23456` ? `1.2346`, `1.99999` ? `2.0`, `0.00000` ? `0.0`). Eight significant integer digits are accepted; overflow reports the maximum-length prefix; the outer run loop then scans the first excess character normally from state 0 (e.g. `12345678` error then `9` token). Identifier overflow works the same way at 20 characters. Diagram state IDs are used in traces, with supplemental states 300?302 documented in code.
- D-008 frontend preview behavior remains; D-009 now makes a final identifier at EOF a lexical error per the approved QA CSV. Reserved words, numeric literals and strings retain their category-specific EOF handling.
- Newline plus indentation smoke input returned line 2 space tokens beginning at column 1; editor Enter now inserts a plain newline without copying prior indentation.
- API source limit increased from 200 KB to 1 MB. Frontend token-table performance with very large, whitespace-heavy inputs remains unmeasured.
- API boundary smoke check: a 250,000-byte source reached lexical analysis (HTTP 200); a source of 1 MB + 1 byte was rejected with HTTP 413.
- Flask GET `/` returned the latest asset references, and GET `/assets/index-1ykS6miC.js` and `/assets/index-HX2pbawO.css` returned HTTP 200.
- The globally resolved `python` is `C:\Python314\python.exe` and has no pytest; use the project interpreter at `.venv/Scripts/python.exe` for repeatable test runs.
- CLI baseline: current `sample.pths` runs without lexical errors. The `errors.pths` sample exits 1 and reports 9 lexical errors, while root README describes an 11-error sample/test collection.
- Flask test-client smoke check: GET and POST `/api.json` both returned 200; POST `x = 1;` serialized the expected tokens. No HTTP server was started.
- Vite production build succeeded to isolated `.preview-dist/`; its new JS/CSS bundles were copied to `dist/`, and `dist/index.html` now references them. Existing generated assets were retained. A normal build still empties `dist/`, so review worktree changes before running one.
- `README.md` describes `back-end/` and test suites/commands that do not match the current `backend/pothos/` and root `tests/test_lexer.py` layout.
- `backend/pothos/compiler/phases.py` contains `SyntaxPhase` and `SemanticPhase` placeholders that raise `NotImplementedError`; `pipeline.py` enables only `LexicalPhase`.
- Paper p. 17 permits non-ASCII content inside strings and comments, while current lexer logic rejects non-ASCII characters in both; see D-005.
- Paper p. 19 says unary plus is unsupported and produces a syntax error. Current lexer emits `+` and a number; one current lexer test expects a lexical error. The phase/error-level expectation needs a student choice and parser context; see D-005.
- A read-only catalog check recognized all 54 entries in `RESERVED_WORDS` and `RESERVED_SYMBOLS` as isolated tokens with a following space. This does not verify all transition or delimiter behavior.
- LEXER_AUDIT.md maps character classes, keyword/symbol tokens, identifiers, numbers, strings/comments, delimiters/EOF, whitespace, positions and recovery to code and current tests. D-006 makes each recognized space, tab, and newline an output token; future parser work must explicitly handle or discard these trivia tokens. Scanned transition diagrams and exact delimiter-table entries still need visual comparison; OCR is not sufficient for arrow/symbol details.
- The user-added Documentation PDF differs from the previously indexed fingerprint (`0bc754653b00d82f68aae4ed9edd4499067f3f6a7ebe9680a1cd4dce553646dc` vs. `6439B2D9A778B226A7AA80FFCE6699B3DE9B5545B3D7D7E7930298E7D3D40F2F`). Paper reconciliation remains separate; SPECIFICATION_INDEX.md was not changed. New lexical text files and images are working revision inputs, not a replacement for the paper.
- Paper pp. 19–20 say excess integer digits are separately tokenized and syntax analysis rejects consecutive numeric tokens; current lexer behavior appears consistent with this division of responsibility.
- Paper p. 6 describes compiling a `.pths` file to an executable, while the current repository implements a lexer API/pipeline only. Confirm the course deliverable/toolchain before deciding whether code generation is required.
- The paper is image-scanned; its OCR-derived index can misread symbols. Inspect original page images for ambiguous delimiter sets, grammar productions, and calculated sets before implementation.
- The earlier PDF `midterm documentation/Final_Midterm_Pothos_ProgrammingLanguage.pdf` remains deleted. Minima and the two textbooks were absent from inventoried repository files.
- At inspection, user modifications existed in `app.py`, lexer files, frontend assets/script, tests, and generated `dist/` files. They were preserved; re-check `git status` before any future work.

## Decisions awaiting approval

- P-04: for each confirmed conflict, should the compiler be changed to match the paper, should the paper be revised to reflect verified compiler behavior, or should a third interpretation be adopted?
- P-08: verify whether the paper includes PREDICT sets and/or a predictive parsing table, then check calculations against the grammar.
- P-12: confirm how the paper's executable-output requirement maps to the current academic project deliverable and implementation scope.

## Next task

Continue P-03 by visually comparing current paper pp. 67–84 against LEXER_AUDIT.md; then complete exact test traceability and reconcile the 34 entries in `backend/pothos/DECISIONS.md`. Present other behavior discrepancies as choices for the student. Do not change compiler logic or paper rules before explicit confirmation.

- D-009 applies the approved Documentation transition diagrams and QA delimiter CSV, including raw newlines in quoted strings, final-identifier EOF errors, arithmetic operator combinations such as `1+-2`, and CSV delimiter changes. Exact choices and scope are recorded in DECISIONS.md.
- The added keyword paths use supplemental states 310-332 to preserve existing TD state numbering in the hand-written lexer. This preserves current trace paths but does not yet make all lexer state numbers match the newly supplied composite text transcription; compare and reconcile state IDs in the continuing P-03 audit.
- Follow-up overflow correction: `123456789;` now reports `12345678` as the lexical error text and emits `9` and `;`; an overlength identifier similarly reports its first 20 characters, then the normal state 0 scan processes character 21. D-010 applies the student?s explicit delimiter additions and removals in `charsets.py`; numeric transitions now use the EOF member of `delim_num`.
- Datatype delimiter follow-up: `strina`, `wharfa`, lowercase `trua`, and `lis` accepting transitions were still checking `delim_space` directly, despite `(` being present in `delim_datatype`. They now use that shared set, matching `flo` and `glossare`; parameterized tests cover all six datatype keywords followed by `(`.
- The preceding datatype follow-up records the 2026-11-13 behavior. D-011 supersedes it: the 2026-11-20 delimiter sheet defines `delim_datatype` as space/tab plus newline, so `(` is no longer accepted directly after a datatype word. The 2026-11-13 test result remains historical and does not verify the new rule.
- Verification after the D-011 test refresh: `.venv/Scripts/python.exe -m py_compile backend/pothos/lexer/lexer.py backend/pothos/lexer/charsets.py backend/pothos/lexer/tokens.py` completed successfully; `.venv/Scripts/python.exe -m pytest tests/test_lexer.py -q --tb=short` completed with **101 passed** on 2026-11-20. `git diff --check` also completed without output.
