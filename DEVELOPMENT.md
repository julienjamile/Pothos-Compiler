# Pothos development roadmap

This roadmap is based on the repository as inspected on 2026-11-11. It describes auditable work, not authorization to change language behavior. The current paper snapshot, `Latest_Pothos_ProgrammingLanguage.pdf`, is a 118-page scan for academic year 2026–2027; its verified fingerprint and page map are recorded in SPECIFICATION_INDEX.md. Its fingerprint differs from the previously indexed 117-page snapshot. Paper/code conflicts require investigation and explicit student choice before changing either the compiler or paper.

## Workflow for every development task

**Understand → Analyze → Plan → Implement → Explain → Test → Review → Update Documentation**

1. **Understand:** Read the task, progress, decisions, relevant current paper, source, and reusable skill.
2. **Analyze:** Explain the compiler concept; establish current behavior and tests; identify dependencies, ambiguity, discrepancies, and whether behavior changes.
3. **Plan:** Before code changes, state what/why/files/intended design/test plan. For a language or logic conflict, compare the paper with observable compiler behavior, evaluate whether the paper or implementation should change (the paper may be revised to reflect sound existing compiler behavior), present the options, and wait for the student's explicit choice before changing either source.
4. **Implement:** Change only the approved scope; preserve unrelated work; keep rule definitions visible and code teachable.
5. **Explain:** Describe actual functions, data, algorithm, input/output flow, paper relation, and an example.
6. **Test:** Run focused tests and relevant regressions, report exact results; add tests with implementation tasks when needed.
7. **Review:** Check acceptance criteria, specification traceability, user worktree changes, and unintended behavior changes.
8. **Update documentation:** Record status/evidence, decisions and specification references.

## Current implementation map

`backend/pothos/lexer/lexer.py` implements a hand-written state machine with TD-oriented methods for reserved words, symbols, identifiers, numbers, strings and comments. `charsets.py` centralizes character classes and delimiter sets. `tokens.py` and `errors.py` hold records. The compiler pipeline invokes `LexicalPhase`; `SyntaxPhase` and `SemanticPhase` raise `NotImplementedError` and are not enabled. `app.py` serves the API; `frontend/` contains the Vite client. Current tests are in root `tests/test_lexer.py`.

The lexer source exists and has broad coverage; it is not considered verified complete. Existing `backend/pothos/DECISIONS.md` lists 34 behavior choices/discrepancies without approval metadata. Treat them as current notes needing comparison with the authoritative paper, not approved historical decisions.

## Task cards

The following fields apply to every card: status, objective, technical background, specification references, dependencies, scope/files, tests, acceptance, learning objective, and approval requirement. References below use paper topics only; exact sections/pages must be added after the paper is accessible. “None verified” means no grammar, parsing-table requirement, or rule has yet been established from the paper.

### P-01 — Verify project references and paper revision

- **Status:** Completed for identified snapshot (paper currently absent; obtain it again for visual verification)
- **Objective:** Establish a traceable, current source of Pothos language requirements.
- **Technical background:** Compiler behavior must be derived from a fixed language definition; revision identity prevents rules from being mixed across drafts.
- **Specification references:** `Latest_Pothos_ProgrammingLanguage.pdf`, 118 pages, title metadata “Latest_Pothos_ProgrammingLanguage”, academic year 2026–2027; page map in SPECIFICATION_INDEX.md.
- **Dependencies:** None.
- **Scope/files:** Identify the current PDF revision, map its sections, and record compiler-relevant topics without duplicating the specification. Recheck its fingerprint when it changes. Locate Minima and both textbooks if supplied.
- **Tests:** N/A; verify page references against the PDF and ensure each quoted/derived rule has a location.
- **Acceptance:** Current paper fingerprint and navigation recorded; relevant page references indexed; missing Minima/textbooks recorded; ambiguous scan text flagged for page-image review.
- **Learning objective:** Distinguish language definition from implementation and technical methods.
- **Approval:** Ask student only for unavailable sources or interpretation choices that block implementation.

### P-02 — Establish implementation and test baseline

