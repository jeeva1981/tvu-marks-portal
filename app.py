import os
import io
import json
import uuid
from datetime import datetime, timezone, timedelta
import pandas as pd
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "tvu_super_secret_key_2026"
CORS(app)

USERS_FILE = "users.json"
LOGS_FILE = "activity_logs.json"
MARKS_STORE = {}
ABSENTEES_STORE = {}
PRACTICAL_STORE = {}

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST).strftime("%d-%m-%Y %I:%M:%S %p")

def log_activity(user, dept, action, details):
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.insert(0, {
        "time": now_ist(),
        "user": user,
        "dept": dept,
        "action": action,
        "details": details
    })
    logs = logs[:250]
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def get_logs():
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

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

def find_user_by_token(token):
    users = load_users()
    for u, info in users.items():
        if info["token"] == token and info["active"]:
            return u, info
    return None, None

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
    input { padding: 7px; margin-right: 6px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 12px; }
    button { padding: 7px 12px; background: #16a34a; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px; }
    .btn-edit { background: #2563eb; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
    th, td { padding: 9px; border: 1px solid #e2e8f0; text-align: left; }
    th { background: #f1f5f9; }
    a { color: white; text-decoration: none; font-weight: bold; }
    .badge { padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: white; }
    .b-login { background: #2563eb; }
    .b-upload { background: #16a34a; }
    .b-ext { background: #dc2626; }
    .msg { background: #dcfce7; border-left: 4px solid #16a34a; padding: 10px; margin-top: 12px; font-size: 13px; font-weight: bold; color: #166534; }
  </style>
</head>
<body>
  <div class="header">
    <h3>Super Admin Control Panel & Live Usage Monitor</h3>
    <div>
      <a href="/admin" style="margin-right:15px;">↻ Refresh</a>
      <a href="/logout">வெளியேறு (Logout)</a>
    </div>
  </div>

  {% if admin_msg %}<div class="msg">{{ admin_msg }}</div>{% endif %}

  <div class="card">
    <h4 style="margin-top:0; color:#1e3a8a;">துறைகளின் Username & Password மாற்றும் பகுதி</h4>
    <table>
      <tr><th>துறை</th><th>தற்போதைய Username & Password மாற்றம்</th><th>Extension Token</th><th>நிலை</th><th>நடவடிக்கை</th></tr>
      {% for u, info in users.items() %}
      <tr>
        <td>{{ info.dept }}</td>
        <td>
          <form method="POST" action="/admin/update/{{ u }}" style="display:flex; gap:5px; align-items:center; margin:0;">
            <input type="text" name="new_username" value="{{ u }}" style="width:110px; font-weight:bold;" required>
            <input type="text" name="new_password" value="{{ info.password }}" style="width:130px;" required>
            <button type="submit" class="btn-edit">மாற்று (Save)</button>
          </form>
        </td>
        <td style="color:#b91c1c; font-weight:bold;">{{ info.token }}</td>
        <td>{{ "Active" if info.active else "Blocked" }}</td>
        <td>
          <a href="/admin/toggle/{{ u }}" style="color:#1e3a8a; margin-right:10px;">{{ "Block" if info.active else "Allow" }}</a>
          <a href="/admin/delete/{{ u }}" style="color:#dc2626;" onclick="return confirm('இந்தக் கணக்கை நீக்க வேண்டுமா?')">நீக்கு</a>
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="card">
    <h4 style="margin-top:0;">புதிய துறை ஆசிரியர் கணக்கு உருவாக்குதல்</h4>
    <form method="POST" action="/admin/add">
      <input type="text" name="dept" placeholder="துறை பெயர் (எ.கா: Dept of Physics)" required>
      <input type="text" name="username" placeholder="Username (எ.கா: physics)" required>
      <input type="text" name="password" placeholder="Password (எ.கா: TvmPhy@2026)" required>
      <button type="submit">+ அனுமதி உருவாக்கு</button>
    </form>
  </div>

  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <h4 style="margin:0; color:#1e3a8a;">யார் யாரெல்லாம் பயன்படுத்துகிறார்கள்? (நேரடிப் பயன்பாட்டுப் பதிவு - {{ logs|length }})</h4>
      <a href="/admin/clear-logs" style="color:#dc2626; font-size:12px;">பதிவுகளை அழி (Clear Logs)</a>
    </div>
    <table>
      <tr><th>நேரம் (IST)</th><th>துறை (Department)</th><th>பயனர்</th><th>செயல்பாடு (Action)</th><th>விவரம் (Details)</th></tr>
      {% for log in logs %}
      <tr>
        <td>{{ log.time }}</td>
        <td><b>{{ log.dept }}</b></td>
        <td>{{ log.user }}</td>
        <td>
          {% if 'Login' in log.action %}<span class="badge b-login">{{ log.action }}</span>
          {% elif 'Upload' in log.action %}<span class="badge b-upload">{{ log.action }}</span>
          {% else %}<span class="badge b-ext">{{ log.action }}</span>{% endif %}
        </td>
        <td>{{ log.details }}</td>
      </tr>
      {% else %}
      <tr><td colspan="5" style="text-align:center; color:#64748b;">இதுவரை எந்தப் பயன்பாட்டுப் பதிவும் இல்லை.</td></tr>
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
    body { font-family: 'Segoe UI', sans-serif; background: #f1f5f9; padding: 20px; margin: 0; }
    .container { max-width: 820px; margin: 20px auto; }
    .header { background: #1e3a8a; color: white; padding: 15px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
    .token-bar { background: #fef9c3; border: 1px solid #fde047; padding: 12px 20px; border-radius: 6px; margin-top: 15px; font-weight: bold; }
    .menu-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 20px; }
    .menu-btn { padding: 18px 12px; border: none; border-radius: 10px; font-size: 15px; font-weight: bold; cursor: pointer; color: white; box-shadow: 0 3px 8px rgba(0,0,0,0.12); transition: transform 0.15s, opacity 0.15s; text-align: center; }
    .menu-btn:hover { transform: translateY(-2px); opacity: 0.95; }
    .menu-btn span { display: block; font-size: 11px; font-weight: normal; margin-top: 5px; opacity: 0.9; }
    .btn-tab-blue { background: #1e3a8a; }
    .btn-tab-red { background: #dc2626; }
    .btn-tab-purple { background: #7c3aed; }
    .card { background: white; padding: 22px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-top: 20px; display: none; }
    .card.active { display: block; }
    .card-head { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 12px; }
    .card-head h3 { margin: 0; color: #1e3a8a; }
    .tpl-btn { background: #0f766e; color: white !important; padding: 7px 13px; border-radius: 5px; font-size: 12px; font-weight: bold; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .tpl-btn:hover { background: #115e59; }
    .upload-box { background: #f8fafc; border: 1px dashed #94a3b8; padding: 12px; border-radius: 6px; margin-top: 10px; }
    .upload-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    label { font-weight: bold; font-size: 12px; color: #334155; display: block; margin-top: 10px; }
    input[type="text"], input[type="file"], textarea, select { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #cbd5e1; border-radius: 5px; box-sizing: border-box; background: white; }
    .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
    .btn-blue { width: 100%; padding: 11px; background: #1e3a8a; color: white; border: none; border-radius: 5px; font-weight: bold; margin-top: 15px; cursor: pointer; font-size: 14px; }
    .btn-red { width: 100%; padding: 11px; background: #dc2626; color: white; border: none; border-radius: 5px; font-weight: bold; margin-top: 15px; cursor: pointer; font-size: 14px; }
    .btn-purple { width: 100%; padding: 11px; background: #7c3aed; color: white; border: none; border-radius: 5px; font-weight: bold; margin-top: 15px; cursor: pointer; font-size: 14px; }
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

    <div class="menu-grid">
      <button type="button" class="menu-btn btn-tab-blue" onclick="openSection('marksSection')">
        1. Internal Marks Entry
        <span>அகமதிப்பீட்டு மதிப்பெண்கள்</span>
      </button>
      <button type="button" class="menu-btn btn-tab-red" onclick="openSection('absSection')">
        2. Exam Attendance Entry
        <span>தேர்வு Absentees பட்டியல்</span>
      </button>
      <button type="button" class="menu-btn btn-tab-purple" onclick="openSection('pracSection')">
        3. External Practical Marks
        <span>செய்முறைத் தேர்வு மதிப்பெண்கள்</span>
      </button>
    </div>

    <!-- 1. Internal Marks Section -->
    <div id="marksSection" class="card {% if marks_msg %}active{% endif %}">
      <div class="card-head">
        <h3>1. Internal Marks பதிவேற்றம்</h3>
        <a href="/download-template/marks" class="tpl-btn">📥 மாதிரி Excel Template பதிவிறக்கம்</a>
      </div>
      <form method="POST" action="/upload-marks" enctype="multipart/form-data">
        <p style="font-size:12px; color:#475569; margin:4px 0;"><b>குறிப்பு:</b> Template-ல் ஒவ்வொரு Sheet-ன் பெயரையும் அந்தந்த <b>Subject Code</b> (உதாரணம்: <code>23UCM11</code>, <code>23UCM12</code>) ஆக வைத்துப் பதிவேற்றவும்.</p>
        <label>பாடக் குறியீடு (ஒரே ஒரு பாடம் எனில் மட்டும்):</label>
        <input type="text" name="subject_code" placeholder="ஒவ்வொரு Sheet-லும் Subject Code பெயர் இருந்தால் காலியாக விடலாம்">
        <div class="upload-box">
          <div class="upload-row">
            <label style="margin:0;">எக்செல் கோப்பு (TVU_Internal_Marks_Template.xlsx):</label>
            <a href="/download-template/marks" style="color:#0f766e; font-size:12px; text-decoration:underline;">📥 Download Template (.xlsx)</a>
          </div>
          <input type="file" name="file" accept=".xlsx,.xls" required>
        </div>
        <button type="submit" class="btn-blue">மதிப்பெண்களைப் பதிவேற்று</button>
      </form>
      {% if marks_msg %}<div class="msg-ok">{{ marks_msg }}</div>{% endif %}
    </div>

    <!-- 2. Exam Attendance / Absentees Section -->
    <div id="absSection" class="card {% if abs_msg %}active{% endif %}">
      <div class="card-head">
        <h3 style="color:#dc2626;">2. Exam Attendance (Absentees Entry)</h3>
        <a href="/download-template/absentees" class="tpl-btn">📥 மாதிரி Excel Template பதிவிறக்கம்</a>
      </div>
      <form method="POST" action="/upload-absentees" enctype="multipart/form-data">
        <p style="font-size:12px; color:#475569; margin:4px 0;"><b>குறிப்பு:</b> ஒரே எக்செல் கோப்பில் பல பாடங்களின் (23ULT10, 23ULE10...) Absentees விவரங்களை அடுக்கி வைத்துப் பதிவேற்றலாம்.</p>
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
        <div class="upload-box">
          <div class="upload-row">
            <label style="margin:0;">வழி B: பல பாடங்கள் கொண்ட Absentees Excel கோப்பு:</label>
            <a href="/download-template/absentees" style="color:#0f766e; font-size:12px; text-decoration:underline;">📥 Download Template (.xlsx)</a>
          </div>
          <input type="file" name="abs_file" accept=".xlsx,.xls">
        </div>
        <button type="submit" class="btn-red">அனைத்துப் பாட Absentees-ஐயும் சேமி</button>
      </form>
      {% if abs_msg %}<div class="msg-ok">{{ abs_msg }}</div>{% endif %}
    </div>

    <!-- 3. External Practical Marks Section -->
    <div id="pracSection" class="card {% if prac_msg %}active{% endif %}">
      <div class="card-head">
        <h3 style="color:#7c3aed;">3. External Practical Marks பதிவேற்றம்</h3>
        <a href="/download-template/practical" class="tpl-btn">📥 மாதிரி Excel Template பதிவிறக்கம்</a>
      </div>
      <form method="POST" action="/upload-practical" enctype="multipart/form-data">
        <p style="font-size:12px; color:#475569; margin:4px 0;"><b>குறிப்பு:</b> Template-ல் <b>External Mark</b> (எ.கா: 70, 65) அல்லது Absent எனில் <b>AAA</b> என உள்ளிட்டுப் பதிவேற்றவும்.</p>
        <div class="row3">
          <div>
            <label>Degree Type:</label>
            <select name="degree_type">
              <option value="">-- Excel-ல் இருந்து --</option>
              <option value="Under Graduate">Under Graduate</option>
              <option value="Post Graduate">Post Graduate</option>
            </select>
          </div>
          <div>
            <label>Degree (எ.கா: B.Sc.):</label>
            <input type="text" name="degree" placeholder="Excel-ல் இருந்தால் விடலாம்">
          </div>
          <div>
            <label>Discipline (எ.கா: U18):</label>
            <input type="text" name="discipline" placeholder="Excel-ல் இருந்தால் விடலாம்">
          </div>
        </div>
        <div class="row3">
          <div>
            <label>Semester (எ.கா: 01):</label>
            <input type="text" name="semester" placeholder="Excel-ல் இருந்தால் விடலாம்">
          </div>
          <div>
            <label>Regulation (எ.கா: 2026):</label>
            <input type="text" name="regulation" placeholder="Excel-ல் இருந்தால் விடலாம்">
          </div>
          <div>
            <label>Exam Type:</label>
            <input type="text" name="exam_type" value="External Exam">
          </div>
        </div>
        <label>பாடக் குறியீடு (ஒரே பாடம் எனில் மட்டும்):</label>
        <input type="text" name="prac_subject_code" placeholder="பல பாடங்கள் Excel-ல் இருந்தால் காலியாக விடலாம்">
        <div class="upload-box">
          <div class="upload-row">
            <label style="margin:0;">Practical Marks Excel கோப்பு:</label>
            <a href="/download-template/practical" style="color:#0f766e; font-size:12px; text-decoration:underline;">📥 Download Template (.xlsx)</a>
          </div>
          <input type="file" name="prac_file" accept=".xlsx,.xls" required>
        </div>
        <button type="submit" class="btn-purple">Practical மதிப்பெண்களைப் பதிவேற்று</button>
      </form>
      {% if prac_msg %}<div class="msg-ok">{{ prac_msg }}</div>{% endif %}
    </div>
  </div>

  <script>
    function openSection(sectionId) {
      document.getElementById('marksSection').classList.remove('active');
      document.getElementById('absSection').classList.remove('active');
      document.getElementById('pracSection').classList.remove('active');
      document.getElementById(sectionId).classList.add('active');
    }
  </script>
</body>
</html>
"""

@app.route("/download-template/<tpl_type>")
def download_template(tpl_type):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if tpl_type == "marks":
            sample_sheets = {
                "23UCM11": [
                    {"Register No": "20423U10001", "Student Name": "AARTHI K", "Attendance": 5, "Test": 14, "Assignment": 5},
                    {"Register No": "20423U10002", "Student Name": "BALAJI S", "Attendance": 4, "Test": 12, "Assignment": 4},
                ],
                "23UCM12": [
                    {"Register No": "20423U10001", "Student Name": "AARTHI K", "Attendance": 5, "Test": 13, "Assignment": 5},
                    {"Register No": "20423U10002", "Student Name": "BALAJI S", "Attendance": 4, "Test": 11, "Assignment": 4},
                ],
                "23UCM13": [
                    {"Register No": "20423U10001", "Student Name": "AARTHI K", "Attendance": 5, "Test": 15, "Assignment": 5},
                    {"Register No": "20423U10002", "Student Name": "BALAJI S", "Attendance": 3, "Test": 10, "Assignment": 4},
                ],
            }
            for sub_name, rows in sample_sheets.items():
                pd.DataFrame(rows).to_excel(writer, sheet_name=sub_name, index=False)
            filename = "TVU_Internal_Marks_Template.xlsx"
        elif tpl_type == "absentees":
            df = pd.DataFrame([
                {"Degree Type": "Under Graduate", "Degree": "B.B.A.", "Discipline": "BUSINESS ADMINISTRATION", "Semester": "02", "Subject Code": "23ULE20", "Register No": "20423U08032"},
                {"Degree Type": "Under Graduate", "Degree": "B.B.A.", "Discipline": "BUSINESS ADMINISTRATION", "Semester": "02", "Subject Code": "23ULE20", "Register No": "20423U08140"},
                {"Degree Type": "Under Graduate", "Degree": "B.Com.", "Discipline": "U10", "Semester": "01", "Subject Code": "23ULT10", "Register No": "20424U10005"},
            ])
            df.to_excel(writer, sheet_name="Absentees_Entry", index=False)
            filename = "TVU_Absentees_Template.xlsx"
        else:
            df = pd.DataFrame([
                {"Degree Type": "Under Graduate", "Degree": "B.Sc.", "Discipline": "U18", "Semester": "01", "Regulation": "2026", "Exam Type": "External Exam", "Subject Code": "26UPCS14", "Register No": "20426U18001", "External Mark": "70"},
                {"Degree Type": "Under Graduate", "Degree": "B.Sc.", "Discipline": "U18", "Semester": "01", "Regulation": "2026", "Exam Type": "External Exam", "Subject Code": "26UPCS14", "Register No": "20426U18002", "External Mark": "65"},
                {"Degree Type": "Under Graduate", "Degree": "B.Sc.", "Discipline": "U18", "Semester": "01", "Regulation": "2026", "Exam Type": "External Exam", "Subject Code": "26UPCS14", "Register No": "20426U18003", "External Mark": "AAA"},
            ])
            df.to_excel(writer, sheet_name="Practical_Marks", index=False)
            filename = "TVU_Practical_Marks_Template.xlsx"

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "").strip().lower()
        p = request.form.get("password", "").strip()
        if u == ADMIN_USER.lower() and p == ADMIN_PASS:
            session["user"] = "admin"
            return redirect(url_for("admin_panel"))
        users = load_users()
        if u in users and users[u]["password"] == p:
            if not users[u]["active"]:
                return render_template_string(LOGIN_HTML, error="உங்கள் கணக்கு தற்காலிகமாக நிறுத்தப்பட்டுள்ளது.")
            session["user"] = u
            log_activity(u, users[u]["dept"], "Portal Login", "இணையதளத்தில் உள்நுழைந்தார்")
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_HTML, error="தவறான Username அல்லது Password!")
    return render_template_string(LOGIN_HTML, error=None)

@app.route("/admin")
def admin_panel():
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    return render_template_string(
        ADMIN_HTML,
        users=load_users(),
        logs=get_logs(),
        admin_msg=session.pop("admin_msg", None)
    )

@app.route("/admin/update/<old_username>", methods=["POST"])
def admin_update(old_username):
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    users = load_users()
    new_u = request.form.get("new_username", "").strip().lower()
    new_p = request.form.get("new_password", "").strip()
    if old_username in users and new_u and new_p:
        info = users.pop(old_username)
        info["password"] = new_p
        users[new_u] = info
        save_users(users)
        session["admin_msg"] = f"வெற்றி! '{old_username}' கணக்கு '{new_u}' (Password: {new_p}) என மாற்றப்பட்டது."
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete/<username>")
def admin_delete(username):
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        session["admin_msg"] = f"'{username}' கணக்கு நீக்கப்பட்டது."
    return redirect(url_for("admin_panel"))

@app.route("/admin/clear-logs")
def admin_clear_logs():
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    if os.path.exists(LOGS_FILE):
        os.remove(LOGS_FILE)
    return redirect(url_for("admin_panel"))

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
    session["admin_msg"] = f"புதிய கணக்கு '{u}' உருவாக்கப்பட்டது."
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
        abs_msg=session.pop("abs_msg", None),
        prac_msg=session.pop("prac_msg", None)
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
            if sheet_name.strip().lower() in ["instructions", "absentees", "absentees_entry", "practical_marks"]:
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
        log_activity(u, users[u]["dept"], "Marks Upload", f"{len(subjects_map)} பாடங்கள்: {summary}")
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
            if sheet_name.strip().lower() in ["instructions", "internal_marks", "marks", "practical_marks"]:
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
    log_activity(u, users[u]["dept"], "Absentees Upload", f"{len(subjects_map)} பாடங்கள்: {summary}")
    session["abs_msg"] = f"தயார்! மொத்தம் {len(subjects_map)} பாடங்கள் சேமிக்கப்பட்டன: {summary}."
    return redirect(url_for("dashboard"))

@app.route("/upload-practical", methods=["POST"])
def upload_practical():
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    token = users[u]["token"]

    def_deg_type = request.form.get("degree_type", "").strip()
    def_degree = request.form.get("degree", "").strip()
    def_disc = request.form.get("discipline", "").strip()
    def_sem = request.form.get("semester", "").strip()
    def_reg = request.form.get("regulation", "").strip()
    def_exam = request.form.get("exam_type", "External Exam").strip()
    def_sub = request.form.get("prac_subject_code", "").strip().upper()
    prac_file = request.files.get("prac_file")

    subjects_map = {}

    if prac_file and prac_file.filename:
        xl = pd.ExcelFile(prac_file)
        for sheet_name in xl.sheet_names:
            if sheet_name.strip().lower() in ["instructions", "absentees", "internal_marks"]:
                continue
            df = xl.parse(sheet_name, dtype=str)
            if df.empty:
                continue
            df.columns = [str(c).strip().lower() for c in df.columns]

            deg_type_col = next((c for c in df.columns if "degree type" in c or "deg_type" in c or "type" in c), None)
            deg_col = next((c for c in df.columns if "degree" in c and c != deg_type_col), None)
            disc_col = next((c for c in df.columns if "disc" in c or "branch" in c or "dept" in c), None)
            sem_col = next((c for c in df.columns if "sem" in c), None)
            regu_col = next((c for c in df.columns if "regu" in c or "batch" in c or "year" in c), None)
            exam_col = next((c for c in df.columns if "exam" in c), None)
            sub_col = next((c for c in df.columns if "sub" in c or "code" in c), None)
            regno_col = next((c for c in df.columns if "reg" in c and c != regu_col), None)
            mark_col = next((c for c in df.columns if "mark" in c or "ext" in c or "score" in c), None)

            if not regno_col or not mark_col:
                continue

            sheet_sub = def_sub if def_sub else sheet_name.strip().upper()

            for _, row in df.iterrows():
                reg = str(row[regno_col]).strip().upper() if not pd.isna(row[regno_col]) else ""
                mark = str(row[mark_col]).strip().upper() if not pd.isna(row[mark_col]) else ""
                if not reg or reg == "NAN" or not mark or mark == "NAN":
                    continue
                if mark.endswith(".0"):
                    mark = mark[:-2]

                row_sub = str(row[sub_col]).strip().upper() if (sub_col and not pd.isna(row[sub_col])) else sheet_sub
                if not row_sub or row_sub == "NAN":
                    continue

                r_deg_type = str(row[deg_type_col]).strip() if (deg_type_col and not pd.isna(row[deg_type_col])) else def_deg_type
                r_deg = str(row[deg_col]).strip() if (deg_col and not pd.isna(row[deg_col])) else def_degree
                r_disc = str(row[disc_col]).strip() if (disc_col and not pd.isna(row[disc_col])) else def_disc
                r_sem = str(row[sem_col]).strip() if (sem_col and not pd.isna(row[sem_col])) else def_sem
                if r_sem.isdigit() and len(r_sem) == 1:
                    r_sem = "0" + r_sem
                r_regu = str(row[regu_col]).strip() if (regu_col and not pd.isna(row[regu_col])) else def_reg
                if r_regu.endswith(".0"):
                    r_regu = r_regu[:-2]
                r_exam = str(row[exam_col]).strip() if (exam_col and not pd.isna(row[exam_col])) else def_exam

                if row_sub not in subjects_map:
                    subjects_map[row_sub] = {
                        "degree_type": r_deg_type,
                        "degree": r_deg,
                        "discipline": r_disc,
                        "semester": r_sem,
                        "regulation": r_regu,
                        "exam_type": r_exam,
                        "subject_code": row_sub,
                        "records": []
                    }

                subjects_map[row_sub]["records"].append({"reg": reg, "mark": mark})

    if not subjects_map:
        session["prac_msg"] = "பிழை: Register No மற்றும் External Mark நெடுவரிசைகள் காணப்படவில்லை!"
        return redirect(url_for("dashboard"))

    PRACTICAL_STORE[token] = subjects_map
    summary = ", ".join([f"{k} ({len(v['records'])} பேர்)" for k, v in subjects_map.items()])
    log_activity(u, users[u]["dept"], "Practical Upload", f"{len(subjects_map)} பாடங்கள்: {summary}")
    session["prac_msg"] = f"தயார்! மொத்தம் {len(subjects_map)} Practical பாடங்கள் சேமிக்கப்பட்டன: {summary}."
    return redirect(url_for("dashboard"))

@app.route("/api/extension/list-subjects")
def api_list_subjects():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    u, info = find_user_by_token(token)
    if not info:
        return jsonify({"success": False, "error": "Invalid or blocked User Token!"})
    abs_subs = list(ABSENTEES_STORE.get(token, {}).keys())
    marks_subs = list(MARKS_STORE.get(token, {}).keys())
    prac_subs = list(PRACTICAL_STORE.get(token, {}).keys())
    return jsonify({
        "success": True,
        "abs_subjects": abs_subs,
        "marks_subjects": marks_subs,
        "prac_subjects": prac_subs
    })

@app.route("/api/extension/get-marks")
def api_get_marks():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    req_sub = request.args.get("subject", "").strip().upper()
    u, info = find_user_by_token(token)
    if not info:
        return jsonify({"success": False, "error": "Invalid or blocked User Token!"})
    sub_map = MARKS_STORE.get(token, {})
    if not sub_map:
        return jsonify({"success": False, "error": "No Internal Marks uploaded for this token."})
    chosen = req_sub if (req_sub and req_sub in sub_map) else next(iter(sub_map))
    data = sub_map[chosen]
    log_activity(u, info["dept"], "Extension Fill Marks", f"பாடம்: {data['subject_code']} ({len(data['records'])} மாணவர்கள்)")
    return jsonify({"success": True, "subject_code": data["subject_code"], "records": data["records"]})

@app.route("/api/extension/get-absentees")
def api_get_absentees():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    req_sub = request.args.get("subject", "").strip().upper()
    u, info = find_user_by_token(token)
    if not info:
        return jsonify({"success": False, "error": "Invalid or blocked User Token!"})
    sub_map = ABSENTEES_STORE.get(token, {})
    if not sub_map:
        return jsonify({"success": False, "error": "No Absentees list uploaded for this token."})
    chosen = req_sub if (req_sub and req_sub in sub_map) else next(iter(sub_map))
    data = sub_map[chosen]
    log_activity(u, info["dept"], "Extension Mark Absentees", f"பாடம்: {data['subject_code']} ({len(data['absentees'])} பேர்)")
    return jsonify({
        "success": True,
        "degree_type": data.get("degree_type", ""),
        "degree": data.get("degree", ""),
        "discipline": data.get("discipline", ""),
        "semester": data.get("semester", ""),
        "subject_code": data["subject_code"],
        "absentees": data["absentees"]
    })

@app.route("/api/extension/get-practical")
def api_get_practical():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    req_sub = request.args.get("subject", "").strip().upper()
    u, info = find_user_by_token(token)
    if not info:
        return jsonify({"success": False, "error": "Invalid or blocked User Token!"})
    sub_map = PRACTICAL_STORE.get(token, {})
    if not sub_map:
        return jsonify({"success": False, "error": "No Practical Marks uploaded for this token."})
    chosen = req_sub if (req_sub and req_sub in sub_map) else next(iter(sub_map))
    data = sub_map[chosen]
    log_activity(u, info["dept"], "Extension Practical Marks", f"பாடம்: {data['subject_code']} ({len(data['records'])} மாணவர்கள்)")
    return jsonify({
        "success": True,
        "degree_type": data.get("degree_type", ""),
        "degree": data.get("degree", ""),
        "discipline": data.get("discipline", ""),
        "semester": data.get("semester", ""),
        "regulation": data.get("regulation", ""),
        "exam_type": data.get("exam_type", "External Exam"),
        "subject_code": data["subject_code"],
        "records": data["records"]
    })

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
