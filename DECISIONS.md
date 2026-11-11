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
- **Selected decision:** Per the student's explicit instruction, emit every currently recognized source whitespace character (space, tab, newline) as a lexer token and show a literal space as `␠` in the frontend. Preserve the actual whitespace character as the token lexeme.
- **Reasoning:** The student wants to see that spaces are tokenized in the lexer output. Retaining the actual lexeme keeps source positions and token data accurate; the UI marker makes the space visible.
- **Affected components or files:** `backend/pothos/lexer/lexer.py`, `backend/pothos/lexer/tokens.py`, `frontend/script.js`, lexer tests, lexer documentation, and the future parser's input contract.
- **Specification references:** Student-approved output requirement. The scanned Pothos paper's exact whitespace treatment has not been visually verified; this decision does not claim the paper defines a whitespace token class.
- **Status:** Approved (student instruction); paper conformance and future parser handling remain to be verified.

## Awaiting decisions

- Parser strategy and whether FIRST, FOLLOW, PREDICT, or parsing tables are required: see P-08.
- Semantic checks, symbol table/scope rules and any IR/code generation: see P-10.
- All unresolved lexer discrepancies beyond the examples in D-003: audit P-03 and existing `backend/pothos/DECISIONS.md`.

