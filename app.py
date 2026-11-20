import os
import io
import json
import uuid
from datetime import datetime, timezone, timedelta
import pandas as pd
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "college_super_secret_key_2026"
CORS(app)

USERS_FILE = "users.json"
LOGS_FILE = "activity_logs.json"
REPORTS_FILE = "exam_reports.json"

MARKS_STORE = {}
ABSENTEES_STORE = {}
PRACTICAL_STORE = {}

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST).strftime("%d-%m-%Y %I:%M:%S %p")

def today_date_ist():
    return datetime.now(IST).strftime("%Y-%m-%d")

def display_date_ist(yyyy_mm_dd):
    try:
        return datetime.strptime(yyyy_mm_dd, "%Y-%m-%d").strftime("%d-%m-%Y")
    except Exception:
        return yyyy_mm_dd

def current_session_ist():
    return "FN" if datetime.now(IST).hour < 13 else "AN"

def normalize_deg_tag(deg_type):
    dt = (deg_type or "").strip().upper()
    if "POST" in dt or dt == "PG":
        return "PG"
    if "UNDER" in dt or dt == "UG":
        return "UG"
    return ""

def make_group_key(deg_type, discipline, subject_code):
    tag = normalize_deg_tag(deg_type)
    disc = (discipline or "").strip().upper()
    sub = (subject_code or "").strip().upper()
    return f"{tag}||{disc}||{sub}"

def format_group_label(key):
    parts = [p for p in key.split("||") if p]
    return " - ".join(parts)

