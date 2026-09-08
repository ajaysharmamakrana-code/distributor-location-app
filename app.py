
from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import sqlite3, os, uuid
from datetime import datetime

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_FILE = os.path.join(BASE_DIR, "Distributor_Master.xlsx")
DB_FILE = os.path.join(BASE_DIR, "submissions.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_master():
    df = pd.read_excel(MASTER_FILE, dtype=str).fillna("")
    df.columns = [str(c).strip() for c in df.columns]
    return df

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                so TEXT NOT NULL,
                distributor_name TEXT NOT NULL,
                distributor_erp_id TEXT,
                city TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy REAL,
                photo_filename TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                UNIQUE(distributor_erp_id)
            )
        """)
        conn.commit()

init_db()

@app.route("/")
def index():
    df = get_master()
    sos = sorted([x for x in df["SO"].astype(str).str.strip().unique().tolist() if x])
    return render_template("index.html", sos=sos)

@app.route("/api/distributors")
def distributors():
    so = request.args.get("so", "").strip()
    df = get_master()
    sub = df[df["SO"].astype(str).str.strip() == so].copy()
    completed = set()
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute("SELECT distributor_erp_id FROM submissions").fetchall()
        completed = {str(r[0]) for r in rows if r[0] is not None}

    result = []
    for _, r in sub.iterrows():
        erp = str(r["Distributor Erp Id"]).strip()
        result.append({
            "name": str(r["Distributor Name"]).strip(),
            "erp": erp,
            "city": str(r["City"]).strip(),
            "completed": erp in completed
        })
    return jsonify(result)

@app.route("/api/submit", methods=["POST"])
def submit():
    so = request.form.get("so", "").strip()
    distributor_name = request.form.get("distributor_name", "").strip()
    erp = request.form.get("erp", "").strip()
    city = request.form.get("city", "").strip()
    lat = request.form.get("latitude", "").strip()
    lon = request.form.get("longitude", "").strip()
    accuracy = request.form.get("accuracy", "").strip()
    photo = request.files.get("photo")

    if not all([so, distributor_name, erp, lat, lon]) or photo is None or photo.filename == "":
        return jsonify({"ok": False, "message": "Photo and GPS are mandatory."}), 400

    # Validate selected distributor against master
    df = get_master()
    valid = df[
        (df["SO"].astype(str).str.strip() == so) &
        (df["Distributor Erp Id"].astype(str).str.strip() == erp)
    ]
    if valid.empty:
        return jsonify({"ok": False, "message": "Invalid SO / Distributor selection."}), 400

    try:
        lat_f = float(lat)
        lon_f = float(lon)
        acc_f = float(accuracy) if accuracy else None
    except ValueError:
        return jsonify({"ok": False, "message": "Invalid GPS coordinates."}), 400

    ext = os.path.splitext(photo.filename)[1].lower() or ".jpg"
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    filename = f"{erp}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
    photo.save(os.path.join(UPLOAD_DIR, filename))

    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                INSERT INTO submissions
                (so, distributor_name, distributor_erp_id, city, latitude, longitude, accuracy, photo_filename, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                so, distributor_name, erp, city, lat_f, lon_f, acc_f,
                filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
    except sqlite3.IntegrityError:
        try:
            os.remove(os.path.join(UPLOAD_DIR, filename))
        except OSError:
            pass
        return jsonify({"ok": False, "message": "This distributor is already completed."}), 409

    return jsonify({"ok": True, "message": "Submitted successfully. Distributor marked Completed."})

@app.route("/report")
def report():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("""
            SELECT
                so AS SO,
                distributor_name AS "Distributor Name",
                distributor_erp_id AS "Distributor Erp Id",
                city AS City,
                latitude AS Latitude,
                longitude AS Longitude,
                accuracy AS "GPS Accuracy (m)",
                submitted_at AS "Date Time",
                photo_filename AS Photo
            FROM submissions
            ORDER BY submitted_at DESC
        """, conn)

    report_file = os.path.join(BASE_DIR, "Distributor_Location_Report.xlsx")
    df.to_excel(report_file, index=False)
    return send_from_directory(BASE_DIR, "Distributor_Location_Report.xlsx", as_attachment=True)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

if __name__ == "__main__":
    # 0.0.0.0 allows phone access on the same Wi‑Fi when running locally.
    app.run(host="0.0.0.0", port=5000, debug=True)
