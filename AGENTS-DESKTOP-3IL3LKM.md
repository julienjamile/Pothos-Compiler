# Pothos project instructions

## Project

Pothos is a student programming-language/compiler project. The current repository contains a Python hand-written lexer, a Python/Flask API and a Vite frontend. The compiler pipeline currently enables lexical analysis; syntax and semantic phase classes are placeholders. Source files are intended to use `.pths`.

## Read before work

Before starting any development task, read the matching task in [DEVELOPMENT.md](DEVELOPMENT.md), current state in [PROGRESS.md](PROGRESS.md), relevant entries in [DECISIONS.md](DECISIONS.md), applicable paper material, the affected code, and the reusable guidance in [.agents/skills/compiler-design-methodology/SKILL.md](.agents/skills/compiler-design-methodology/SKILL.md). Follow the Understand → Analyze → Plan → Implement → Explain → Test → Review → Update Documentation workflow in DEVELOPMENT.md.

## Authority and evidence

Use these sources for their proper role:

1. The current Pothos paper and explicit project requirements describe intended behavior, but paper/code disagreement is a question to investigate, not an automatic instruction to change either one.
2. The running implementation and tests establish what the current compiler actually does. Inspect or execute it when this helps determine whether a proposed paper change is warranted.
3. Approved entries in DECISIONS.md record student choices after disagreements are reviewed.
4. Pothos notes and examples are supporting evidence; check them against both the paper and implementation.
5. Minima material is only for document presentation or organization, never for Pothos rules.
6. Compiler textbooks and general compiler practice guide technical methods, never substitute for Pothos requirements.

The current paper is `Latest_Pothos_ProgrammingLanguage.pdf`, a 118-page scanned PDF for academic year 2026–2027. Its SHA-256 and page map are in [SPECIFICATION_INDEX.md](SPECIFICATION_INDEX.md); the fingerprint differs from the previously indexed 117-page snapshot, so review relevant page changes before relying on old citations. OCR can misread notation; inspect cited page images for ambiguous symbols. An earlier PDF at `midterm documentation/Final_Midterm_Pothos_ProgrammingLanguage.pdf` is deleted. No Minima reference or compiler textbook files were found. The two course textbooks have not been consulted. For routine progress refreshes, inspect the existing repository copy and update PROGRESS.md; do not ask the student to upload the same paper again unless it is missing or they indicate a new revision.

## Repository map

- `backend/pothos/lexer/`: token records, character/delimiter sets, lexer state machine and lexical errors.
- `backend/pothos/compiler/`: phase interface, pipeline and JSON serializers.
- `backend/pothos/samples/`: sample inputs.
- `tests/test_lexer.py`: current repository-level lexer tests.
- `app.py`, `frontend/`, `scripts/`: API, browser interface and setup/build/run scripts.
- `Latest_Pothos_ProgrammingLanguage.pdf`: current 118-page paper snapshot at repository root; verify its fingerprint in SPECIFICATION_INDEX.md before relying on page references.
- `SPECIFICATION_INDEX.md`: paper revision fingerprint, page map, and verified rule index (not a replacement specification).
- `LEXER_AUDIT.md`: current lexer rule-to-code-to-test audit and remaining verification work.
- `backend/pothos/READ.md`, `WALKTHROUGH.md`, `DECISIONS.md`: existing lexer documentation; check each against implementation before relying on it.
- `AGENTS.md`, `DEVELOPMENT.md`, `PROGRESS.md`, `DECISIONS.md`: project workflow and state records.

The root README has paths and commands that do not match the present tree (for example it describes `back-end/` and unittest suites absent from the inventory). Confirm commands and paths directly before documenting or using them.

## Working rules

- Inspect the current worktree and relevant files before editing. Preserve pre-existing user changes; never revert or overwrite unrelated work.
- Before any change to language behavior, its rules, or the paper itself, verify the discrepancy against the current paper and actual compiler behavior. Explain what is observed, what the paper says, whether either source appears wrong, the alternatives (including adjusting the paper to match a sound compiler behavior when appropriate), affected files, and focused checks. Then ask the student whether a change is actually needed and which direction to take. Wait for explicit confirmation before changing source logic or paper rules. Do not assume the paper must always change the compiler or that the compiler should always drive a paper revision.
- Structural/readability changes that demonstrably preserve behavior may proceed within an authorized task; if behavior preservation is uncertain, treat it as behavior-changing and get confirmation first.
- Keep language rules explicit and easy to locate. Separate rule data from scanning/control logic when that improves clarity, without excessive abstraction or file splitting.
- Prefer clear names, focused functions, straightforward flow, and comments for non-obvious decisions. Explain compiler concepts in student-accessible terms.
- Before implementation, report the requested change, reason, affected files, intended shape, and test plan. After implementation, explain what the code actually does and how data moves through it.
- Run relevant tests when requested or required by the task. Report exact commands and outcomes, including failures. Do not claim an unrun test passed.
- Update DEVELOPMENT.md, PROGRESS.md, DECISIONS.md, and reference documentation when task evidence or decisions change. Never mark work complete without repository or test evidence.

## Specification revisions and decisions

When a paper revision arrives, identify its title/version/date if stated, calculate or otherwise verify its fingerprint, compare affected rules with the prior verified source and actual compiler, list affected code/tests/docs, and create a task for each controlled change. Do not silently replace the working language rules. Record ambiguous or conflicting interpretations as Awaiting Approval in DECISIONS.md. Before changing either the compiler or paper to resolve a language/logic conflict, present the evidence and options and wait for the student's explicit choice. Keep paper citations exact and verifiable.

## Student learning

Explain the compiler idea before implementation and the actual algorithm after it. Use small examples, trace inputs through real functions and data structures, and distinguish C or textbook examples from Pothos behavior. Invite the student to review specification ambiguities; do not present unsupported assumptions as settled rules.