def load_reports():
    if os.path.exists(REPORTS_FILE):
        try:
            with open(REPORTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_reports(records):
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(records[:1500], f, indent=2, ensure_ascii=False)

def upsert_report_entry(entry):
    records = load_reports()
    records = [
        r for r in records
        if not (
            r.get("token") == entry.get("token")
            and r.get("module") == entry.get("module")
            and r.get("group_key") == entry.get("group_key")
            and r.get("date") == entry.get("date")
            and r.get("session") == entry.get("session")
        )
    ]
    records.insert(0, entry)
    save_reports(records)

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
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>College Automation Portal - Login</title>
  <style>
    body { font-family: 'Segoe UI', sans-serif; background: #f1f5f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .box { background: white; padding: 32px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 360px; }
    h2 { color: #1e3a8a; text-align: center; margin-top: 0; margin-bottom: 20px; }
    label { font-weight: bold; font-size: 13px; color: #334155; display: block; margin-top: 14px; }
    input { width: 100%; padding: 10px; margin-top: 6px; border: 1px solid #cbd5e1; border-radius: 5px; box-sizing: border-box; font-size: 14px; }
    button { width: 100%; padding: 11px; background: #1e3a8a; color: white; border: none; border-radius: 5px; font-weight: bold; font-size: 15px; margin-top: 22px; cursor: pointer; }
    button:hover { background: #172554; }
    .err { color: #dc2626; font-size: 13px; text-align: center; margin-top: 12px; font-weight: bold; }
  </style>
</head>
<body>
  <div class="box">
    <h2>College Automation Portal</h2>
    <form method="POST">
      <label>Username</label>
      <input type="text" name="username" placeholder="Enter Username" required>
      <label>Password</label>
      <input type="password" name="password" placeholder="Enter Password" required>
      <button type="submit">Login</button>
      {% if error %}<div class="err">{{ error }}</div>{% endif %}
    </form>
  </div>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>College Automation Portal - Super Admin</title>
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
    <h3>College Automation Portal - Super Admin & Live Usage Monitor</h3>
    <div>
      <a href="/admin" style="margin-right:15px;">↻ Refresh</a>
      <a href="/logout">Logout</a>
    </div>
  </div>

  {% if admin_msg %}<div class="msg">{{ admin_msg }}</div>{% endif %}

  <div class="card">
    <h4 style="margin-top:0; color:#1e3a8a;">Manage Department Credentials (Username & Password)</h4>
    <table>
      <tr><th>Department</th><th>Update Username & Password</th><th>Extension Token</th><th>Status</th><th>Action</th></tr>
      {% for u, info in users.items() %}
      <tr>
        <td>{{ info.dept }}</td>
        <td>
          <form method="POST" action="/admin/update/{{ u }}" style="display:flex; gap:5px; align-items:center; margin:0;">
            <input type="text" name="new_username" value="{{ u }}" style="width:110px; font-weight:bold;" required>
            <input type="text" name="new_password" value="{{ info.password }}" style="width:130px;" required>
            <button type="submit" class="btn-edit">Save</button>
          </form>
        </td>
        <td style="color:#b91c1c; font-weight:bold;">{{ info.token }}</td>
        <td>{{ "Active" if info.active else "Blocked" }}</td>
        <td>
          <a href="/admin/toggle/{{ u }}" style="color:#1e3a8a; margin-right:10px;">{{ "Block" if info.active else "Allow" }}</a>
          <a href="/admin/delete/{{ u }}" style="color:#dc2626;" onclick="return confirm('Delete this user account?')">Delete</a>
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="card">
    <h4 style="margin-top:0;">Add New Department Account</h4>
    <form method="POST" action="/admin/add">
      <input type="text" name="dept" placeholder="Department Name (e.g., Dept of Physics)" required>
      <input type="text" name="username" placeholder="Username (e.g., physics)" required>
      <input type="text" name="password" placeholder="Password (e.g., TvmPhy@2026)" required>
      <button type="submit">+ Create User</button>
    </form>
  </div>

  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <h4 style="margin:0; color:#1e3a8a;">Live Usage Activity Logs ({{ logs|length }})</h4>
      <a href="/admin/clear-logs" style="color:#dc2626; font-size:12px;">Clear Logs</a>
    </div>
    <table>
      <tr><th>Time (IST)</th><th>Department</th><th>Username</th><th>Action</th><th>Details</th></tr>
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
      <tr><td colspan="5" style="text-align:center; color:#64748b;">No activity recorded yet.</td></tr>
      {% endfor %}
    </table>
  </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>College Automation Portal - Dashboard</title>
  <style>
    body { font-family: 'Segoe UI', sans-serif; background: #f1f5f9; padding: 20px; margin: 0; }
    .container { max-width: 960px; margin: 15px auto; }
    .header { background: #1e3a8a; color: white; padding: 15px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
    .token-bar { background: #fef9c3; border: 1px solid #fde047; padding: 12px 20px; border-radius: 6px; margin-top: 15px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
    .menu-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 18px; }
    .menu-btn { padding: 18px 10px; border: none; border-radius: 10px; font-size: 14px; font-weight: bold; cursor: pointer; color: white; box-shadow: 0 3px 8px rgba(0,0,0,0.12); transition: transform 0.15s, opacity 0.15s; text-align: center; }
    .menu-btn:hover { transform: translateY(-2px); opacity: 0.95; }
    .btn-tab-red { background: #dc2626; }
    .btn-tab-blue { background: #1e3a8a; }
    .btn-tab-purple { background: #7c3aed; }
    .btn-tab-teal { background: #0f766e; }
    .card { background: white; padding: 22px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-top: 20px; display: none; }
    .card.active { display: block; }
    .card-head { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
    .card-head h3 { margin: 0; }
    .tpl-btn { background: #0f766e; color: white !important; padding: 7px 13px; border-radius: 5px; font-size: 12px; font-weight: bold; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; }
    .print-btn { background: #1e293b; color: white !important; padding: 7px 14px; border-radius: 5px; font-size: 12px; font-weight: bold; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; cursor: pointer; border: none; }
    .print-btn:hover { background: #0f172a; }
    .upload-box { background: #f8fafc; border: 1px dashed #94a3b8; padding: 12px; border-radius: 6px; margin-top: 10px; }
    .upload-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    label { font-weight: bold; font-size: 12px; color: #334155; display: block; margin-top: 10px; }
    input[type="text"], input[type="date"], input[type="file"], textarea, select { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #cbd5e1; border-radius: 5px; box-sizing: border-box; background: white; }
    .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
    .btn-blue { width: 100%; padding: 11px; background: #1e3a8a; color: white; border: none; border-radius: 5px; font-weight: bold; margin-top: 15px; cursor: pointer; font-size: 14px; }
    .btn-red { width: 100%; padding: 11px; background: #dc2626; color: white; border: none; border-radius: 5px; font-weight: bold; margin-top: 15px; cursor: pointer; font-size: 14px; }
    .btn-purple { width: 100%; padding: 11px; background: #7c3aed; color: white; border: none; border-radius: 5px; font-weight: bold; margin-top: 15px; cursor: pointer; font-size: 14px; }
    .msg-ok { background: #dcfce7; border-left: 4px solid #16a34a; padding: 12px; margin-top: 15px; font-size: 13px; line-height: 1.5; }
    .status-panel { margin-top: 22px; border-top: 2px solid #e2e8f0; padding-top: 15px; }
    .status-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 10px; }
    .summary-boxes { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 12px 0; }
    .s-box { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; text-align: center; }
    .s-box .num { font-size: 20px; font-weight: bold; color: #1e3a8a; }
    .s-box .lbl { font-size: 11px; color: #475569; font-weight: bold; text-transform: uppercase; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12.5px; }
    th, td { padding: 8px 10px; border: 1px solid #cbd5e1; text-align: left; }
    th { background: #f1f5f9; color: #1e293b; }
    .st-done { background: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block; }
    .st-wait { background: #dbeafe; color: #1e40af; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block; }
    .st-pend { background: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block; }
    a { color: white; text-decoration: none; font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div><b>{{ dept }}</b> ({{ username }})</div>
      <div>
        <a href="/dashboard?date={{ selected_date }}&sess={{ selected_sess }}" style="margin-right:15px;">↻ Refresh Status</a>
        <a href="/logout">Logout</a>
      </div>
    </div>

    <div class="token-bar">
      <div>Extension Token: <span style="color:#dc2626;">{{ token }}</span></div>
      <div style="font-size:12px; color:#334155;">Today: {{ today_disp }} ({{ current_sess }} Session)</div>
    </div>

    <!-- 4 Main Navigation Buttons -->
    <div class="menu-grid">
      <button type="button" class="menu-btn btn-tab-red" onclick="openSection('absSection')">
        1. Attendance Entry
      </button>
      <button type="button" class="menu-btn btn-tab-blue" onclick="openSection('marksSection')">
        2. Internal Mark Entry
      </button>
      <button type="button" class="menu-btn btn-tab-purple" onclick="openSection('pracSection')">
        3. Practical Mark Entry
      </button>
      <button type="button" class="menu-btn btn-tab-teal" onclick="openSection('reportSection')">
        4. Reports & Print Abstract
      </button>
    </div>

    <!-- 1. Attendance Entry + Daily FN/AN Live Tracker -->
    <div id="absSection" class="card {% if active_tab == 'abs' %}active{% endif %}">
      <div class="card-head">
        <h3 style="color:#dc2626;">1. Attendance Entry (FN / AN Session)</h3>
        <a href="/download-template/absentees" class="tpl-btn">📥 Download Model Excel Template</a>
      </div>
      <form method="POST" action="/upload-absentees" enctype="multipart/form-data">
        <div class="row3">
          <div>
            <label>Exam Date:</label>
            <input type="date" name="exam_date" value="{{ selected_date }}">
          </div>
          <div>
            <label>Session (FN / AN):</label>
            <select name="exam_session">
              <option value="FN" {% if current_sess == 'FN' %}selected{% endif %}>FN (Forenoon / Morning)</option>
              <option value="AN" {% if current_sess == 'AN' %}selected{% endif %}>AN (Afternoon / Evening)</option>
            </select>
          </div>
          <div>
            <label>Program Level (UG / PG):</label>
            <select name="degree_type">
              <option value="">-- Read from Excel --</option>
              <option value="Under Graduate">Under Graduate (UG)</option>
              <option value="Post Graduate">Post Graduate (PG)</option>
            </select>
          </div>
        </div>
        <div class="row3">
          <div>
            <label>Degree (e.g., B.Com. / M.Com.):</label>
            <input type="text" name="degree" placeholder="Leave blank if in Excel">
          </div>
          <div>
            <label>Discipline (e.g., U10 / P10):</label>
            <input type="text" name="discipline" placeholder="Leave blank if in Excel">
          </div>
          <div>
            <label>Semester (e.g., 01):</label>
            <input type="text" name="semester" placeholder="Leave blank if in Excel">
          </div>
        </div>
        <label>Subject Code (Only for single subject entry):</label>
        <input type="text" name="abs_subject_code" placeholder="Leave blank if multiple subjects are in Excel">
        <label>Option A: Paste Absent Register Numbers (Comma separated):</label>
        <textarea name="abs_text" rows="2" placeholder="20423U10117, 20424U10001"></textarea>
        <div class="upload-box">
          <div class="upload-row">
            <label style="margin:0;">Option B: Upload Absentees Excel File (.xlsx):</label>
            <a href="/download-template/absentees" style="color:#0f766e; font-size:12px; text-decoration:underline;">📥 Download Template (.xlsx)</a>
          </div>
          <input type="file" name="abs_file" accept=".xlsx,.xls">
        </div>
        <button type="submit" class="btn-red">Save Attendance Absentees</button>
      </form>
      {% if abs_msg %}<div class="msg-ok">{{ abs_msg }}</div>{% endif %}

      <div class="status-panel">
        <div class="status-header">
          <h4 style="margin:0; color:#1e3a8a;">Daily Attendance Tracker ({{ selected_date_disp }} - {{ selected_sess }})</h4>
          <div style="display:flex; gap:8px; align-items:center;">
            <form method="GET" action="/dashboard" style="display:flex; gap:6px; margin:0;">
              <input type="hidden" name="tab" value="abs">
              <input type="date" name="date" value="{{ selected_date }}" style="width:140px; margin:0; padding:5px;">
              <select name="sess" style="width:95px; margin:0; padding:5px;">
                <option value="ALL" {% if selected_sess == 'ALL' %}selected{% endif %}>All (FN+AN)</option>
                <option value="FN" {% if selected_sess == 'FN' %}selected{% endif %}>FN Only</option>
                <option value="AN" {% if selected_sess == 'AN' %}selected{% endif %}>AN Only</option>
              </select>
              <button type="submit" class="tpl-btn" style="border:none; cursor:pointer;">Filter</button>
            </form>
            <a href="/print-report/attendance?date={{ selected_date }}&sess={{ selected_sess }}" target="_blank" class="print-btn">🖨️ Print Attendance Report</a>
          </div>
        </div>
        <div class="summary-boxes">
          <div class="s-box"><div class="num">{{ att_summary.subjects }}</div><div class="lbl">Subjects Tracked</div></div>
          <div class="s-box"><div class="num">{{ att_summary.total }}</div><div class="lbl">Total Students</div></div>
          <div class="s-box"><div class="num" style="color:#16a34a;">{{ att_summary.present }}</div><div class="lbl">Present</div></div>
          <div class="s-box"><div class="num" style="color:#dc2626;">{{ att_summary.absent }}</div><div class="lbl">Absent</div></div>
        </div>
        <table>
          <tr><th>Session</th><th>UG/PG</th><th>Discipline</th><th>Subject Code & Title</th><th>Total</th><th>Present</th><th>Absent</th><th>Absent Reg Nos</th><th>Status</th></tr>
          {% for r in att_rows %}
          <tr>
            <td><b>{{ r.session }}</b></td>
            <td>{{ r.deg_tag }}</td>
            <td>{{ r.discipline }}</td>
            <td><b>{{ r.subject_code }}</b> {{ r.subject_title }}</td>
            <td>{{ r.total }}</td>
            <td style="color:#16a34a; font-weight:bold;">{{ r.present }}</td>
            <td style="color:#dc2626; font-weight:bold;">{{ r.absent }}</td>
            <td style="font-size:11px;">{{ r.absent_regs }}</td>
            <td>
              {% if r.status == 'Completed' %}<span class="st-done">Completed ✅</span>
              {% elif 'Filled' in r.status %}<span class="st-wait">Filled (Click SUBMIT in TVU) ⏳</span>
              {% else %}<span class="st-pend">Pending ⏳</span>{% endif %}
            </td>
          </tr>
          {% else %}
          <tr><td colspan="9" style="text-align:center; color:#64748b;">No attendance records for this date yet.</td></tr>
          {% endfor %}
        </table>
      </div>
    </div>

    <!-- 2. Internal Mark Entry + Live Status & Print Abstract -->
    <div id="marksSection" class="card {% if active_tab == 'marks' %}active{% endif %}">
      <div class="card-head">
        <h3 style="color:#1e3a8a;">2. Internal Mark Entry</h3>
        <div style="display:flex; gap:8px;">
          <a href="/download-template/marks" class="tpl-btn">📥 Download Model Excel Template</a>
          <a href="/print-report/internal" target="_blank" class="print-btn">🖨️ Print Internal Abstract</a>
        </div>
      </div>
      <form method="POST" action="/upload-marks" enctype="multipart/form-data">
        <div class="row3">
          <div>
            <label>Program Level (UG / PG):</label>
            <select name="degree_type">
              <option value="">-- Read from Excel --</option>
              <option value="Under Graduate">Under Graduate (UG)</option>
              <option value="Post Graduate">Post Graduate (PG)</option>
            </select>
          </div>
          <div>
            <label>Discipline (Optional, e.g., U10):</label>
            <input type="text" name="discipline" placeholder="Leave blank if in Excel">
          </div>
          <div>
            <label>Subject Code (Optional):</label>
            <input type="text" name="subject_code" placeholder="Leave blank if sheet names are codes">
          </div>
        </div>
        <div class="upload-box">
          <div class="upload-row">
            <label style="margin:0;">Upload Internal Marks Excel File (.xlsx):</label>
            <a href="/download-template/marks" style="color:#0f766e; font-size:12px; text-decoration:underline;">📥 Download Template (.xlsx)</a>
          </div>
          <input type="file" name="file" accept=".xlsx,.xls" required>
        </div>
        <button type="submit" class="btn-blue">Upload Internal Marks</button>
      </form>
      {% if marks_msg %}<div class="msg-ok">{{ marks_msg }}</div>{% endif %}

      <div class="status-panel">
        <div class="status-header">
          <h4 style="margin:0; color:#1e3a8a;">Internal Mark Entry Status (TVU Submit Verified)</h4>
          <a href="/print-report/internal" target="_blank" class="print-btn">🖨️ Print Internal Abstract</a>
        </div>
        <table>
          <tr><th>UG/PG</th><th>Discipline</th><th>Subject Code</th><th>Total Students</th><th>Entered</th><th>Updated Time</th><th>Status</th></tr>
          {% for r in int_rows %}
          <tr>
            <td>{{ r.deg_tag }}</td>
            <td>{{ r.discipline }}</td>
            <td><b>{{ r.subject_code }}</b></td>
            <td>{{ r.total }}</td>
            <td>{{ r.filled }}</td>
            <td>{{ r.time }}</td>
            <td>
              {% if r.status == 'Completed' %}<span class="st-done">Completed ✅</span>
              {% elif 'Filled' in r.status %}<span class="st-wait">Filled (Click SUBMIT in TVU) ⏳</span>
              {% else %}<span class="st-pend">Pending ⏳</span>{% endif %}
            </td>
          </tr>
          {% else %}
          <tr><td colspan="7" style="text-align:center; color:#64748b;">No internal mark subjects uploaded yet.</td></tr>
          {% endfor %}
        </table>
      </div>
    </div>

    <!-- 3. Practical Mark Entry + Live Status & Print Abstract -->
    <div id="pracSection" class="card {% if active_tab == 'prac' %}active{% endif %}">
      <div class="card-head">
        <h3 style="color:#7c3aed;">3. Practical Mark Entry</h3>
        <div style="display:flex; gap:8px;">
          <a href="/download-template/practical" class="tpl-btn">📥 Download Model Excel Template</a>
          <a href="/print-report/practical" target="_blank" class="print-btn">🖨️ Print Practical Abstract</a>
        </div>
      </div>
      <form method="POST" action="/upload-practical" enctype="multipart/form-data">
        <div class="row3">
          <div>
            <label>Program Level (UG / PG):</label>
            <select name="degree_type">
              <option value="">-- Read from Excel --</option>
              <option value="Under Graduate">Under Graduate (UG)</option>
              <option value="Post Graduate">Post Graduate (PG)</option>
            </select>
          </div>
          <div>
            <label>Degree (e.g., B.Sc. / M.Sc.):</label>
            <input type="text" name="degree" placeholder="Leave blank if in Excel">
          </div>
          <div>
            <label>Discipline (e.g., U18 / P18):</label>
            <input type="text" name="discipline" placeholder="Leave blank if in Excel">
          </div>
        </div>
        <div class="row3">
          <div>
            <label>Semester (e.g., 01):</label>
            <input type="text" name="semester" placeholder="Leave blank if in Excel">
          </div>
          <div>
            <label>Regulation (e.g., 2026):</label>
            <input type="text" name="regulation" placeholder="Leave blank if in Excel">
          </div>
          <div>
            <label>Exam Type:</label>
            <input type="text" name="exam_type" value="External Exam">
          </div>
        </div>
        <label>Subject Code (Only for single subject entry):</label>
        <input type="text" name="prac_subject_code" placeholder="Leave blank if multiple subjects are in Excel">
        <div class="upload-box">
          <div class="upload-row">
            <label style="margin:0;">Upload Practical Marks Excel File (.xlsx):</label>
            <a href="/download-template/practical" style="color:#0f766e; font-size:12px; text-decoration:underline;">📥 Download Template (.xlsx)</a>
          </div>
          <input type="file" name="prac_file" accept=".xlsx,.xls" required>
        </div>
        <button type="submit" class="btn-purple">Upload Practical Marks</button>
      </form>
      {% if prac_msg %}<div class="msg-ok">{{ prac_msg }}</div>{% endif %}

      <div class="status-panel">
        <div class="status-header">
          <h4 style="margin:0; color:#7c3aed;">Practical Mark Entry Status (TVU Submit Verified)</h4>
          <a href="/print-report/practical" target="_blank" class="print-btn">🖨️ Print Practical Abstract</a>
        </div>
        <table>
          <tr><th>UG/PG</th><th>Discipline</th><th>Subject Code</th><th>Total Students</th><th>Entered</th><th>Absent (AAA)</th><th>Updated Time</th><th>Status</th></tr>
          {% for r in prac_rows %}
          <tr>
            <td>{{ r.deg_tag }}</td>
            <td>{{ r.discipline }}</td>
            <td><b>{{ r.subject_code }}</b></td>
            <td>{{ r.total }}</td>
            <td>{{ r.filled }}</td>
            <td>{{ r.absent }}</td>
            <td>{{ r.time }}</td>
            <td>
              {% if r.status == 'Completed' %}<span class="st-done">Completed ✅</span>
              {% elif 'Filled' in r.status %}<span class="st-wait">Filled (Click SUBMIT in TVU) ⏳</span>
              {% else %}<span class="st-pend">Pending ⏳</span>{% endif %}
            </td>
          </tr>
          {% else %}
          <tr><td colspan="8" style="text-align:center; color:#64748b;">No practical subjects uploaded yet.</td></tr>
          {% endfor %}
        </table>
      </div>
    </div>

    <!-- 4. Consolidated Reports & Date-wise Print Center -->
    <div id="reportSection" class="card {% if active_tab == 'report' %}active{% endif %}">
      <div class="card-head">
        <h3 style="color:#0f766e;">4. Consolidated Reports & Print Center</h3>
      </div>
      <div class="row3">
        <div class="upload-box" style="text-align:center;">
          <h4 style="margin:0 0 8px 0; color:#dc2626;">Daily Attendance Report</h4>
          <form method="GET" action="/print-report/attendance" target="_blank" style="margin:0;">
            <label style="text-align:left;">Select Date:</label>
            <input type="date" name="date" value="{{ selected_date }}" required>
            <label style="text-align:left;">Session:</label>
            <select name="sess">
              <option value="ALL">All (FN & AN)</option>
              <option value="FN">FN (Forenoon)</option>
              <option value="AN">AN (Afternoon)</option>
            </select>
            <button type="submit" class="btn-red">🖨️ Print Attendance Report</button>
          </form>
        </div>

        <div class="upload-box" style="text-align:center;">
          <h4 style="margin:0 0 8px 0; color:#1e3a8a;">Internal Marks Abstract</h4>
          <p style="font-size:12px; color:#475569;">Completed: <b>{{ int_done }}</b> | Pending: <b>{{ int_pend }}</b></p>
          <a href="/print-report/internal" target="_blank" class="btn-blue" style="display:block; box-sizing:border-box; margin-top:34px;">🖨️ Print Internal Abstract</a>
        </div>

        <div class="upload-box" style="text-align:center;">
          <h4 style="margin:0 0 8px 0; color:#7c3aed;">Practical Marks Abstract</h4>
          <p style="font-size:12px; color:#475569;">Completed: <b>{{ prac_done }}</b> | Pending: <b>{{ prac_pend }}</b></p>
          <a href="/print-report/practical" target="_blank" class="btn-purple" style="display:block; box-sizing:border-box; margin-top:34px;">🖨️ Print Practical Abstract</a>
        </div>
      </div>
    </div>
  </div>

  <script>
    function openSection(sectionId) {
      document.getElementById('absSection').classList.remove('active');
      document.getElementById('marksSection').classList.remove('active');
      document.getElementById('pracSection').classList.remove('active');
      document.getElementById('reportSection').classList.remove('active');
      document.getElementById(sectionId).classList.add('active');
    }
  </script>
</body>
</html>
"""

PRINT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{{ title }} - Print Report</title>
  <style>
    body { font-family: 'Times New Roman', serif; padding: 20px; color: #000; }
    .no-print { background: #1e3a8a; color: white; padding: 10px 18px; border-radius: 6px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; font-family: 'Segoe UI', sans-serif; }
    .no-print button { background: #16a34a; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 13px; }
    .header-box { text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px; }
    .header-box h2 { margin: 0; font-size: 18px; text-transform: uppercase; }
    .header-box h3 { margin: 4px 0; font-size: 15px; }
    .meta { display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; margin-bottom: 12px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { border: 1px solid #000; padding: 7px 8px; text-align: left; }
    th { background: #f1f5f9; }
    .totals-row td { font-weight: bold; background: #f8fafc; }
    .sign-row { display: flex; justify-content: space-between; margin-top: 55px; font-weight: bold; font-size: 13px; }
    @media print {
      .no-print { display: none; }
      body { padding: 0; }
    }
  </style>
</head>
<body>
  <div class="no-print">
    <span>Print Preview Ready — Click Print to save as PDF or print on A4 paper.</span>
    <button onclick="window.print()">🖨️ Print Now</button>
  </div>

  <div class="header-box">
    <h2>Kalaignar Karunanidhi Government Arts College (204)</h2>
    <h3>{{ title }}</h3>
  </div>

  <div class="meta">
    <span>Department: {{ dept }}</span>
    <span>{{ subtitle }}</span>
    <span>Printed On: {{ printed_on }}</span>
  </div>

  <table>
    <thead>
      <tr>
        {% for h in headers %}
        <th>{{ h }}</th>
        {% endfor %}
      </tr>
    </thead>
    <tbody>
      {% for row in rows %}
      <tr>
        {% for cell in row %}
        <td>{{ cell }}</td>
        {% endfor %}
      </tr>
      {% else %}
      <tr><td colspan="{{ headers|length }}" style="text-align:center;">No records found for this selection.</td></tr>
      {% endfor %}
      {% if footer_row %}
      <tr class="totals-row">
        {% for cell in footer_row %}
        <td>{{ cell }}</td>
        {% endfor %}
      </tr>
      {% endif %}
    </tbody>
  </table>

  <div class="sign-row">
    <span>Signature of Faculty / Staff In-Charge</span>
    <span>Head of the Department</span>
    <span>Chief Superintendent / COE Cell</span>
  </div>
</body>
</html>
"""

@app.route("/download-template/<tpl_type>")
def download_template(tpl_type):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if tpl_type == "marks":
            sample_sheets = {
                "U10_23ULT10": [
                    {"Degree Type": "Under Graduate", "Discipline": "U10", "Register No": "20423U10001", "Student Name": "AARTHI K", "Attendance": 5, "Test": 14, "Assignment": 5},
                    {"Degree Type": "Under Graduate", "Discipline": "U10", "Register No": "20423U10002", "Student Name": "BALAJI S", "Attendance": 4, "Test": 12, "Assignment": 4},
                ],
                "P10_23PLT10": [
                    {"Degree Type": "Post Graduate", "Discipline": "P10", "Register No": "20423P10001", "Student Name": "DIVYA R", "Attendance": 5, "Test": 13, "Assignment": 5},
                    {"Degree Type": "Post Graduate", "Discipline": "P10", "Register No": "20423P10002", "Student Name": "GANESH M", "Attendance": 4, "Test": 11, "Assignment": 4},
                ],
            }
            for sheet_name, rows in sample_sheets.items():
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, index=False)
            filename = "College_Internal_Marks_Template.xlsx"
        elif tpl_type == "absentees":
            df = pd.DataFrame([
                {"Degree Type": "Under Graduate", "Degree": "B.Com.", "Discipline": "U10", "Semester": "01", "Subject Code": "23ULT10", "Register No": "20424U10005"},
                {"Degree Type": "Under Graduate", "Degree": "B.A.", "Discipline": "U06", "Semester": "01", "Subject Code": "23ULT10", "Register No": "20424U06008"},
                {"Degree Type": "Post Graduate", "Degree": "M.Com.", "Discipline": "P10", "Semester": "01", "Subject Code": "23PCM11", "Register No": "20424P10002"},
            ])
            df.to_excel(writer, sheet_name="Absentees_Entry", index=False)
            filename = "College_Absentees_Template.xlsx"
        else:
            df = pd.DataFrame([
                {"Degree Type": "Under Graduate", "Degree": "B.Sc.", "Discipline": "U18", "Semester": "01", "Regulation": "2026", "Exam Type": "External Exam", "Subject Code": "26UPCS14", "Register No": "20426U18001", "External Mark": "70"},
                {"Degree Type": "Post Graduate", "Degree": "M.Sc.", "Discipline": "P18", "Semester": "01", "Regulation": "2026", "Exam Type": "External Exam", "Subject Code": "26PPCS14", "Register No": "20426P18001", "External Mark": "68"},
            ])
            df.to_excel(writer, sheet_name="Practical_Marks", index=False)
            filename = "College_Practical_Marks_Template.xlsx"

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
                return render_template_string(LOGIN_HTML, error="Your account has been temporarily blocked.")
            session["user"] = u
            log_activity(u, users[u]["dept"], "Portal Login", "Logged into web portal")
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_HTML, error="Invalid Username or Password!")
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
        session["admin_msg"] = f"Updated '{old_username}' to '{new_u}' (Password: {new_p})."
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete/<username>")
def admin_delete(username):
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        session["admin_msg"] = f"Deleted account '{username}'."
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
    session["admin_msg"] = f"Created new user '{u}'."
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

def build_status_views(token, selected_date, selected_sess):
    all_reports = [r for r in load_reports() if r.get("token") == token]

    att_rows = []
    seen_att_keys = set()
    for r in all_reports:
        if r.get("module") != "attendance":
            continue
        if selected_date and r.get("date") != selected_date:
            continue
        if selected_sess and selected_sess != "ALL" and r.get("session") != selected_sess:
            continue
        seen_att_keys.add(r.get("group_key"))
        att_rows.append({
            "session": r.get("session", ""),
            "deg_tag": normalize_deg_tag(r.get("degree_type", "")),
            "discipline": r.get("discipline", ""),
            "subject_code": r.get("subject_code", ""),
            "subject_title": r.get("subject_title", ""),
            "total": r.get("total_students", 0),
            "present": r.get("present_count", 0),
            "absent": r.get("absent_count", 0),
            "absent_regs": ", ".join(r.get("absent_regs", [])) or "NIL",
            "status": r.get("status", "Completed")
        })

    for gkey, gdata in ABSENTEES_STORE.get(token, {}).items():
        g_date = gdata.get("exam_date", today_date_ist())
        g_sess = gdata.get("exam_session", "FN")
        if selected_date and g_date != selected_date:
            continue
        if selected_sess and selected_sess != "ALL" and g_sess != selected_sess:
            continue
        if gkey not in seen_att_keys:
            att_rows.append({
                "session": g_sess,
                "deg_tag": normalize_deg_tag(gdata.get("degree_type", "")),
                "discipline": gdata.get("discipline", ""),
                "subject_code": gdata.get("subject_code", ""),
                "subject_title": "(Uploaded - Pending TVU Entry)",
                "total": "-",
                "present": "-",
                "absent": len(gdata.get("absentees", [])),
                "absent_regs": ", ".join(gdata.get("absentees", [])) or "NIL",
                "status": "Pending"
            })

    att_summary = {
        "subjects": len(att_rows),
        "total": sum(r["total"] for r in att_rows if isinstance(r["total"], int)),
        "present": sum(r["present"] for r in att_rows if isinstance(r["present"], int)),
        "absent": sum(r["absent"] for r in att_rows if isinstance(r["absent"], int)),
    }

    int_rows = []
    int_done_map = {r.get("group_key"): r for r in all_reports if r.get("module") == "internal"}
    int_all_keys = list(dict.fromkeys(list(MARKS_STORE.get(token, {}).keys()) + list(int_done_map.keys())))
    for gkey in int_all_keys:
        if gkey in int_done_map:
            r = int_done_map[gkey]
            int_rows.append({
                "deg_tag": normalize_deg_tag(r.get("degree_type", "")),
                "discipline": r.get("discipline", ""),
                "subject_code": r.get("subject_code", ""),
                "total": r.get("total_students", 0),
                "filled": r.get("filled_count", 0),
                "time": r.get("updated_at", ""),
                "status": r.get("status", "Completed")
            })
        else:
            gdata = MARKS_STORE[token][gkey]
            int_rows.append({
                "deg_tag": normalize_deg_tag(gdata.get("degree_type", "")),
                "discipline": gdata.get("discipline", ""),
                "subject_code": gdata.get("subject_code", ""),
                "total": len(gdata.get("records", [])),
                "filled": 0,
                "time": "Not yet entered in TVU",
                "status": "Pending"
            })

    prac_rows = []
    prac_done_map = {r.get("group_key"): r for r in all_reports if r.get("module") == "practical"}
    prac_all_keys = list(dict.fromkeys(list(PRACTICAL_STORE.get(token, {}).keys()) + list(prac_done_map.keys())))
    for gkey in prac_all_keys:
        if gkey in prac_done_map:
            r = prac_done_map[gkey]
            prac_rows.append({
                "deg_tag": normalize_deg_tag(r.get("degree_type", "")),
                "discipline": r.get("discipline", ""),
                "subject_code": r.get("subject_code", ""),
                "total": r.get("total_students", 0),
                "filled": r.get("filled_count", 0),
                "absent": r.get("absent_count", 0),
                "time": r.get("updated_at", ""),
                "status": r.get("status", "Completed")
            })
        else:
            gdata = PRACTICAL_STORE[token][gkey]
            prac_rows.append({
                "deg_tag": normalize_deg_tag(gdata.get("degree_type", "")),
                "discipline": gdata.get("discipline", ""),
                "subject_code": gdata.get("subject_code", ""),
                "total": len(gdata.get("records", [])),
                "filled": 0,
                "absent": sum(1 for x in gdata.get("records", []) if x.get("mark", "").upper() in ["AAA", "NA", "AB"]),
                "time": "Not yet entered in TVU",
                "status": "Pending"
            })

    return att_rows, att_summary, int_rows, prac_rows

@app.route("/dashboard")
def dashboard():
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    info = users[u]
    token = info["token"]

    selected_date = request.args.get("date", today_date_ist())
    selected_sess = request.args.get("sess", "ALL")
    active_tab = request.args.get("tab", session.pop("active_tab", "abs"))

    att_rows, att_summary, int_rows, prac_rows = build_status_views(token, selected_date, selected_sess)

    return render_template_string(
        DASHBOARD_HTML,
        dept=info["dept"],
        username=u,
        token=token,
        today_disp=display_date_ist(today_date_ist()),
        current_sess=current_session_ist(),
        selected_date=selected_date,
        selected_date_disp=display_date_ist(selected_date),
        selected_sess=selected_sess,
        active_tab=active_tab,
        att_rows=att_rows,
        att_summary=att_summary,
        int_rows=int_rows,
        prac_rows=prac_rows,
        int_done=sum(1 for x in int_rows if x["status"] == "Completed"),
        int_pend=sum(1 for x in int_rows if x["status"] != "Completed"),
        prac_done=sum(1 for x in prac_rows if x["status"] == "Completed"),
        prac_pend=sum(1 for x in prac_rows if x["status"] != "Completed"),
        marks_msg=session.pop("marks_msg", None),
        abs_msg=session.pop("abs_msg", None),
        prac_msg=session.pop("prac_msg", None)
    )

@app.route("/print-report/<rep_type>")
def print_report(rep_type):
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    info = users[u]
    token = info["token"]

    selected_date = request.args.get("date", today_date_ist())
    selected_sess = request.args.get("sess", "ALL")
    att_rows, att_summary, int_rows, prac_rows = build_status_views(token, selected_date, selected_sess)

    if rep_type == "attendance":
        title = f"Daily Exam Attendance Report ({display_date_ist(selected_date)})"
        subtitle = f"Date: {display_date_ist(selected_date)} | Session: {selected_sess}"
        headers = ["S.No", "Session", "UG/PG", "Discipline", "Subject Code & Title", "Total", "Present", "Absent", "Absent Register Numbers", "Status"]
        rows = [
            [i + 1, r["session"], r["deg_tag"], r["discipline"], f"{r['subject_code']} {r['subject_title']}", r["total"], r["present"], r["absent"], r["absent_regs"], r["status"]]
            for i, r in enumerate(att_rows)
        ]
        footer = ["", "", "", "", "GRAND TOTAL", att_summary["total"], att_summary["present"], att_summary["absent"], "", ""]
    elif rep_type == "internal":
        title = "Internal Marks Entry Status Abstract"
        subtitle = f"Completed: {sum(1 for x in int_rows if x['status']=='Completed')} | Pending: {sum(1 for x in int_rows if x['status']!='Completed')}"
        headers = ["S.No", "UG/PG", "Discipline", "Subject Code", "Total Students", "Marks Entered", "Updated Time", "Status"]
        rows = [
            [i + 1, r["deg_tag"], r["discipline"], r["subject_code"], r["total"], r["filled"], r["time"], r["status"]]
            for i, r in enumerate(int_rows)
        ]
        footer = None
    else:
        title = "External Practical Marks Entry Status Abstract"
        subtitle = f"Completed: {sum(1 for x in prac_rows if x['status']=='Completed')} | Pending: {sum(1 for x in prac_rows if x['status']!='Completed')}"
        headers = ["S.No", "UG/PG", "Discipline", "Subject Code", "Total Students", "Marks Entered", "Absent (AAA)", "Updated Time", "Status"]
        rows = [
            [i + 1, r["deg_tag"], r["discipline"], r["subject_code"], r["total"], r["filled"], r["absent"], r["time"], r["status"]]
            for i, r in enumerate(prac_rows)
        ]
        footer = None

    return render_template_string(
        PRINT_HTML,
        title=title,
        dept=info["dept"],
        subtitle=subtitle,
        printed_on=now_ist(),
        headers=headers,
        rows=rows,
        footer_row=footer
    )

@app.route("/upload-marks", methods=["POST"])
def upload_marks():
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    token = users[u]["token"]
    default_deg_type = request.form.get("degree_type", "").strip()
    default_disc = request.form.get("discipline", "").strip().upper()
    default_sub = request.form.get("subject_code", "").strip().upper()
    file = request.files.get("file")

    if file:
        xl = pd.ExcelFile(file)
        groups_map = {}

        for sheet_name in xl.sheet_names:
            if sheet_name.strip().lower() in ["instructions", "absentees", "absentees_entry", "practical_marks"]:
                continue
            df = xl.parse(sheet_name)
            if df.empty:
                continue
            df.columns = [str(c).strip().lower() for c in df.columns]

            deg_type_col = next((c for c in df.columns if "degree type" in c or "deg_type" in c or "level" in c or "type" in c), None)
            disc_col = next((c for c in df.columns if "disc" in c or "branch" in c or "dept" in c), None)
            sub_col = next((c for c in df.columns if "sub" in c or "code" in c), None)
            reg_col = next((c for c in df.columns if "reg" in c), None)
            if not reg_col:
                continue
            att_col = next((c for c in df.columns if "att" in c), None)
            test_col = next((c for c in df.columns if "test" in c or "cia" in c), None)
            ass_col = next((c for c in df.columns if "ass" in c), None)

            raw_sheet = sheet_name.strip().upper()
            if "_" in raw_sheet:
                parts = raw_sheet.split("_", 1)
                sheet_disc = default_disc if default_disc else parts[0].strip()
                sheet_sub = default_sub if default_sub else parts[1].strip()
            else:
                sheet_disc = default_disc
                sheet_sub = default_sub if default_sub else raw_sheet

            for _, row in df.iterrows():
                reg = str(row[reg_col]).strip()
                if not reg or reg.lower() == "nan":
                    continue
                row_deg_type = str(row[deg_type_col]).strip() if (deg_type_col and not pd.isna(row[deg_type_col])) else default_deg_type
                if row_deg_type.lower() == "nan":
                    row_deg_type = default_deg_type
                row_disc = str(row[disc_col]).strip().upper() if (disc_col and not pd.isna(row[disc_col])) else sheet_disc
                if row_disc == "NAN":
                    row_disc = ""
                row_sub = str(row[sub_col]).strip().upper() if (sub_col and not pd.isna(row[sub_col])) else sheet_sub
                if not row_sub or row_sub == "NAN":
                    row_sub = "DEFAULT"

                gkey = make_group_key(row_deg_type, row_disc, row_sub)
                groups_map.setdefault(gkey, {"degree_type": row_deg_type, "discipline": row_disc, "subject_code": row_sub, "records": []})
                groups_map[gkey]["records"].append({
                    "reg": reg,
                    "att": "" if not att_col or pd.isna(row[att_col]) else str(int(row[att_col])) if isinstance(row[att_col], float) and row[att_col].is_integer() else str(row[att_col]).strip(),
                    "test": "" if not test_col or pd.isna(row[test_col]) else str(int(row[test_col])) if isinstance(row[test_col], float) and row[test_col].is_integer() else str(row[test_col]).strip(),
                    "ass": "" if not ass_col or pd.isna(row[ass_col]) else str(int(row[ass_col])) if isinstance(row[ass_col], float) and row[ass_col].is_integer() else str(row[ass_col]).strip()
                })

        MARKS_STORE[token] = groups_map
        summary = ", ".join([f"{format_group_label(k)} ({len(v['records'])})" for k, v in groups_map.items()])
        log_activity(u, users[u]["dept"], "Marks Upload", f"{len(groups_map)} groups: {summary}")
        session["marks_msg"] = f"Ready! Uploaded {len(groups_map)} UG/PG discipline groups: {summary}."
        session["active_tab"] = "marks"
    return redirect(url_for("dashboard"))

@app.route("/upload-absentees", methods=["POST"])
def upload_absentees():
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    token = users[u]["token"]

    exam_date = request.form.get("exam_date", today_date_ist()).strip() or today_date_ist()
    exam_session = request.form.get("exam_session", current_session_ist()).strip().upper()
    def_deg_type = request.form.get("degree_type", "").strip()
    def_degree = request.form.get("degree", "").strip()
    def_disc = request.form.get("discipline", "").strip().upper()
    def_sem = request.form.get("semester", "").strip()
    def_sub = request.form.get("abs_subject_code", "").strip().upper()
    abs_text = request.form.get("abs_text", "")
    abs_file = request.files.get("abs_file")

    groups_map = {}

    text_regs = [x.strip().upper() for x in abs_text.replace("\n", ",").replace(" ", ",").split(",") if x.strip()]
    if text_regs and def_sub:
        gkey = make_group_key(def_deg_type, def_disc, def_sub)
        groups_map[gkey] = {
            "exam_date": exam_date,
            "exam_session": exam_session,
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

            deg_type_col = next((c for c in df.columns if "degree type" in c or "deg_type" in c or "level" in c or "type" in c), None)
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
                if r_deg_type.lower() == "nan":
                    r_deg_type = def_deg_type
                r_deg = str(row[deg_col]).strip() if (deg_col and not pd.isna(row[deg_col])) else def_degree
                r_disc = str(row[disc_col]).strip().upper() if (disc_col and not pd.isna(row[disc_col])) else def_disc
                if r_disc == "NAN":
                    r_disc = ""
                r_sem = str(row[sem_col]).strip() if (sem_col and not pd.isna(row[sem_col])) else def_sem
                if r_sem.isdigit() and len(r_sem) == 1:
                    r_sem = "0" + r_sem

                gkey = make_group_key(r_deg_type, r_disc, row_sub)
                if gkey not in groups_map:
                    groups_map[gkey] = {
                        "exam_date": exam_date,
                        "exam_session": exam_session,
                        "degree_type": r_deg_type,
                        "degree": r_deg,
                        "discipline": r_disc,
                        "semester": r_sem,
                        "subject_code": row_sub,
                        "absentees": []
                    }

                if reg != row_sub and reg not in groups_map[gkey]["absentees"]:
                    groups_map[gkey]["absentees"].append(reg)

    if not groups_map:
        session["abs_msg"] = "Error: Subject Code and Register No not found!"
        session["active_tab"] = "abs"
        return redirect(url_for("dashboard"))

    ABSENTEES_STORE[token] = groups_map
    summary = ", ".join([f"{format_group_label(k)} ({len(v['absentees'])} absentees)" for k, v in groups_map.items()])
    log_activity(u, users[u]["dept"], "Absentees Upload", f"[{exam_session}] {len(groups_map)} groups: {summary}")
    session["abs_msg"] = f"Ready! Saved for {display_date_ist(exam_date)} ({exam_session}): {summary}."
    session["active_tab"] = "abs"
    return redirect(url_for("dashboard", date=exam_date, sess=exam_session))

@app.route("/upload-practical", methods=["POST"])
def upload_practical():
    u = session.get("user")
    users = load_users()
    if not u or u not in users:
        return redirect(url_for("login"))
    token = users[u]["token"]

    def_deg_type = request.form.get("degree_type", "").strip()
    def_degree = request.form.get("degree", "").strip()
    def_disc = request.form.get("discipline", "").strip().upper()
    def_sem = request.form.get("semester", "").strip()
    def_reg = request.form.get("regulation", "").strip()
    def_exam = request.form.get("exam_type", "External Exam").strip()
    def_sub = request.form.get("prac_subject_code", "").strip().upper()
    prac_file = request.files.get("prac_file")

    groups_map = {}

    if prac_file and prac_file.filename:
        xl = pd.ExcelFile(prac_file)
        for sheet_name in xl.sheet_names:
            if sheet_name.strip().lower() in ["instructions", "absentees", "internal_marks"]:
                continue
            df = xl.parse(sheet_name, dtype=str)
            if df.empty:
                continue
            df.columns = [str(c).strip().lower() for c in df.columns]

            deg_type_col = next((c for c in df.columns if "degree type" in c or "deg_type" in c or "level" in c or "type" in c), None)
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
                if r_deg_type.lower() == "nan":
                    r_deg_type = def_deg_type
                r_deg = str(row[deg_col]).strip() if (deg_col and not pd.isna(row[deg_col])) else def_degree
                r_disc = str(row[disc_col]).strip().upper() if (disc_col and not pd.isna(row[disc_col])) else def_disc
                if r_disc == "NAN":
                    r_disc = ""
                r_sem = str(row[sem_col]).strip() if (sem_col and not pd.isna(row[sem_col])) else def_sem
                if r_sem.isdigit() and len(r_sem) == 1:
                    r_sem = "0" + r_sem
                r_regu = str(row[regu_col]).strip() if (regu_col and not pd.isna(row[regu_col])) else def_reg
                if r_regu.endswith(".0"):
                    r_regu = r_regu[:-2]
                r_exam = str(row[exam_col]).strip() if (exam_col and not pd.isna(row[exam_col])) else def_exam

                gkey = make_group_key(r_deg_type, r_disc, row_sub)
                if gkey not in groups_map:
                    groups_map[gkey] = {
                        "degree_type": r_deg_type,
                        "degree": r_deg,
                        "discipline": r_disc,
                        "semester": r_sem,
                        "regulation": r_regu,
                        "exam_type": r_exam,
                        "subject_code": row_sub,
                        "records": []
                    }

                groups_map[gkey]["records"].append({"reg": reg, "mark": mark})

    if not groups_map:
        session["prac_msg"] = "Error: Register No and External Mark columns not found!"
        session["active_tab"] = "prac"
        return redirect(url_for("dashboard"))

    PRACTICAL_STORE[token] = groups_map
    summary = ", ".join([f"{format_group_label(k)} ({len(v['records'])} students)" for k, v in groups_map.items()])
    log_activity(u, users[u]["dept"], "Practical Upload", f"{len(groups_map)} groups: {summary}")
    session["prac_msg"] = f"Ready! Separated into {len(groups_map)} UG/PG discipline groups: {summary}."
    session["active_tab"] = "prac"
    return redirect(url_for("dashboard"))

@app.route("/api/extension/report-status", methods=["POST"])
def api_report_status():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    u, info = find_user_by_token(token)
    if not info:
        return jsonify({"success": False, "error": "Invalid User Token"})

    payload = request.get_json(silent=True) or {}
    module = payload.get("module", "")
    group_key = payload.get("group_key", "")
    status = payload.get("status", "Completed")

    att_meta = ABSENTEES_STORE.get(token, {}).get(group_key, {})
    exam_date = att_meta.get("exam_date", today_date_ist())
    exam_session = att_meta.get("exam_session", current_session_ist())

    entry = {
        "token": token,
        "dept": info["dept"],
        "module": module,
        "group_key": group_key,
        "date": exam_date,
        "session": exam_session,
        "degree_type": payload.get("degree_type", ""),
        "discipline": payload.get("discipline", ""),
        "subject_code": payload.get("subject_code", ""),
        "subject_title": payload.get("subject_title", ""),
        "total_students": payload.get("total_students", 0),
        "present_count": payload.get("present_count", 0),
        "absent_count": payload.get("absent_count", 0),
        "absent_regs": payload.get("absent_regs", []),
        "filled_count": payload.get("filled_count", 0),
        "status": status,
        "updated_at": now_ist()
    }
    upsert_report_entry(entry)
    if status == "Completed":
        log_activity(u, info["dept"], f"TVU Submit Confirmed ({module})", f"{format_group_label(group_key)}")
    return jsonify({"success": True})

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
    log_activity(u, info["dept"], "Extension Fill Marks", f"{format_group_label(chosen)} ({len(data['records'])} students)")
    return jsonify({
        "success": True,
        "degree_type": data.get("degree_type", ""),
        "discipline": data.get("discipline", ""),
        "subject_code": data["subject_code"],
        "records": data["records"]
    })

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
    log_activity(u, info["dept"], "Extension Mark Absentees", f"{format_group_label(chosen)} ({len(data['absentees'])} absentees)")
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
    log_activity(u, info["dept"], "Extension Practical Marks", f"{format_group_label(chosen)} ({len(data['records'])} students)")
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
