import os

from flask import Flask, redirect, request

app = Flask(__name__)

TITLE = os.environ.get("APP_TITLE", "Study Group Board")

sessions = []


@app.route("/")
def home():
    html = f"<h1>{TITLE}</h1>"
    html += """
    <form method="post" action="/add">
      <input name="unit" placeholder="Unit code" required>
      <input name="topic" placeholder="Topic" required>
      <input name="when" placeholder="When and where" required>
      <button>Add</button>
    </form>
    """
    for s in sessions:
        html += f"<p>{s['unit']} - {s['topic']} - {s['when']}</p>"
    return html


@app.route("/add", methods=["POST"])
def add():
    sessions.append(request.form.to_dict())
    return redirect("/")


@app.route("/health")
def health():
    return "ok"
