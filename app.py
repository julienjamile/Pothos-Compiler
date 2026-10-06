from pathlib import Path
import sys

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
POTHOS = ROOT / "back-end" / "pothos"
sys.path.insert(0, str(POTHOS))

from lexer import tokenize

app = Flask(__name__, static_folder=str(DIST), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(DIST, "index.html")


@app.route("/api.json", methods=['GET', 'POST'])
def api_json():
    if request.method == "GET":
        return send_from_directory(ROOT, "api.json")

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("code"), str):
        return jsonify({"error": "Expected a JSON object with a string 'code' field."}), 400

    tokens, errors = tokenize(payload["code"])
    return jsonify({
        "tokens": [
            {"no": number, "lexeme": token.lexeme, "token": token.type}
            for number, token in enumerate(tokens, start=1)
        ],
        "errors": [
            {"line": error.line, "column": error.column, "message": error.message}
            for error in errors
        ],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)