- **Status:** Completed (2026-11-11; CLI/API/test baseline verified; frontend build not run because it clears the modified `dist/` directory)
- **Objective:** Reconcile repository documentation with actual files, runnable commands, and behavior.
- **Technical background:** A baseline separates regressions from existing failures and informs dependency planning.
- **Specification references:** Paper-wide audit after P-01; existing lexer notes and samples are secondary evidence.
- **Dependencies:** None; refine after P-01.
- **Scope/files:** Inspect root README, `backend/pothos/`, `tests/test_lexer.py`, API and scripts. Verify CLI/API invocation and inventory samples. Do not change compiler source in this audit.
- **Tests:** `.venv/Scripts/python.exe -m pytest tests/test_lexer.py -q`: **52 passed, 8 failed** (2026-11-11 baseline). `python backend/pothos/main.py backend/pothos/samples/sample.pths` exited 0 with no lexical errors; the `errors.pths` sample exited 1 and reported 9 errors. Flask test client POST and GET `/api.json` both returned 200. A later Vite production build to an isolated `.preview-dist/` directory succeeded; the new JS bundle was added to `dist/` and `dist/index.html` updated to reference it while existing assets were preserved. Normal builds still empty `dist/` per Vite config, so inspect worktree changes before running one.
- **Acceptance:** Architecture, confirmed CLI/API invocations, test inventory, known failures, README mismatches, and build-test limitation are documented with evidence.
- **Learning objective:** Understand how unit tests, API integration, and command-line execution cover different layers.
- **Approval:** Audit required no approval. Any fixes are separate tasks; language or behavior changes require explicit student confirmation under D-005.

### P-03 — Audit lexer state transitions and token recognition

- **Status:** In Progress (current paper restored and fingerprinted; OCR/source audit findings recorded; page-image rule comparison remains)
- **Objective:** Verify every existing lexer transition/token class against paper rules and TD1–TD5.
- **Technical background:** A scanner consumes characters through deterministic states, accepting lexemes at final states and sometimes retracting lookahead.
- **Specification references:** Paper regular definitions pp. 67–69, regular expressions/token table pp. 70–73, delimiter tables pp. 74–77, transition diagrams pp. 78–84; see SPECIFICATION_INDEX.md. This is based on OCR/navigation comparison; diagrams and ambiguous symbols still require page-image verification.
- **Dependencies:** P-01, P-02.
- **Scope/files:** Compare `lexer.py`, `tokens.py`, `charsets.py`, existing tests/samples and notes. Check keyword boundaries, longest/special symbol handling, identifiers, integer/fraction limits, strings/escapes, comments (including Unicode), whitespace, EOF and retract paths. Initial conflicts include Unicode policy inside strings/comments and which phase rejects unary plus. Classify outcomes as verified, unverified, missing, inconsistent, or unclear; do not fix them in the audit. Record findings in `LEXER_AUDIT.md`.
- **Tests:** Maintain a rule-to-case matrix; run lexer regression suite; a read-only catalog check for 54 reserved-word/symbol entries passed, but does not cover transition edges. No implementation or test changes are part of this audit.
- **Acceptance:** Each paper lexical rule maps to code path and current test coverage, with mismatches and unverified scanned-diagram details explicitly recorded. P-03 remains In Progress until current-paper lexical pages 67–84 are visually checked and the 34 existing lexer decision notes are reconciled.
- **Learning objective:** Trace a concrete input character-by-character through transition logic and explain acceptance/retraction.
- **Approval:** Audit independent; behavior fixes need an approved P-04/P-05 scope.

### P-04 — Resolve lexer discrepancies and student-approved rule choices

