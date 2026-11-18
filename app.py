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
    default_users = {
        "commerce": {
            "password": "1234",
            "dept": "Department of Commerce",
            "token": "TVU-COMMERCE01",
            "active": True
        },
        "jeeva": {
            "password": "TvmJee@2026",
            "dept": "Dr. Kasi Jeeva - Exam Cell",
            "token": "TVM-JEEVA01",
            "active": True
        },
        "tamil": {
            "password": "TvmTam@2026",
            "dept": "Department of Tamil",
            "token": "TVM-TAMIL01",
            "active": True
        },
        "english": {
            "password": "TvmEng@2026",
            "dept": "Department of English",
            "token": "TVM-ENGLISH01",
            "active": True
        },
        "bba": {
            "password": "TvmBba@2026",
            "dept": "Department of Business Administration",
            "token": "TVM-BBA01",
            "active": True
        },
        "maths": {
            "password": "TvmMat@2026",
            "dept": "Department of Mathematics",
            "token": "TVM-MATHS01",
            "active": True
        },
        "cs": {
            "password": "TvmCs@2026",
            "dept": "Department of Computer Science",
            "token": "TVM-CS01",
            "active": True
        }
    }
    saved = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except Exception:
            saved = {}

    updated = False
    if "mithun" in saved:
        del saved["mithun"]
        updated = True

    for k, v in default_users.items():
        if k not in saved:
            saved[k] = v
            updated = True

    if updated or not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(saved, f, indent=2)

    return saved

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
      <input type="text" name="dept" placeholder="துறை பெயர் (எ.கா: Dept of Physics)" required>
      <input type="text" name="username" placeholder="Username (எ.கா: physics)" required>
      <input type="text" name="password" placeholder="Password (எ.கா: TvmPhy@2026)" required>
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
    .container { max-width: 980px; margin: auto; }
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
    .msg-ok { background: #dcfce7; border-left: 4px solid #16a34a; padding: 12px; margin-top: 15px; font-size: 13px; line-height: 1.5; }
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
      <div class="card">
        <h3>1. Internal Marks பதிவேற்றம் (பல பாடங்கள்)</h3>
        <form method="POST" action="/upload-marks" enctype="multipart/form-data">
          <p style="font-size:12px; color:#475569; margin:4px 0;"><b>குறிப்பு:</b> எக்செல் கோப்பில் <b>Subject Code</b> நெடுவரிசை இருந்தாலோ அல்லது ஒவ்வொரு பாடத்திற்கும் தனி Sheet பெயர் (எ.கா: 23UCM11) இருந்தாலோ அனைத்தையும் ஒரே நேரத்தில் எடுத்துக்கொள்ளும்.</p>
          <label>பாடக் குறியீடு (ஒரே ஒரு பாடம் எனில் மட்டும்):</label>
          <input type="text" name="subject_code" placeholder="பல பாடங்கள் Excel-ல் இருந்தால் காலியாக விடலாம்">
          <label>எக்செல் கோப்பு (marks.xlsx):</label>
          <input type="file" name="file" accept=".xlsx,.xls" required>
          <button type="submit" class="btn-blue">மதிப்பெண்களைப் பதிவேற்று</button>
        </form>
        {% if marks_msg %}<div class="msg-ok">{{ marks_msg }}</div>{% endif %}
      </div>

      <div class="card">
        <h3>2. Exam Attendance (பல பாடங்கள் Absentees)</h3>
        <form method="POST" action="/upload-absentees" enctype="multipart/form-data">
          <p style="font-size:12px; color:#475569; margin:4px 0;"><b>குறிப்பு:</b> ஒரே எக்செல் கோப்பில் பல பாடங்களின் (23ULT10, 23ULE10...) Absentees விவரங்கள் இருந்தாலும் அனைத்தையும் தானாகப் பிரித்துச் சேமித்துக்கொள்ளும்.</p>
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
          <label>பாடக் குறியீடு (ஒரே பாடம் எனில் மட்டும்):</label>
          <input type="text" name="abs_subject_code" placeholder="பல பாடங்கள் Excel-ல் இருந்தால் காலியாக விடலாம்">
          <label>வழி A: Absent Register Numbers (Copy-Paste):</label>
          <textarea name="abs_text" rows="2" placeholder="20423U10117, 20424U10001"></textarea>
          <label>வழி B: அல்லது பல பாடங்கள் கொண்ட Absentees Excel கோப்பு:</label>
          <input type="file" name="abs_file" accept=".xlsx,.xls">
          <button type="submit" class="btn-red">அனைத்துப் பாட Absentees-ஐயும் சேமி</button>
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
        u = request.form.get("username", "").strip().lower()
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
    u = request.form.get("username").strip().lower()
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
    default_sub = request.form.get("subject_code", "").strip().upper()
    file = request.files.get("file")

    if file:
        xl = pd.ExcelFile(file)
        subjects_map = {}

        for sheet_name in xl.sheet_names:
            if sheet_name.strip().lower() in ["instructions", "absentees", "absentees_entry"]:
                continue
            df = xl.parse(sheet_name)
            if df.empty:
                continue
            df.columns = [str(c).strip().lower() for c in df.columns]

            sub_col = next((c for c in df.columns if "sub" in c or "code" in c), None)
            reg_col = next((c for c in df.columns if "reg" in c), None)
            if not reg_col:
                continue
            att_col = next((c for c in df.columns if "att" in c), None)
            test_col = next((c for c in df.columns if "test" in c or "cia" in c), None)
            ass_col = next((c for c in df.columns if "ass" in c), None)

            sheet_sub = default_sub if default_sub else sheet_name.strip().upper()

            for _, row in df.iterrows():
                reg = str(row[reg_col]).strip()
                if not reg or reg.lower() == "nan":
                    continue
                row_sub = str(row[sub_col]).strip().upper() if (sub_col and not pd.isna(row[sub_col])) else sheet_sub
                if not row_sub or row_sub == "NAN":
                    row_sub = "DEFAULT"

                subjects_map.setdefault(row_sub, {"subject_code": row_sub, "records": []})
                subjects_map[row_sub]["records"].append({
                    "reg": reg,
                    "att": "" if not att_col or pd.isna(row[att_col]) else str(int(row[att_col])) if isinstance(row[att_col], float) and row[att_col].is_integer() else str(row[att_col]).strip(),
                    "test": "" if not test_col or pd.isna(row[test_col]) else str(int(row[test_col])) if isinstance(row[test_col], float) and row[test_col].is_integer() else str(row[test_col]).strip(),
                    "ass": "" if not ass_col or pd.isna(row[ass_col]) else str(int(row[ass_col])) if isinstance(row[ass_col], float) and row[ass_col].is_integer() else str(row[ass_col]).strip()
                })

        MARKS_STORE[token] = subjects_map
        summary = ", ".join([f"{k} ({len(v['records'])})" for k, v in subjects_map.items()])
        session["marks_msg"] = f"தயார்! மொத்தம் {len(subjects_map)} பாடங்கள் பதிவேற்றப்பட்டன: {summary}."
    return redirect(url_for("dashboard"))

@app.route("/upload-absentees", methods=["POST"])
def upload_absentees():
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    token = users[u]["token"]

    def_deg_type = request.form.get("degree_type", "").strip()
    def_degree = request.form.get("degree", "").strip()
    def_disc = request.form.get("discipline", "").strip()
    def_sem = request.form.get("semester", "").strip()
    def_sub = request.form.get("abs_subject_code", "").strip().upper()
    abs_text = request.form.get("abs_text", "")
    abs_file = request.files.get("abs_file")

    subjects_map = {}

    text_regs = [x.strip().upper() for x in abs_text.replace("\n", ",").replace(" ", ",").split(",") if x.strip()]
    if text_regs and def_sub:
        subjects_map[def_sub] = {
            "degree_type": def_deg_type,
            "degree": def_degree,
            "discipline": def_disc,
            "semester": def_sem,
            "subject_code": def_sub,
            "absentees": list(dict.fromkeys(text_regs))
        }

    if abs_file and abs_file.filename:
        xl = pd.ExcelFile(abs_file)
        for sheet_name in xl.sheet_names:
            if sheet_name.strip().lower() in ["instructions", "internal_marks", "marks"]:
                continue
            df = xl.parse(sheet_name, dtype=str)
            if df.empty:
                continue
            df.columns = [str(c).strip().lower() for c in df.columns]

            deg_type_col = next((c for c in df.columns if "degree type" in c or "deg_type" in c or "type" in c), None)
            deg_col = next((c for c in df.columns if "degree" in c and c != deg_type_col), None)
            disc_col = next((c for c in df.columns if "disc" in c or "branch" in c or "dept" in c), None)
            sem_col = next((c for c in df.columns if "sem" in c), None)
            sub_col = next((c for c in df.columns if "sub" in c or "code" in c), None)
            reg_col = next((c for c in df.columns if "reg" in c), None)

            if not reg_col:
                continue

            for _, row in df.iterrows():
                reg = str(row[reg_col]).strip().upper() if not pd.isna(row[reg_col]) else ""
                if not reg or reg == "NAN":
                    continue

                row_sub = str(row[sub_col]).strip().upper() if (sub_col and not pd.isna(row[sub_col])) else def_sub
                if not row_sub or row_sub == "NAN":
                    continue

                r_deg_type = str(row[deg_type_col]).strip() if (deg_type_col and not pd.isna(row[deg_type_col])) else def_deg_type
                r_deg = str(row[deg_col]).strip() if (deg_col and not pd.isna(row[deg_col])) else def_degree
                r_disc = str(row[disc_col]).strip() if (disc_col and not pd.isna(row[disc_col])) else def_disc
                r_sem = str(row[sem_col]).strip() if (sem_col and not pd.isna(row[sem_col])) else def_sem
                if r_sem.isdigit() and len(r_sem) == 1:
                    r_sem = "0" + r_sem

                if row_sub not in subjects_map:
                    subjects_map[row_sub] = {
                        "degree_type": r_deg_type,
                        "degree": r_deg,
                        "discipline": r_disc,
                        "semester": r_sem,
                        "subject_code": row_sub,
                        "absentees": []
                    }

                if reg != row_sub and reg not in subjects_map[row_sub]["absentees"]:
                    subjects_map[row_sub]["absentees"].append(reg)

    if not subjects_map:
        session["abs_msg"] = "பிழை: பாடக் குறியீடு (Subject Code) மற்றும் Register No காணப்படவில்லை!"
        return redirect(url_for("dashboard"))

    ABSENTEES_STORE[token] = subjects_map
    summary = ", ".join([f"{k} ({len(v['absentees'])} பேர்)" for k, v in subjects_map.items()])
    session["abs_msg"] = f"தயார்! மொத்தம் {len(subjects_map)} பாடங்கள் சேமிக்கப்பட்டன: {summary}."
    return redirect(url_for("dashboard"))

@app.route("/api/extension/list-subjects")
def api_list_subjects():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    users = load_users()
    valid = any(info["token"] == token and info["active"] for info in users.values())
    if not valid:
        return jsonify({"success": False, "error": "தவறான அல்லது முடக்கப்பட்ட User Token!"})
    abs_subs = list(ABSENTEES_STORE.get(token, {}).keys())
    marks_subs = list(MARKS_STORE.get(token, {}).keys())
    return jsonify({"success": True, "abs_subjects": abs_subs, "marks_subjects": marks_subs})

@app.route("/api/extension/get-marks")
def api_get_marks():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    req_sub = request.args.get("subject", "").strip().upper()
    users = load_users()
    valid = any(info["token"] == token and info["active"] for info in users.values())
    if not valid:
        return jsonify({"success": False, "error": "தவறான அல்லது முடக்கப்பட்ட User Token!"})
    sub_map = MARKS_STORE.get(token, {})
    if not sub_map:
        return jsonify({"success": False, "error": "இந்த Token-க்கு மதிப்பெண்கள் எதுவும் பதிவேற்றப்படவில்லை."})
    chosen = req_sub if (req_sub and req_sub in sub_map) else next(iter(sub_map))
    data = sub_map[chosen]
    return jsonify({"success": True, "subject_code": data["subject_code"], "records": data["records"]})

@app.route("/api/extension/get-absentees")
def api_get_absentees():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    req_sub = request.args.get("subject", "").strip().upper()
    users = load_users()
    valid = any(info["token"] == token and info["active"] for info in users.values())
    if not valid:
        return jsonify({"success": False, "error": "தவறான அல்லது முடக்கப்பட்ட User Token!"})
    sub_map = ABSENTEES_STORE.get(token, {})
    if not sub_map:
        return jsonify({"success": False, "error": "இந்த Token-க்கு Absentees பட்டியல் எதுவும் சேமிக்கப்படவில்லை."})
    chosen = req_sub if (req_sub and req_sub in sub_map) else next(iter(sub_map))
    data = sub_map[chosen]
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
