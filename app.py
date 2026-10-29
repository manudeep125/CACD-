"""PhishGuard AI - Flask application."""
import json
import os
import re
import sqlite3
from datetime import datetime
from urllib.parse import urlparse

import joblib
from flask import Flask, g, jsonify, render_template, request

from features import explain_url, extract_features, normalize_url

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "phishguard.db")
app = Flask(__name__)

if not os.path.exists(os.path.join(BASE, "models", "email_model.joblib")):
    raise SystemExit("Models not found. Run:  python train_model.py")
EMAIL_MODEL = joblib.load(os.path.join(BASE, "models", "email_model.joblib"))
URL_MODEL = joblib.load(os.path.join(BASE, "models", "url_model.joblib"))
with open(os.path.join(BASE, "models", "metrics.json")) as _f:
    METRICS = json.load(_f)


# ---------- database ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, input TEXT NOT NULL,
            label TEXT NOT NULL, confidence REAL NOT NULL, reasons TEXT, created_at TEXT NOT NULL)""")


def save(kind, text, label, conf, reasons):
    db = get_db()
    db.execute("INSERT INTO detections (kind,input,label,confidence,reasons,created_at) VALUES (?,?,?,?,?,?)",
               (kind, text[:2000], label, conf, json.dumps(reasons), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()


# ---------- analysis ----------
def email_reasons(text):
    tfidf, clf = EMAIL_MODEL.named_steps["tfidf"], EMAIL_MODEL.named_steps["clf"]
    vec = tfidf.transform([text])
    names = tfidf.get_feature_names_out()
    idx = vec.nonzero()[1]
    contrib = sorted(((clf.coef_[0][i] * vec[0, i], names[i]) for i in idx), reverse=True)
    words = [w for c, w in contrib if c > 0][:5]
    out = [f"Phishing-indicating terms: {', '.join(words)}"] if words else []
    if re.search(r"https?://\S+", text): out.append("Contains a link - verify the destination before clicking")
    if re.search(r"urgent|immediately|within 24 hours|final notice", text, re.I): out.append("Uses urgent / pressure language")
    return out or ["No strong phishing indicators found"]


def verdict(prob):
    return ("Phishing" if prob >= 0.5 else "Safe"), round((prob if prob >= 0.5 else 1 - prob) * 100, 2)


def error(msg, code=400):
    return jsonify({"error": msg}), code


@app.post("/api/analyze/email")
def analyze_email():
    text = ((request.get_json(silent=True) or {}).get("text") or "").strip()
    if len(text) < 20: return error("Email text must be at least 20 characters.")
    if len(text) > 10000: return error("Email text must be under 10,000 characters.")
    label, conf = verdict(EMAIL_MODEL.predict_proba([text])[0][1])
    reasons = email_reasons(text)
    save("email", text, label, conf, reasons)
    return jsonify({"label": label, "confidence": conf, "reasons": reasons})


@app.post("/api/analyze/url")
def analyze_url():
    raw = ((request.get_json(silent=True) or {}).get("url") or "").strip()
    if not raw: return error("Please enter a URL.")
    if len(raw) > 2048 or re.search(r"\s", raw): return error("URL is too long or contains spaces.")
    host = urlparse(normalize_url(raw)).hostname or ""
    if "." not in host: return error("Invalid URL: could not find a valid domain.")
    label, conf = verdict(URL_MODEL.predict_proba([extract_features(raw)])[0][1])
    reasons = explain_url(raw)
    save("url", raw, label, conf, reasons)
    return jsonify({"label": label, "confidence": conf, "reasons": reasons})


@app.get("/api/history")
def history():
    rows = get_db().execute("SELECT * FROM detections ORDER BY id DESC LIMIT 200").fetchall()
    return jsonify([{**dict(r), "reasons": json.loads(r["reasons"] or "[]")} for r in rows])


@app.delete("/api/history")
def clear_history():
    get_db().execute("DELETE FROM detections")
    get_db().commit()
    return jsonify({"ok": True})


@app.get("/api/stats")
def stats():
    db = get_db()
    one = lambda q: db.execute(q).fetchone()[0]
    daily = db.execute("""SELECT substr(created_at,1,10) d, COUNT(*) n, SUM(label='Phishing') p
                          FROM detections GROUP BY d ORDER BY d DESC LIMIT 7""").fetchall()[::-1]
    return jsonify({
        "total": one("SELECT COUNT(*) FROM detections"),
        "phishing": one("SELECT COUNT(*) FROM detections WHERE label='Phishing'"),
        "safe": one("SELECT COUNT(*) FROM detections WHERE label='Safe'"),
        "emails": one("SELECT COUNT(*) FROM detections WHERE kind='email'"),
        "urls": one("SELECT COUNT(*) FROM detections WHERE kind='url'"),
        "daily": [{"date": r["d"], "total": r["n"], "phishing": r["p"] or 0} for r in daily],
        "metrics": METRICS})


# ---------- pages ----------
@app.get("/")
def index(): return render_template("index.html", page="home")
@app.get("/dashboard")
def dashboard(): return render_template("dashboard.html", page="dashboard")
@app.get("/history")
def history_page(): return render_template("history.html", page="history")


@app.errorhandler(404)
def not_found(_):
    return error("Not found.", 404) if request.path.startswith("/api") else (render_template("index.html", page="home"), 404)


@app.errorhandler(500)
def server_error(_): return error("Internal server error.", 500)


init_db()
if __name__ == "__main__":
    app.run(debug=True)
