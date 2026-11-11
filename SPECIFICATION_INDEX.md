# Pothos paper index

This is a navigation aid and discrepancy index, not a replacement language specification. The paper remains authoritative for intended Pothos behavior.

## Current paper snapshot

- **File:** `Latest_Pothos_ProgrammingLanguage.pdf` (present at repository root)
- **Title metadata:** `Latest_Pothos_ProgrammingLanguage`
- **Cover:** Pothos Compiler, BSCS 3-2 Group 3, academic year 2026–2027
- **Length:** 118 pages
- **SHA-256 verified 2026-11-11:** `6439B2D9A778B226A7AA80FFCE6699B3DE9B5545B3D7D7E7930298E7D3D40F2F`
- **Previously indexed snapshot:** 117 pages, SHA-256 `1FEE7BAEDC1EF65691DE2DF1BF32D55B1DF6F6BDCFA4106B49DB0F50DEBC36E0`. The current file differs. OCR/navigation suggests an inserted page and a one-page shift in lexical material; exact rules and diagrams must be checked visually before assuming wording is unchanged.
- **Text access:** The paper is scanned/image-based. OCR is only a navigation aid and can misread punctuation, braces, quotes, token spellings, and symbols. Inspect page images for exact notation.
- **Older copy:** `midterm documentation/Final_Midterm_Pothos_ProgrammingLanguage.pdf` is deleted from the worktree.

## Page map

Page numbers refer to PDF pages as displayed in the scanned paper.

| Pages | Topic | Development use |
|---|---|---|
| 4–5 | Language overview and program structure | Intended compiler output and program structure |
| 6–11 | General rules | Source alphabet, execution order, identifiers, statements, types/operators |
| 12–14 | Reserved words | Keyword spellings and descriptions |
| 15–16 | Reserved symbols | Operators, grouping, comments, separators |
| 17–31 | Data types and literals | Types, literals, collections, indexing |
| 32–40 | Operators, identifiers, expressions | Constraints, naming, precedence and associativity |
| 41–50 | Statements, blocks, variables, built-ins, control flow | Syntax and behavior |
| 51–65 | Functions, calls, scope, object removal | Parameters, returns, visibility, `deleo` |
| 67–69 | Regular definitions | Character classes and delimiter names/sets |
| 70–73 | Regular expressions and token definitions | Reserved word patterns and token classes |
| 74–77 | Delimiter tables | Reserved-word and symbol delimiters |
| 78–84 | Transition diagrams | Words, symbols, identifiers, numbers, strings/comments |
| 85–97 | Context-free grammar | Program, expression, statement and loop productions |
| 98–108 | FIRST set material | Predictive parsing analysis; verify calculations |
| 108–118 | FOLLOW and related parsing-set material | OCR locates FOLLOW at p.108; determine remaining artifacts visually |

## OCR-derived rule notes

These notes preserve navigation from the paper scan and earlier inspection. Confirm exact wording on cited page images before using a note to change implementation.

- Source files use `.pths`; top-level statements execute in source order (pp. 4–6).
- The paper describes an ASCII source alphabet while permitting non-ASCII data inside strings and comments (pp. 6, 17, 42–43). Current lexer rejects non-ASCII there; unresolved, see D-005.
- `wharfa` literals are unsigned; unary `-` supplies negative values. Unary `+` is described as unsupported/syntax error (p.19); phase responsibility remains to be resolved against actual parser requirements.
- Integer literals have at most 8 significant digits; excess digits are emitted as following tokens for syntax analysis to reject (pp.19–20). Float limits and malformed forms are described on pp.20–22.
- Identifiers start with a letter, continue with alphanumeric/underscore, max 20 characters; function-name minimum length is a syntax rule (pp.6, 38–39).
- Type, collection, expression, scope, and semantic constraints are described across pp.17–65. These do not establish that corresponding compiler phases exist.
- The paper includes a CFG and FIRST/FOLLOW material (pp.85–118). Exact final parsing artifacts and computed-set validity need visual verification.
- The overview describes executable output (pp.4,6); confirm course deliverable before treating code generation as in scope.

## Refresh procedure

For a new PDF, verify its fingerprint, title/version/date, and page count. Compare affected pages with this index and the implementation; keep old snapshot identity in the history when the hash changes. OCR or visually inspect relevant pages, update DEVELOPMENT.md and PROGRESS.md, and record unresolved conflicts in DECISIONS.md. Routine progress refreshes use the repository copy and do not require another upload. Never alter language behavior or paper rules without the student's explicit choice.