- **Status:** In Progress (D-009 approved for diagrams/CSV; unrelated discrepancies remain open)
- **Objective:** Decide the intended behavior where paper, lexer, tests, and notes conflict.
- **Technical background:** A discrepancy may be a bug, an obsolete test, a paper change, or a conscious exception; code alone cannot decide intent.
- **Specification references:** Paper pp. 17–20, 42–43, 66–83; specific conflicts summarized in SPECIFICATION_INDEX.md.
- **Dependencies:** P-01, P-03.
- **Scope/files:** Review `backend/pothos/DECISIONS.md`, tests and behavior. Explicit cases include non-ASCII in strings/comments, unary plus, and final `]`/`)` at EOF. D-009 records the student's diagram/CSV choices. Keep the separate paper review open; do not infer that paper approval from this lexer task. For each remaining discrepancy, explain whether correcting the compiler or revising the paper to match verified compiler behavior is preferable, then record the student's choice.
- **Tests:** Define expected cases before code changes; include boundaries and regression expectations.
- **Acceptance:** Each language-affecting discrepancy is marked approved/provisional/awaiting approval with evidence and expected examples.
- **Learning objective:** Separate specification interpretation from implementation defects and test defects.
- **Approval:** Student approval required for any interpretation that changes language behavior.

### P-05 — Complete approved lexer corrections and regression suite

- **Status:** In Progress (whitespace/editor updates and D-009 lexer changes implemented; remaining audit and regression work open)
- **Objective:** Bring lexer behavior into line with approved Pothos rules while preserving verified behavior.
- **Current scoped item:** D-006 emits recognized spaces as `space` tokens and preserves a literal blank in the lexeme cell. Auto-run refreshes without the manual stale notice; manual mode shows the stale notice; Enter starts a new line at column 1; API source limit is 1 MB. D-009 float behavior is approved and implemented: fractional zeroes normalize to at least `.0`, extra precision is consumed and rounded half up to four places, and numeric lexemes are normalized. D-008 withholds a final identifier/keyword/literal in auto-run until a real following delimiter is entered, while preserving normal EOF handling in manual Run. The p. 22 inconsistency, browser verification, and remaining lexer coverage are open.
- **Technical background:** Scanner correctness is validated at character-class boundaries, token boundaries, EOF, errors, and recovery points.
- **Specification references:** Approved lexical rules from P-01/P-04.
- **Dependencies:** P-02, P-03, P-04 for paper/compiler corrections. A separately student-approved output requirement may be implemented as a narrow scoped change while unrelated P-04 discrepancies remain blocked.
- **Scope/files:** Only approved minimal changes in `backend/pothos/lexer/{lexer.py,charsets.py}`, `backend/pothos/main.py`, focused tests, and lexer/project documentation. Keep language rule data findable; avoid refactoring unrelated logic.
- **Tests:** Valid/invalid examples per rule, min/max lengths, each transition/retract, EOF, line/column, multiple errors/recovery, Unicode policy, keyword prefixes, API serialization and full lexer regression. For whitespace-token display, verify each recognized whitespace character, repeated spaces and source positions; ensure the space lexeme remains a literal blank in its table cell and the `space` token name identifies it.
- **Acceptance:** Approved rule matrix passes; no unexplained regression; exact test command/output recorded; student can explain changed transitions.
- **Learning objective:** Relate character sets and accepting states to observable tokens and errors.
- **Approval:** Behavior changes only within P-04-approved decisions or a separately explicit student instruction recorded in `DECISIONS.md`.

### P-06 — Verify lexer API, pipeline, and frontend consistency

- **Status:** Needs Verification
- **Objective:** Ensure token/error results flow consistently through CLI, compiler pipeline, HTTP API and editor highlighting.
- **Technical background:** Integration checks contracts between separately working components, including token names, positions, errors and options.
- **Specification references:** Project interface requirements and lexical token definitions, pending P-01 mapping.
- **Dependencies:** P-02; P-05 for final lexer behavior.
- **Scope/files:** `backend/pothos/compiler/{phases.py,pipeline.py,serialize.py}`, `backend/pothos/main.py`, `app.py`, `frontend/language.json`, frontend API notes/scripts. Reconcile reserved-word/token tables and actual file paths.
- **Tests:** CLI sample/error runs; API request shape, CRLF normalization, invalid requests/size limit, tracing/comment options; frontend highlighting smoke check if practical.
- **Acceptance:** Interfaces agree with lexer outputs; integration tests and commands are documented; no syntax acceptance implied by lex-only endpoint.
- **Learning objective:** Follow source text from UI/CLI to lexer, phase state, serializer, and response.
- **Approval:** Independent for contract-preserving fixes; behavior/interface changes require approval.

