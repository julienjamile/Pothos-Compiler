# Pothos Compiler

**Pothos** is a programming language designed for BSCS 3-2 Group 3, PLM
(Polytechnic University of the Philippines – Manila), Automata Theory &
Formal Languages course.  
Source files use the **`.pths`** extension.

This repository contains:
- A complete **hand-written lexical analyser** (state machine matching transition diagrams TD1–TD5).
- A **Flask web app** that serves a CodeMirror editor and lexes Pothos source code in the browser.
- A **compiler pipeline** ready to receive syntax and semantic phases.

---

## Folder layout

```
Pothos-Compiler/
├── app.py                  Flask server (POST /api.json → runs the compiler pipeline)
├── requirements.txt        Flask>=3.0,<4.0
├── index.html              Frontend entry point (built by Vite)
├── script.js               CodeMirror editor + API client
├── style.css               UI styles
├── language.json           CodeMirror syntax configuration for Pothos
├── vite.config.mjs         Vite build config
├── package.json            npm dependencies
├── dist/                   Vite build output (served by Flask)
└── back-end/pothos/        The Pothos compiler back end
    ├── main.py             CLI: lex a .pths file or use the interactive prompt
    ├── compiler/           Compiler pipeline (pipeline.py, phases.py, serialize.py)
    ├── lexer/              Hand-written state-machine lexer (DO NOT EDIT)
    │   ├── __init__.py     Exports: tokenize, Lexer, Token, LexicalError
    │   ├── charsets.py     Character sets from the Pothos PDF (IV.B / IV.E)
    │   ├── tokens.py       Token dataclass + token-type names
    │   ├── errors.py       LexicalError dataclass
    │   └── lexer.py        The state machine (one branch per TD state)
    ├── samples/
    │   ├── sample.pths     A valid Pothos program
    │   └── errors.pths     11 lines, one lexical error each
    ├── tests/              108 lexer tests + API tests
    ├── READ.md             Lexer README
    ├── DECISIONS.md        Every PDF conflict and what the lexer does
    └── WALKTHROUGH.md      Plain-language tour of the code
```

---

## Running the web app

### 1. Set up a virtual environment

**Linux / macOS**
```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 2. (Optional) Rebuild the frontend

Only needed if you edited `index.html`, `script.js`, or `style.css`.

```bash
npm install
npm run build
```

### 3. Start the server

**Linux / macOS**
```bash
.venv/bin/python app.py
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\python app.py
```

Open **http://localhost:5000** in your browser.

---

## Running the CLI

Run from inside `back-end/pothos/`:

```bash
python main.py samples/sample.pths             # token table + errors
python main.py samples/errors.pths             # shows all 11 errors
python main.py --no-comments samples/sample.pths  # hide comment tokens
python main.py --trace samples/sample.pths     # show TD state paths
python main.py                                 # interactive prompt
```

---

## Running the tests

All tests live under `back-end/pothos/tests/`.

**Quick (from `back-end/pothos/`):**
```bash
python -m unittest
```

**Verbose (from `back-end/pothos/`):**
```bash
python -m unittest discover -s tests -v
```

**From the repo root:**
```bash
python -m unittest discover -s back-end/pothos/tests -t back-end/pothos
```

If Flask is not installed, `test_api.py` is skipped automatically — the other 108 tests still run.

---

## API format

### `POST /api.json`

**Request body** (`application/json`):
```json
{
  "code":         "<Pothos source string>",
  "skipComments": false,
  "trace":        false
}
```

**Success response** (HTTP 200):
```json
{
  "tokens": [
    { "no": 1, "lexeme": "prin", "token": "prin", "line": 1, "column": 1 }
  ],
  "errors": [
    { "phase": "lexical", "line": 1, "column": 5,
      "message": "...", "text": "..." }
  ],
  "phases":     { "lexical": "ok" },
  "stopped_at": null
}
```

When `trace` is `true`, each token also has `"path": "0 -> 72 -> ... 75*"`.

**Error responses:**
| Status | Meaning |
|--------|---------|
| 400    | Missing/invalid `code` field, bad JSON, or wrong Content-Type |
| 413    | Source code exceeds the 200 KB limit |

### `GET /api.json`

Returns the lexed output of `samples/sample.pths` (same shape as the POST response). Lets the page load with example data before the user types anything.

---

## Adding a syntax or semantic phase

1. Implement a class in `back-end/pothos/compiler/phases.py` following the `Phase` protocol (see the docstring there).
2. Import it in `back-end/pothos/compiler/pipeline.py` and append an instance to `_PHASES`.
3. That is all — the pipeline will run it after the lexical phase, stop on errors, and include its output in the response.

See `phases.py` for the placeholder `SyntaxPhase` and `SemanticPhase` stubs with detailed docstrings.
