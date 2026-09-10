"""
Outright Payment Dashboard — Flask server for Render deployment.

Serves index.html (the dashboard) and exposes the bot-refreshed data file
at /data/dashboard_data.json so the page can fetch live numbers.

Protected by HTTP Basic Auth — set DASHBOARD_USER and DASHBOARD_PASS as
environment variables (locally via .env / shell, on Render via the
dashboard's Environment tab). Defaults below are only a fallback for local
testing and should NOT be relied on in production.
"""
import os
import json
from functools import wraps
from flask import Flask, send_from_directory, jsonify, request, Response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "dashboard_data.json")

DASHBOARD_USER = os.environ.get("DASHBOARD_USER", "admin")
DASHBOARD_PASS = os.environ.get("DASHBOARD_PASS", "changeme")

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")


def check_auth(username, password):
    return username == DASHBOARD_USER and password == DASHBOARD_PASS


def authenticate():
    return Response(
        "Login required.", 401,
        {"WWW-Authenticate": 'Basic realm="Outright Dashboard"'},
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route("/")
@requires_auth
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/data/dashboard_data.json")
@requires_auth
def dashboard_data():
    """Serves the JSON file the local bot keeps refreshing."""
    if not os.path.exists(DATA_FILE):
        return jsonify({"error": "no data yet — bot has not pushed a file"}), 404
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/healthz")
def healthz():
    # left unauthenticated so Render's health checks still pass
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
