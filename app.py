import os
import json
import uuid
import pandas as pd
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "tvu_super_secret_key_2026"
CORS(app)

USERS_FILE = "users.json"
MARKS_STORE = {}
ABSENTEES_STORE = {}

def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {
            "commerce",def load_users():
    default_users = {
        "commerce": {
            "password": "1234",
            "dept": "Department of Commerce",
            "token": "TVU-COMMERCE01",
            "active": True
        },
        "jeeva": {
            "password": "TvmMit@2026",
            "dept": "jeeva - Exam Cell",
            "token": "TVM-JEEVA01",
            "active": True
        }
    }: {
                "password": "1234",
                "dept": "Department of Commerce",
                "token": "TVU-COMMERCE01",
                "active": True
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=2)
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ta">
<head>
  <meta charset="UTF-8">
  <title>TVU Automation Portal - Login</title>
  <style>
    body { font-family: 'Segoe UI', sans-serif; background: #f1f5f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 360px; }
    h2 { color: #1e3a8a; text-align: center; margin-top: 0; }
    label { font-weight: bold; font-size: 13px; color: #334155; display: block; margin-top: 12px; }
    input { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #cbd5e1; border-radius: 5px; box-sizing: border-box; }
    button { width: 100%; padding: 11px; background: #1e3a8a; color: white; border: none; border-radius: 5px; font-weight: bold; font-size: 15px; margin-top: 20px; cursor: pointer; }
    .err { color: #dc2626; font-size: 13px; text-align: center; margin-top: 10px; }
  </style>
</head>
<body>
  <div class="box">
    <h2>TVU Automation Portal</h2>
    <form method="POST">
      <label>பயனர் பெயர் (Username):</label>
      <input type="text" name="username" required>
      <label>கடவுச்சொல் (Password):</label>
      <input type="password" name="password" required>
      <button type="submit">உள்நுழைக (Login)</button>
      {% if error %}<div class="err">{{ error }}</div>{% endif %}
    </form>
  </div>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ta">
<head>
  <meta charset="UTF-8">
  <title>Super Admin - TVU Portal</title>
  <style>
    body { font-family: 'Segoe UI', sans-serif; background: #f8fafc; padding: 25px; }
    .header { background: #1e3a8a; color: white; padding: 15px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
    .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); margin-top: 20px; }
    input { padding: 8px; margin-right: 10px; border: 1px solid #cbd5e1; border-radius: 4px; }
    button { padding: 8px 15px; background: #16a34a; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th, td { padding: 10px; border: 1px solid #e2e8f0; text-align: left; }
    th { background: #f1f5f9; }
    a { color: white; text-decoration: none; font-weight: bold; }
  </style>
</head>
<body>
  <div class="header">
    <h3>Super Admin Control Panel</h3>
    <a href="/logout">வெளியேறு (Logout)</a>
  </div>
  <div class="card">
    <h4>புதிய துறை ஆசிரியர் கணக்கு உருவாக்குதல்</h4>
    <form method="POST" action="/admin/add">
      <input type="text" name="dept" placeholder="துறை பெயர் (எ.கா: Dept of Tamil)" required>
      <input type="text" name="username" placeholder="Username (எ.கா: tamil)" required>
      <input type="text" name="password" placeholder="Password (எ.கா: TvmTam@2026)" required>
      <button type="submit">+ அனுமதி உருவாக்கு</button>
    </form>
  </div>
  <div class="card">
    <h4>அனுமதிக்கப்பட்ட துறைகள் & Extension Tokens</h4>
    <table>
      <tr><th>துறை</th><th>Username</th><th>Password</th><th>Extension Token</th><th>நிலை</th><th>நடவடிக்கை</th></tr>
      {% for u, info in users.items() %}
      <tr>
        <td>{{ info.dept }}</td>
        <td><b>{{ u }}</b></td>
        <td>{{ info.password }}</td>
        <td style="color:#b91c1c; font-weight:bold;">{{ info.token }}</td>
        <td>{{ "Active" if info.active else "Blocked" }}</td>
        <td><a href="/admin/toggle/{{ u }}" style="color:#1e3a8a;">{{ "Block செய்" if info.active else "Allow செய்" }}</a></td>
      </tr>
      {% endfor %}
    </table>
  </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ta">
<head>
  <meta charset="UTF-8">
  <title>TVU Automation Dashboard</title>
  <style>
    body { font-family: 'Segoe UI', sans-serif; background: #f1f5f9; padding: 20px; }
    .container { max-width: 960px; margin: auto; }
    .header { background: #1e3a8a; color: white; padding: 15px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
    .token-bar { background: #fef9c3; border: 1px solid #fde047; padding: 12px 20px; border-radius: 6px; margin-top: 15px; font-weight: bold; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
    .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    h3 { margin-top: 0; color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }
    label { font-weight: bold; font-size: 12px; color: #334155; display: block; margin-top: 10px; }
    input[type="text"], input[type="file"], textarea, select { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #cbd5e1; border-radius: 5px; box-sizing: border-box; }
    .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .btn-blue { width: 100%; padding: 11px; background: #1e3a8a; color: white; border: none; border-radius: 5px; font-weight: bold; margin-top: 15px; cursor: pointer; }
    .btn-red { width: 100%; padding: 11px; background: #dc2626; color: white; border: none; border-radius: 5px; font-weight: bold; margin-top: 15px; cursor: pointer; }
    .msg-ok { background: #dcfce7; border-left: 4px solid #16a34a; padding: 12px; margin-top: 15px; font-size: 13px; }
    a { color: white; text-decoration: none; font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div><b>{{ dept }}</b> ({{ username }})</div>
      <a href="/logout">வெளியேறு (Logout)</a>
    </div>

    <div class="token-bar">
      உங்கள் Extension Token: <span style="color:#dc2626;">{{ token }}</span>
    </div>

    <div class="grid">
      <!-- 1. Internal Marks Section -->
      <div class="card">
        <h3>1. Internal Marks பதிவேற்றம்</h3>
        <form method="POST" action="/upload-marks" enctype="multipart/form-data">
          <label>பாடக் குறியீடு (Subject Code - எ.கா: 26UACM13B):</label>
          <input type="text" name="subject_code" placeholder="26UACM13B" required>
          <label>எக்செல் கோப்பு (marks.xlsx):</label>
          <input type="file" name="file" accept=".xlsx,.xls" required>
          <button type="submit" class="btn-blue">மதிப்பெண்களைப் பதிவேற்று</button>
        </form>
        {% if marks_msg %}<div class="msg-ok">{{ marks_msg }}</div>{% endif %}
      </div>

      <!-- 2. Exam Attendance / Absentees Section -->
      <div class="card">
        <h3>2. Exam Attendance (Auto Dropdown & Absentees)</h3>
        <form method="POST" action="/upload-absentees" enctype="multipart/form-data">
          <p style="font-size:12px; color:#475569; margin:4px 0;"><b>குறிப்பு:</b> முழு விவரங்கள் கொண்ட Excel கோப்பைப் பதிவேற்றினால் கீழே உள்ள பெட்டிகளை நிரப்பத் தேவையில்லை.</p>
          <div class="row2">
            <div>
              <label>Degree Type (விருப்பம்):</label>
              <select name="degree_type">
                <option value="">-- Excel-ல் இருந்து எடு --</option>
                <option value="Under Graduate">Under Graduate</option>
                <option value="Post Graduate">Post Graduate</option>
              </select>
            </div>
            <div>
              <label>Degree (எ.கா: B.Com.):</label>
              <input type="text" name="degree" placeholder="Excel-ல் இருந்தால் காலியாக விடலாம்">
            </div>
          </div>
          <div class="row2">
            <div>
              <label>Discipline (எ.கா: U10):</label>
              <input type="text" name="discipline" placeholder="Excel-ல் இருந்தால் காலியாக விடலாம்">
            </div>
            <div>
              <label>Semester (எ.கா: 01):</label>
              <input type="text" name="semester" placeholder="Excel-ல் இருந்தால் காலியாக விடலாம்">
            </div>
          </div>
          <label>பாடக் குறியீடு (Subject Code):</label>
          <input type="text" name="abs_subject_code" placeholder="Excel-ல் இருந்தால் காலியாக விடலாம்">
          <label>வழி A: Absent Register Numbers (Copy-Paste):</label>
          <textarea name="abs_text" rows="2" placeholder="20423U10117, 20424U10001"></textarea>
          <label>வழி B: அல்லது முழு விவரங்கள் கொண்ட Absentees Excel கோப்பு:</label>
          <input type="file" name="abs_file" accept=".xlsx,.xls">
          <button type="submit" class="btn-red">Absentees & Dropdown விவரங்களைச் சேமி</button>
        </form>
        {% if abs_msg %}<div class="msg-ok">{{ abs_msg }}</div>{% endif %}
      </div>
    </div>
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        if u == "admin" and p == "admin123":
            session["user"] = "admin"
            return redirect(url_for("admin_panel"))
        users = load_users()
        if u in users and users[u]["password"] == p:
            if not users[u]["active"]:
                return render_template_string(LOGIN_HTML, error="உங்கள் கணக்கு தற்காலிகமாக நிறுத்தப்பட்டுள்ளது.")
            session["user"] = u
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_HTML, error="தவறான Username அல்லது Password!")
    return render_template_string(LOGIN_HTML, error=None)

@app.route("/admin")
def admin_panel():
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    return render_template_string(ADMIN_HTML, users=load_users())

@app.route("/admin/add", methods=["POST"])
def admin_add():
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    users = load_users()
    u = request.form.get("username").strip()
    users[u] = {
        "dept": request.form.get("dept").strip(),
        "password": request.form.get("password").strip(),
        "token": "TVM-" + uuid.uuid4().hex[:8].upper(),
        "active": True
    }
    save_users(users)
    return redirect(url_for("admin_panel"))

@app.route("/admin/toggle/<username>")
def admin_toggle(username):
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    users = load_users()
    if username in users:
        users[username]["active"] = not users[username]["active"]
        save_users(users)
    return redirect(url_for("admin_panel"))

@app.route("/dashboard")
def dashboard():
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    info = users[u]
    return render_template_string(
        DASHBOARD_HTML,
        dept=info["dept"],
        username=u,
        token=info["token"],
        marks_msg=session.pop("marks_msg", None),
        abs_msg=session.pop("abs_msg", None)
    )

@app.route("/upload-marks", methods=["POST"])
def upload_marks():
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    token = users[u]["token"]
    sub = request.form.get("subject_code", "").strip().upper()
    file = request.files.get("file")
    if file:
        xl = pd.ExcelFile(file)
        sheet = sub if sub in xl.sheet_names else xl.sheet_names[0]
        df = xl.parse(sheet)
        df.columns = [str(c).strip().lower() for c in df.columns]
        reg_col = next((c for c in df.columns if "reg" in c), df.columns[0])
        att_col = next((c for c in df.columns if "att" in c), None)
        test_col = next((c for c in df.columns if "test" in c or "cia" in c), None)
        ass_col = next((c for c in df.columns if "ass" in c), None)

        records = []
        for _, row in df.iterrows():
            reg = str(row[reg_col]).strip()
            if reg and reg.lower() != "nan":
                records.append({
                    "reg": reg,
                    "att": "" if not att_col or pd.isna(row[att_col]) else str(int(row[att_col])) if isinstance(row[att_col], float) and row[att_col].is_integer() else str(row[att_col]).strip(),
                    "test": "" if not test_col or pd.isna(row[test_col]) else str(int(row[test_col])) if isinstance(row[test_col], float) and row[test_col].is_integer() else str(row[test_col]).strip(),
                    "ass": "" if not ass_col or pd.isna(row[ass_col]) else str(int(row[ass_col])) if isinstance(row[ass_col], float) and row[ass_col].is_integer() else str(row[ass_col]).strip()
                })
        MARKS_STORE[token] = {"subject_code": sub, "records": records}
        session["marks_msg"] = f"தயார்! பாடம்: {sub} | மொத்த மாணவர்கள்: {len(records)}."
    return redirect(url_for("dashboard"))

@app.route("/upload-absentees", methods=["POST"])
def upload_absentees():
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    token = users[u]["token"]
    degree_type = request.form.get("degree_type", "").strip()
    degree = request.form.get("degree", "").strip()
    discipline = request.form.get("discipline", "").strip()
    semester = request.form.get("semester", "").strip()
    sub = request.form.get("abs_subject_code", "").strip().upper()
    abs_text = request.form.get("abs_text", "")
    abs_file = request.files.get("abs_file")

    abs_list = []
    for item in abs_text.replace("\n", ",").replace(" ", ",").split(","):
        cleaned = item.strip().upper()
        if cleaned and cleaned not in abs_list:
            abs_list.append(cleaned)

    if abs_file and abs_file.filename:
        df = pd.read_excel(abs_file, dtype=str)
        df.columns = [str(c).strip().lower() for c in df.columns]

        def get_first_val(keywords, exact_exclude=None):
            for col in df.columns:
                if exact_exclude and col == exact_exclude:
                    continue
                if any(k in col for k in keywords):
                    s = df[col].dropna()
                    if not s.empty:
                        return str(s.iloc[0]).strip()
            return ""

        if not degree_type:
            degree_type = get_first_val(["degree type", "deg_type", "type"])
        if not degree:
            degree = get_first_val(["degree"], exact_exclude="degree type")
        if not discipline:
            discipline = get_first_val(["disc", "branch", "dept"])
        if not semester:
            sem_val = get_first_val(["sem"])
            if sem_val.isdigit() and len(sem_val) == 1:
                sem_val = "0" + sem_val
            semester = sem_val
        if not sub:
            sub = get_first_val(["sub", "code"]).upper()

        reg_col = next((c for c in df.columns if "reg" in c), None)
        if reg_col:
            for val in df[reg_col].dropna():
                cleaned = str(val).strip().upper()
                if cleaned and cleaned != sub and cleaned not in abs_list:
                    abs_list.append(cleaned)

    if not sub:
        session["abs_msg"] = "பிழை: பாடக் குறியீடு (Subject Code) காணப்படவில்லை! Excel அல்லது பெட்டியில் உள்ளிடவும்."
        return redirect(url_for("dashboard"))

    ABSENTEES_STORE[token] = {
        "degree_type": degree_type,
        "degree": degree,
        "discipline": discipline,
        "semester": semester,
        "subject_code": sub,
        "absentees": abs_list
    }
    session["abs_msg"] = f"தயார்! {degree_type} | {degree} | {discipline} | Sem {semester} | பாடம்: {sub} | Absentees: {len(abs_list)} பேர்."
    return redirect(url_for("dashboard"))

@app.route("/api/extension/get-marks")
def api_get_marks():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    users = load_users()
    valid = any(info["token"] == token and info["active"] for info in users.values())
    if not valid:
        return jsonify({"success": False, "error": "தவறான அல்லது முடக்கப்பட்ட User Token!"})
    if token not in MARKS_STORE:
        return jsonify({"success": False, "error": "இந்த Token-க்கு மதிப்பெண்கள் எதுவும் பதிவேற்றப்படவில்லை."})
    data = MARKS_STORE[token]
    return jsonify({"success": True, "subject_code": data["subject_code"], "records": data["records"]})

@app.route("/api/extension/get-absentees")
def api_get_absentees():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    users = load_users()
    valid = any(info["token"] == token and info["active"] for info in users.values())
    if not valid:
        return jsonify({"success": False, "error": "தவறான அல்லது முடக்கப்பட்ட User Token!"})
    if token not in ABSENTEES_STORE:
        return jsonify({"success": False, "error": "இந்த Token-க்கு Absentees பட்டியல் எதுவும் சேமிக்கப்படவில்லை."})
    data = ABSENTEES_STORE[token]
    return jsonify({
        "success": True,
        "degree_type": data.get("degree_type", ""),
        "degree": data.get("degree", ""),
        "discipline": data.get("discipline", ""),
        "semester": data.get("semester", ""),
        "subject_code": data["subject_code"],
        "absentees": data["absentees"]
    })

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
