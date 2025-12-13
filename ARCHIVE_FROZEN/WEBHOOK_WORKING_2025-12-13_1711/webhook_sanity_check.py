from flask import Flask, request, jsonify
from datetime import datetime
import sys
import os

app = Flask(__name__)

LOG_PATH = os.path.join(os.path.dirname(__file__), "webhook_hits.log")

def log_line(text: str) -> None:
    """Append a line to webhook_hits.log and flush immediately."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {text}\n")

@app.route("/webhook", methods=["GET", "POST"])
@app.route("/webhook/", methods=["GET", "POST"])
def webhook():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build a simple summary string for the log file
    try:
        body = request.get_json(force=False, silent=True)
    except Exception as e:
        body = f"<JSON error: {e}>"

    summary = (
        f"WEBHOOK HIT | method={request.method} | "
        f"path={request.path} | "
        f"json={body} | "
        f"form={dict(request.form)} | "
        f"len(raw)={len(request.data)}"
    )
    print(summary)
    sys.stdout.flush()
    log_line(summary)

    # Return a distinctive JSON so we know this handler responded
    return jsonify({"listener": "WEBHOOK_V3_FILELOG", "ok": True}), 200


if __name__ == "__main__":
    start_msg = "=== STARTING WEBHOOK V3 FILELOG LISTENER on http://localhost:5000/webhook ==="
    print(start_msg)
    sys.stdout.flush()
    log_line(start_msg)
    app.run(host="0.0.0.0", port=5000, debug=False)