### P-07 — Audit and validate the paper grammar

- **Status:** Needs Verification
- **Objective:** Validate and make usable the grammar already present in the paper for parser planning.
- **Technical background:** A context-free grammar describes hierarchical phrase structure; ambiguity and precedence affect parser design.
- **Specification references:** Context-free grammar pp. 85–97; syntax examples pp. 41–65; see SPECIFICATION_INDEX.md.
- **Dependencies:** P-01, P-02; resolve conflicts that affect grammar only after student review.
- **Scope/files:** Compare grammar productions and terminals to the rules/examples in the same paper, lexer token stream, and project code. Identify gaps, ambiguity, precedence/associativity and error expectations. Add a compact versioned grammar reference only if it improves navigation. Do not invent productions.
- **Tests:** Compare every production with paper examples; create positive/negative program corpus after grammar is verified.
- **Acceptance:** Student-reviewed grammar faithfully traces to paper, unresolved points listed, parser input token conventions specified.
- **Learning objective:** Explain terminals, nonterminals, productions, derivations, ambiguity and precedence.
- **Approval:** Student approval for any grammar interpretation or language extension.

### P-08 — Verify parsing strategy and analysis artifacts

- **Status:** Needs Verification
- **Objective:** Verify whether the paper's grammar and set calculations specify a predictive parsing strategy, and what implementation artifacts are expected.
- **Technical background:** Predictive LL parsing may use FIRST/FOLLOW/PREDICT and a table when grammar conditions allow; LR methods use different structures. These are alternatives, not automatic requirements.
- **Specification references:** Paper FIRST set section begins p. 98 and FOLLOW set section begins p. 108; remaining headings and any PREDICT/table material require visual confirmation. Grammar pp. 85–97.
- **Dependencies:** P-01, P-07, access to required textbooks/course instructions.
- **Scope/files:** Inspect the remaining paper pages visually to identify PREDICT sets, parsing tables, grammar conflicts, and required parser method; compare the paper's calculations with the grammar. Determine required AST/parse tree and course expectations. No parser implementation in this task.
- **Tests:** Hand-check set/table calculations for representative productions and input strings, if those artifacts are required.
- **Acceptance:** Method and required artifacts justified by grammar/project requirements; textbooks cited only with verified details.
- **Learning objective:** Explain why the selected method fits grammar properties and how its data structures guide parsing.
- **Approval:** Student/course constraint confirmation required where requirements are unspecified.

### P-09 — Implement syntax analysis and syntax diagnostics

- **Status:** Pending
- **Objective:** Parse lexer tokens according to the approved Pothos grammar and expose a usable syntax result.
- **Technical background:** Parsing checks token sequence structure; the chosen parser builds the representation required by later project stages.
- **Specification references:** Approved P-07 grammar and P-08 parser decision.
- **Dependencies:** P-05, P-06, P-07, P-08.
- **Scope/files:** `backend/pothos/compiler/phases.py`, parser module only if justified, `pipeline.py`, serializers/API and tests. Decide parse tree versus AST from deliverables; implement only the required form. Define error positions/messages and recovery only to required scope.
- **Tests:** Valid programs for each production, invalid/missing/unexpected tokens, precedence/associativity, EOF, recovery if required, pipeline stop/status and API integration.
- **Acceptance:** Syntax phase consumes lexer tokens, produces required structure, reports errors deterministically, is enabled only when complete, and passes grammar-based tests.
- **Learning objective:** Trace tokens through parser state/stack or recursive calls to resulting tree and diagnostic.
- **Approval:** Grammar fixed before implementation; any grammar changes need approval.

### P-10 — Audit semantic requirements and scope rules

