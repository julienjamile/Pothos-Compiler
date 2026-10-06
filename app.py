from pathlib import Path

from flask import Flask, send_from_directory

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"

app = Flask(__name__, static_folder=str(DIST), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(DIST, "index.html")


@app.route("/api.json", methods=['GET', 'POST'])
def api_json():
    return send_from_directory(ROOT, "api.json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)