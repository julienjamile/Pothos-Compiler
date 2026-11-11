# Pothos project progress

**As of:** 2026-11-11  
**Overall status:** P-01's paper snapshot/index and P-02 are complete. The lexer is the active focus: P-03 has a code/test audit record and the regression suite currently has 8 failures. The current 118-page paper is present and fingerprinted; P-03 still needs visual comparison of scanned transition diagrams and delimiter tables. Later syntax and semantic tasks are deferred.

## Completed

- P-01 — Identified current paper as `Latest_Pothos_ProgrammingLanguage.pdf`, 118 pages, academic year 2026–2027; verified SHA-256 `6439B2D9A778B226A7AA80FFCE6699B3DE9B5545B3D7D7E7930298E7D3D40F2F` and updated SPECIFICATION_INDEX.md. This differs from the previous 117-page snapshot; lexical page references shifted by one according to OCR/navigation, with visual rule comparison still pending.
- Inspected OCR text for language rules, regular definitions, token rules, delimiter tables, transition diagrams, grammar, and FIRST/FOLLOW material. OCR limitations and visual verification needs are recorded.
- P-02 — Confirmed current structure, samples, CLI invocation, and Flask test-client GET/POST API invocation. Full evidence and limitations are in DEVELOPMENT.md.

## Current task

- **P-03 — Audit lexer state transitions and token recognition:** current implementation map, rule-to-code-to-test matrix, conflicts and remaining checks are in LEXER_AUDIT.md. Full diagram/table verification remains unfinished.

## Pending

- P-05 lexer corrections after approved P-04 decisions.
- P-06 API/pipeline/frontend consistency audit.
- P-09 syntax phase implementation.
- P-11 semantic phase implementation.
- P-12 integration and deliverable validation, including the paper's statement that the compiler produces an executable.
- P-13 final documentation and demonstration.

## Blocked

- **P-04** awaits student choices on behavior discrepancies after code/paper evidence is reviewed. Do not change compiler logic or the paper until a choice is confirmed.
- P-07, P-08, and P-10 remain **Needs Verification**: the paper contains a grammar (pp. 85–97), FIRST-set material (pp. 98–108), FOLLOW-related material (pp. 108–118), and extensive semantic rules (pp. 17–65), but these have not yet been validated against one another and the current code.
- Textbook-based technical references await access to the two course textbooks. No textbook files were found in the repository.

## Known issues and evidence

- `.venv/Scripts/python.exe -m pytest tests/test_lexer.py -q` on 2026-11-11: **8 failed, 52 passed**. Failures include EOF after `]` and `)`, plus the `+25` expectation; inspect full pytest output and `backend/pothos/DECISIONS.md` before changing behavior.
- The globally resolved `python` is `C:\Python314\python.exe` and has no pytest; use the project interpreter at `.venv/Scripts/python.exe` for repeatable test runs.
- CLI baseline: current `sample.pths` runs without lexical errors. The `errors.pths` sample exits 1 and reports 9 lexical errors, while root README describes an 11-error sample/test collection.
- Flask test-client smoke check: GET and POST `/api.json` both returned 200; POST `x = 1;` serialized the expected tokens. No HTTP server was started.
- Frontend build was not run: `vite.config.mjs` sets `emptyOutDir: true`, and `dist/` already contains user-modified and untracked assets. PowerShell also resolved `npm` to `npm.ps1`, blocked by the local script policy. Preserve `dist/` and resolve invocation safely before a future build check.
- `README.md` describes `back-end/` and test suites/commands that do not match the current `backend/pothos/` and root `tests/test_lexer.py` layout.
- `backend/pothos/compiler/phases.py` contains `SyntaxPhase` and `SemanticPhase` placeholders that raise `NotImplementedError`; `pipeline.py` enables only `LexicalPhase`.
- Paper p. 17 permits non-ASCII content inside strings and comments, while current lexer logic rejects non-ASCII characters in both; see D-005.
- Paper p. 19 says unary plus is unsupported and produces a syntax error. Current lexer emits `+` and a number; one current lexer test expects a lexical error. The phase/error-level expectation needs a student choice and parser context; see D-005.
- A read-only catalog check recognized all 54 entries in `RESERVED_WORDS` and `RESERVED_SYMBOLS` as isolated tokens with a following space. This does not verify all transition or delimiter behavior.
- LEXER_AUDIT.md maps character classes, keyword/symbol tokens, identifiers, numbers, strings/comments, delimiters/EOF, whitespace, positions and recovery to code and current tests. Scanned transition diagrams and exact delimiter-table entries still need visual comparison; OCR is not sufficient for arrow/symbol details.
- The current PDF SHA-256 differs from the previously indexed snapshot. Page counts and navigation have been updated in SPECIFICATION_INDEX.md and roadmap references. OCR suggests a one-page shift in lexical material; exact wording and transition-diagram comparison remain open under P-03.
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

Continue P-03 by visually comparing current paper pp. 67–84 against LEXER_AUDIT.md; then complete exact test traceability and reconcile the 34 entries in `backend/pothos/DECISIONS.md`. Present behavior discrepancies as choices for the student. Do not change compiler logic or paper rules before explicit confirmation.
