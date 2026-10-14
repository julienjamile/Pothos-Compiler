# Frontend ↔ Backend Notes

## Server

The Flask server (`app.py`) at the repo root serves:
- `GET  /`           → `dist/index.html`  (the Vite-built frontend)
- `GET  /api.json`   → lexes `samples/sample.pths` and returns the result
- `POST /api.json`   → lexes user-submitted source and returns the result

Start it with (Linux/macOS):
```bash
.venv/bin/python app.py
```

Windows (PowerShell):
```powershell
.venv\Scripts\python app.py
```

Then open **http://localhost:5000**.

---

## POST /api.json  (submit code)

**Request headers:** `Content-Type: application/json`

**Request body:**
```json
{
  "code":         "prin(\"Hello\");",
  "skipComments": false,
  "trace":        false
}
```
- `code` *(string, required)*: Pothos source code. Windows `\r\n` and bare `\r` line endings are normalised to `\n` server-side.
- `skipComments` *(bool, optional, default `false`)*: drop `comment_sl` and `comment_ml` tokens from the response.
- `trace` *(bool, optional, default `false`)*: include `"path"` (TD state-path string) in each token dict.

**Success response (HTTP 200):**
```json
{
  "tokens": [
    {
      "no":     1,
      "lexeme": "prin",
      "token":  "prin",
      "line":   1,
      "column": 1
    }
  ],
  "errors": [
    {
      "phase":   "lexical",
      "line":    2,
      "column":  5,
      "message": "identifier exceeds 20 characters",
      "text":    "studentRegistrationNumber2026"
    }
  ],
  "phases": {
    "lexical": "ok"
  },
  "stopped_at": null
}
```

When `trace` is `true`, each token also has:
```json
{ "path": "0 -> 72 -> 73 -> 74 -> 75*" }
```

**Error responses:**

| HTTP | Body | Reason |
|------|------|--------|
| 400  | `{"error": "..."}` | Missing/invalid `code` field, malformed JSON, or wrong Content-Type |
| 413  | `{"error": "..."}` | Source code > 200 KB |

---

## GET /api.json  (sample data)

Returns the same JSON shape as the POST response, lexed from
`back-end/pothos/samples/sample.pths`. This lets the page load with real data
before the user presses Run.

---

## Token types

Token `type` (the `"token"` field) uses the token names defined by the Pothos lexer:

| Category | Examples |
|----------|---------|
| Reserved words | `belial`, `wharfa`, `prin`, `lood`, … |
| Reserved symbols | `+`, `==`, `;`, `(`, `[`, … |
| Identifier | `id` |
| Integer literal | `wharfa_lit` |
| String literal | `strina_lit` |
| Boolean literal | `trua_lit` |
| Single-line comment | `comment_sl` |
| Multi-line comment | `comment_ml` |

---

## Rebuilding the frontend

After editing `index.html`, `script.js`, or `style.css`:
```bash
npm install   # first time only
npm run build
```
The output goes to `dist/` and is served by Flask immediately.