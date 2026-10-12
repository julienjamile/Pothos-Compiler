"""
test_api.py – unittest tests for the Flask /api.json endpoint.

Run from the repo root:
    python -m unittest discover -s back-end/pothos/tests -t back-end/pothos

Or from back-end/pothos/:
    python -m unittest tests.test_api

If Flask is not installed, all tests in this module are skipped automatically.
"""
import json
import os
import sys
import unittest

# ── Ensure back-end/pothos is on sys.path ────────────────────────────────────
_POTHOS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _POTHOS_DIR not in sys.path:
    sys.path.insert(0, _POTHOS_DIR)

# ── Skip the whole module if Flask is not installed ───────────────────────────
try:
    import flask  # noqa: F401
except ImportError:
    flask = None  # type: ignore

# ── repo root (two levels above back-end/pothos/) ─────────────────────────────
_REPO_ROOT = os.path.dirname(os.path.dirname(_POTHOS_DIR))

# We need the repo root on sys.path so that `from compiler import ...` works
# when app.py patches sys.path dynamically.
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@unittest.skipIf(flask is None, "Flask is not installed – skipping API tests")
class TestApiEndpoint(unittest.TestCase):
    """Integration tests for POST /api.json and GET /api.json."""

    @classmethod
    def setUpClass(cls):
        # Import app only when Flask is available.
        # app.py lives at the repo root.
        import importlib.util
        app_path = os.path.join(_REPO_ROOT, "app.py")
        spec = importlib.util.spec_from_file_location("app", app_path)
        app_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_mod)
        cls.client = app_mod.app.test_client()

    # ── Helper ────────────────────────────────────────────────────────────────

    def _post(self, body):
        """POST /api.json with a JSON body, return (status_code, parsed_json)."""
        resp = self.client.post(
            "/api.json",
            data=json.dumps(body),
            content_type="application/json",
        )
        return resp.status_code, resp.get_json()

    # ── Basic happy-path ──────────────────────────────────────────────────────

    def test_hello_world_tokens(self):
        """prin("Hello, World"); → 5 tokens, no errors."""
        code, data = self._post({"code": 'prin("Hello, World");'})
        self.assertEqual(code, 200)
        token_types = [t["token"] for t in data["tokens"]]
        self.assertEqual(token_types, ["prin", "(", "strina_lit", ")", ";"])
        self.assertEqual(data["errors"], [])

    def test_hello_world_lexemes(self):
        """Lexemes are the exact source text."""
        _, data = self._post({"code": 'prin("Hello, World");'})
        lexemes = [t["lexeme"] for t in data["tokens"]]
        self.assertEqual(lexemes, ["prin", "(", '"Hello, World"', ")", ";"])

    def test_hello_world_line_column(self):
        """All 5 tokens are on line 1; columns are 1-based."""
        _, data = self._post({"code": 'prin("Hello, World");'})
        for t in data["tokens"]:
            self.assertEqual(t["line"], 1, msg=f"token {t} not on line 1")
        # prin starts at column 1
        self.assertEqual(data["tokens"][0]["column"], 1)

    def test_hello_world_no_field(self):
        """Token 'no' field is a 1-based sequential integer."""
        _, data = self._post({"code": 'prin("Hello, World");'})
        nos = [t["no"] for t in data["tokens"]]
        self.assertEqual(nos, [1, 2, 3, 4, 5])

    def test_phases_field_present(self):
        """Response always has a 'phases' dict and a 'stopped_at' key."""
        _, data = self._post({"code": 'prin("Hello, World");'})
        self.assertIn("phases", data)
        self.assertIn("lexical", data["phases"])
        self.assertIn("stopped_at", data)

    # ── errors.pths ───────────────────────────────────────────────────────────

    def test_errors_pths_eleven_errors(self):
        """samples/errors.pths contains exactly 11 lexical errors."""
        sample = os.path.join(_POTHOS_DIR, "samples", "errors.pths")
        with open(sample, encoding="utf-8") as fh:
            source = fh.read()
        _, data = self._post({"code": source})
        self.assertEqual(len(data["errors"]), 11,
                         msg=f"Expected 11 errors, got {len(data['errors'])}: "
                             + str([e['message'] for e in data['errors']]))

    def test_errors_pths_phase_label(self):
        """Every error from errors.pths has phase == 'lexical'."""
        sample = os.path.join(_POTHOS_DIR, "samples", "errors.pths")
        with open(sample, encoding="utf-8") as fh:
            source = fh.read()
        _, data = self._post({"code": source})
        for err in data["errors"]:
            self.assertEqual(err["phase"], "lexical",
                             msg=f"Wrong phase on error: {err}")

    # ── skipComments ──────────────────────────────────────────────────────────

    def test_skip_comments_removes_comment_tokens(self):
        """skipComments=True drops comment_sl and comment_ml tokens."""
        source = '-- single-line comment\nprin("x");'
        _, with_comments = self._post({"code": source, "skipComments": False})
        _, without_comments = self._post({"code": source, "skipComments": True})
        types_with = [t["token"] for t in with_comments["tokens"]]
        types_without = [t["token"] for t in without_comments["tokens"]]
        self.assertIn("comment_sl", types_with)
        self.assertNotIn("comment_sl", types_without)
        self.assertNotIn("comment_ml", types_without)

    def test_skip_comments_ml(self):
        """skipComments=True also drops comment_ml tokens."""
        source = '/-- block comment --/ wharfa x = 1;'
        _, with_comments = self._post({"code": source, "skipComments": False})
        _, without_comments = self._post({"code": source, "skipComments": True})
        types_with = [t["token"] for t in with_comments["tokens"]]
        types_without = [t["token"] for t in without_comments["tokens"]]
        self.assertIn("comment_ml", types_with)
        self.assertNotIn("comment_ml", types_without)

    # ── trace ─────────────────────────────────────────────────────────────────

    def test_trace_adds_path_field(self):
        """trace=True adds a 'path' string to every token dict."""
        _, data = self._post({"code": 'lis x;', "trace": True})
        for t in data["tokens"]:
            self.assertIn("path", t,
                          msg=f"Token missing 'path' key: {t}")
            self.assertIsInstance(t["path"], str)

    def test_no_trace_no_path_field(self):
        """trace=False (default) omits 'path' from token dicts."""
        _, data = self._post({"code": 'lis x;'})
        for t in data["tokens"]:
            self.assertNotIn("path", t,
                             msg=f"Unexpected 'path' key in token: {t}")

    # ── CRLF normalisation ────────────────────────────────────────────────────

    def test_crlf_same_as_lf(self):
        """\\r\\n input gives the same tokens and positions as \\n input."""
        source_lf = 'lis x;\nlis y;'
        source_crlf = 'lis x;\r\nlis y;'
        _, data_lf = self._post({"code": source_lf})
        _, data_crlf = self._post({"code": source_crlf})
        # Same token types and lexemes
        self.assertEqual(
            [(t["token"], t["lexeme"]) for t in data_lf["tokens"]],
            [(t["token"], t["lexeme"]) for t in data_crlf["tokens"]],
        )
        # Same positions
        self.assertEqual(
            [(t["line"], t["column"]) for t in data_lf["tokens"]],
            [(t["line"], t["column"]) for t in data_crlf["tokens"]],
        )

    def test_cr_only_same_as_lf(self):
        """\\r input gives the same tokens and positions as \\n input."""
        source_lf = 'lis a;\nlis b;'
        source_cr = 'lis a;\rlis b;'
        _, data_lf = self._post({"code": source_lf})
        _, data_cr = self._post({"code": source_cr})
        self.assertEqual(
            [(t["token"], t["line"], t["column"]) for t in data_lf["tokens"]],
            [(t["token"], t["line"], t["column"]) for t in data_cr["tokens"]],
        )

    # ── Error responses ───────────────────────────────────────────────────────

    def test_missing_code_field_returns_400(self):
        """Omitting the 'code' field returns HTTP 400."""
        code, data = self._post({"notCode": "x"})
        self.assertEqual(code, 400)
        self.assertIn("error", data)

    def test_non_string_code_returns_400(self):
        """Passing a non-string 'code' field returns HTTP 400."""
        code, data = self._post({"code": 42})
        self.assertEqual(code, 400)
        self.assertIn("error", data)

    def test_empty_body_returns_400(self):
        """An empty body returns HTTP 400."""
        resp = self.client.post(
            "/api.json",
            data=b"",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_json_returns_400(self):
        """Malformed JSON returns HTTP 400."""
        resp = self.client.post(
            "/api.json",
            data=b"not-json{{{",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_oversized_body_returns_413(self):
        """A body exceeding 200 KB returns HTTP 413."""
        big_code = "x" * (201 * 1024)
        code, data = self._post({"code": big_code})
        self.assertEqual(code, 413)
        self.assertIn("error", data)

    def test_wrong_content_type_returns_400(self):
        """Sending a non-JSON Content-Type returns HTTP 400."""
        resp = self.client.post(
            "/api.json",
            data='{"code":"x"}',
            content_type="text/plain",
        )
        self.assertEqual(resp.status_code, 400)

    # ── GET /api.json ─────────────────────────────────────────────────────────

    def test_get_returns_valid_structure(self):
        """GET /api.json returns a valid API response (not a 404/500)."""
        resp = self.client.get("/api.json")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("tokens", data)
        self.assertIn("errors", data)
        self.assertIn("phases", data)
        self.assertIn("stopped_at", data)

    def test_get_tokens_are_lists(self):
        """GET /api.json tokens and errors fields are lists."""
        resp = self.client.get("/api.json")
        data = resp.get_json()
        self.assertIsInstance(data["tokens"], list)
        self.assertIsInstance(data["errors"], list)


if __name__ == "__main__":
    unittest.main()
