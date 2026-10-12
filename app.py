"""
app.py  –  Flask web server for the Pothos compiler.

Endpoints
---------
GET  /                 Serve the Vite-built frontend (dist/index.html).
GET  /api.json         Return the lexed output of samples/sample.pths so the
                       page still loads even before the user types anything.
POST /api.json         Lex the Pothos source sent in the JSON body and return
                       the compiler pipeline result.

POST body (JSON):
    {
        "code"         : str,   // Pothos source code  (required)
        "skipComments" : bool,  // drop comment tokens (default: false)
        "trace"        : bool   // add TD state paths  (default: false)
    }

Success response (200):
    {
        "tokens"    : [{ "no", "lexeme", "token", "line", "column"[, "path"] }],
        "errors"    : [{ "phase", "line", "column", "message", "text" }],
        "phases"    : { "lexical": "ok" | "error" | "skipped", ... },
        "stopped_at": str | null
    }

Error responses:
    400  {"error": "<description>"}   – bad request (missing/invalid body)
    413  {"error": "<description>"}   – source too large

The lexer package lives under back-end/pothos/ (the folder name has a hyphen,
so it cannot be imported as a Python package).  We add that directory to
sys.path relative to this file so no absolute paths are baked in.
"""
import json
import os
import sys

from flask import Flask, Response, request, send_from_directory

# ── Bootstrap sys.path so the lexer / compiler packages are importable ────────
# app.py is at the repo root; back-end/pothos/ is two levels down.
_HERE = os.path.dirname(os.path.abspath(__file__))
_POTHOS_DIR = os.path.join(_HERE, "backend", "pothos")
if _POTHOS_DIR not in sys.path:
    sys.path.insert(0, _POTHOS_DIR)

from compiler import compile_source  # noqa: E402  (after sys.path patch)

# ── Flask app ─────────────────────────────────────────────────────────────────
_DIST = os.path.join(_HERE, "dist")
app = Flask(__name__, static_folder=_DIST, static_url_path="")

_MAX_SOURCE_BYTES = 200 * 1024  # 200 KB


def _json_response(data: dict, status: int = 200) -> Response:
    """Return a JSON response with the correct Content-Type header."""
    body = json.dumps(data, ensure_ascii=False)
    return Response(body, status=status, mimetype="application/json")


def _lex_sample() -> dict:
    """Lex samples/sample.pths and return the API dict (used for GET /api.json)."""
    sample_path = os.path.join(_POTHOS_DIR, "samples", "sample.pths")
    try:
        with open(sample_path, encoding="utf-8") as fh:
            source = fh.read()
    except OSError:
        source = ""
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    return compile_source(source, options={})


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return send_from_directory(_DIST, "index.html")


@app.get("/api.json")
def api_get():
    """GET /api.json – return the lexed sample.pths so the page loads cleanly."""
    return _json_response(_lex_sample())


@app.post("/api.json")
def api_post():
    """POST /api.json – lex the submitted Pothos source code."""
    # ── Validate content type ────────────────────────────────────────────────
    if not request.is_json:
        return _json_response(
            {"error": "Content-Type must be application/json"}, status=400
        )

    # ── Size guard (check raw bytes before parsing) ───────────────────────────
    if request.content_length is not None and request.content_length > _MAX_SOURCE_BYTES:
        return _json_response(
            {"error": f"Request body exceeds the {_MAX_SOURCE_BYTES // 1024} KB limit"},
            status=413,
        )

    # ── Parse body ────────────────────────────────────────────────────────────
    try:
        body = request.get_json(force=False, silent=False)
    except Exception:
        return _json_response({"error": "Invalid JSON in request body"}, status=400)

    if body is None:
        return _json_response({"error": "Request body is empty or not valid JSON"}, status=400)

    if not isinstance(body, dict):
        return _json_response({"error": "Request body must be a JSON object"}, status=400)

    code = body.get("code")
    if code is None:
        return _json_response({"error": "Missing required field: 'code'"}, status=400)

    if not isinstance(code, str):
        return _json_response({"error": "Field 'code' must be a string"}, status=400)

    # Secondary size check on the decoded string (for chunked transfers that
    # lack Content-Length).
    if len(code.encode("utf-8")) > _MAX_SOURCE_BYTES:
        return _json_response(
            {"error": f"Source code exceeds the {_MAX_SOURCE_BYTES // 1024} KB limit"},
            status=413,
        )

    # ── Normalise line endings (browser may send \r\n) ────────────────────────
    source = code.replace("\r\n", "\n").replace("\r", "\n")

    # ── Options ───────────────────────────────────────────────────────────────
    options = {
        "skipComments": bool(body.get("skipComments", False)),
        "trace": bool(body.get("trace", False)),
    }

    # ── Run compiler pipeline ─────────────────────────────────────────────────
    result = compile_source(source, options=options)
    return _json_response(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)