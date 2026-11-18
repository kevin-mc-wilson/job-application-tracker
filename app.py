from flask import Flask, render_template, request, redirect
from database import get_db

app = Flask(__name__)


@app.route("/")
def dashboard():
    conn = get_db()

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS count FROM applications")
        stats = cursor.fetchone()
    finally:
        conn.close()
    return render_template("dashboard.html", stats=stats)

if __name__ == "__main__":
    app.run(debug=True)