- **Status:** Needs Verification
- **Objective:** Validate the detailed semantic rules already described by the paper and identify the checks required by the project.
- **Technical background:** Semantic analysis checks well-formed constructs that grammar alone cannot validate, such as type consistency or declaration/use constraints.
- **Specification references:** Paper specific rules pp. 17–65, especially types/collections pp. 17–31, operators/expressions pp. 32–40, statements and variables pp. 41–46, functions/control flow pp. 47–65.
- **Dependencies:** P-01, P-07, P-09; course deliverables.
- **Scope/files:** Build a rule matrix; validate types, declarations, scope/visibility, symbol table lifetime/deletion, operator type checks, collection restrictions, function rules, and error phase against actual source behavior and tests. Identify which can be implemented within project requirements. No assumed IR/code generation.
- **Tests:** Rule-level valid/invalid examples derived from paper, once approved.
- **Acceptance:** Each proposed check traces to an explicit rule; unknowns are marked awaiting approval; no unsupported checks added.
- **Learning objective:** Distinguish syntax errors from contextual/type errors and explain symbol lookup if required.
- **Approval:** Student approval required for ambiguous or absent semantic policy.

### P-11 — Implement required semantic checks and diagnostics

- **Status:** Pending
- **Objective:** Enforce approved semantic rules on the syntax representation.
- **Technical background:** Symbol tables associate declarations with attributes and scope; type checking validates operations against declared rules.
- **Specification references:** Approved P-10 matrix.
- **Dependencies:** P-09, P-10.
- **Scope/files:** `backend/pothos/compiler/phases.py` and minimal supporting module(s), pipeline, serializers and tests. Add a symbol table/scope stack only if rules require it. Do not add IR unless a deliverable requires it.
- **Tests:** Each semantic rule, nested scope/shadowing only if specified, undeclared/duplicate/type mismatch cases, phase stopping and API error serialization.
- **Acceptance:** Only approved checks run; results identify location and rule; tests cover each rule and learning walkthrough explains lookup/checking.
- **Learning objective:** Explain declarations, scope, symbol attributes and semantic validation for Pothos constructs.
- **Approval:** Approved rule matrix required before behavior-affecting implementation.

### P-12 — Integrate required phases and finalize end-to-end validation

- **Status:** Pending
- **Objective:** Verify the full required pipeline and project demonstration path.
- **Technical background:** Integration validates phase ordering, shared representations, error stopping, and user-facing output.
- **Specification references:** Full approved language requirements and project rubric, pending P-01.
- **Dependencies:** P-05, P-06 and whichever of P-09/P-11 are required.
- **Scope/files:** Pipeline, API/UI, samples, tests, scripts and project docs. Verify the overview's executable-output requirement against the course deliverable before deciding whether code generation is needed. Include only confirmed deliverables; optimization remains out of scope unless explicitly required.
- **Tests:** Valid end-to-end Pothos program, one representative failure per implemented phase, regression suite, setup/build/run smoke checks on documented platforms where available.
- **Acceptance:** Required deliverables run from clean documented setup; phase statuses and diagnostics are consistent; known limitations are explicit.
- **Learning objective:** Explain the complete input-to-result flow and limits of the compiler.
- **Approval:** Confirm the executable target and any code-generation scope with the student/course requirements before implementation planning; other integration work may proceed within already approved features.

### P-13 — Prepare final technical documentation and demonstration

- **Status:** Pending
- **Objective:** Produce accurate student-facing explanation and project demonstration materials required by the course.
- **Technical background:** Technical documentation communicates language rules, architecture, algorithms, validation evidence and limitations.
- **Specification references:** Final approved paper and course rubric, exact references pending.
- **Dependencies:** P-01 and completion of required implementation tasks.
- **Scope/files:** Root README, relevant walkthrough/reference docs and presentation/demo materials actually required. Correct stale commands, architecture descriptions and test counts; include traceable paper references and reproducible examples.
- **Tests:** Follow instructions from a clean environment; verify examples and cited locations against implementation/paper.
- **Acceptance:** A student can set up/run/demo and explain each required phase; claims are evidence-based and limitations recorded.
- **Learning objective:** Present compiler design decisions and demonstrate understanding.
- **Approval:** Student review of final academic claims and submission materials.

## Status meaning

Completed requires evidence; In Progress is actively being inspected or implemented; Pending has clear prerequisites; Blocked awaits a missing source or student decision; Needs Verification means implementation exists but conformance/evidence is incomplete. Do not reorder tasks around a conventional compiler syllabus when paper/course dependencies say otherwise.
