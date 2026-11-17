import os
import re
import json
import uuid
import sqlite3
import pandas as pd
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# ==============================================================================
# 1. அடிப்படை அமைப்புகள் (Super Admin Login விவரங்கள்)
# ==============================================================================
SUPER_ADMIN_USER = "admin"
SUPER_ADMIN_PASS = "admin123"
DB_PATH = "tvu_college_cloud.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "tvu_cloud_secret_key_2026")
CORS(app)

# ==============================================================================
# 2. டேட்டாபேஸ் (SQLite) அமைப்பு
# ==============================================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        department TEXT NOT NULL,
        api_token TEXT UNIQUE NOT NULL,
        is_active INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_marks (
        user_id INTEGER PRIMARY KEY,
        subject_code TEXT,
        records_json TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # ஆரம்ப Commerce கணக்கு
    c.execute("SELECT id FROM users WHERE username = 'commerce'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password_hash, department, api_token, is_active) VALUES (?, ?, ?, ?, 1)",
                  ("commerce", generate_password_hash("1234"), "Department of Commerce", "TVU-COMMERCE01"))
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

init_db()

# ==============================================================================
# 3. இணையதளப் பக்கங்கள் (HTML Templates)
# ==============================================================================
LOGIN_HTML = """<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TVU Internal Marks Portal - Login</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #e2e8f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 35px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 350px; }
        h2 { color: #1e3a8a; text-align: center; margin-bottom: 20px; }
        input { width: 100%; padding: 10px; margin: 6px 0 15px 0; border: 1px solid #cbd5e1; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 11px; background: #1e3a8a; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; font-weight: bold; }
        .err { color: #dc2626; font-size: 14px; text-align: center; margin-bottom: 10px; font-weight: bold; }
    </style>
</head>
<body>
<div class="card">
    <h2>TVU Marks Portal</h2>
    {% if error %}<div class="err">{{ error }}</div>{% endif %}
    <form method="POST">
        <label>பயனர் பெயர் (Username):</label>
        <input type="text" name="username" required>
        <label>கடவுச்சொல் (Password):</label>
        <input type="password" name="password" required>
        <button type="submit">உள்நுழைக (Login)</button>
    </form>
</div>
</body>
</html>"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Super Admin Control Panel</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f1f5f9; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e3a8a; color: white; padding: 15px 25px; border-radius: 8px; max-width: 950px; margin: auto; }
        .container { max-width: 950px; margin: 20px auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        .form-row { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        input { padding: 9px; border: 1px solid #cbd5e1; border-radius: 5px; flex: 1; min-width: 170px; }
        .btn-add { background: #16a34a; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #e2e8f0; padding: 10px; text-align: center; font-size: 14px; }
        th { background: #f8fafc; color: #1e3a8a; }
        .badge-active { background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        .badge-blocked { background: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        .btn-toggle { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; color: white; font-weight: bold; }
        .btn-block { background: #dc2626; }
        .btn-allow { background: #2563eb; }
        .btn-del { background: #64748b; margin-left: 5px; }
    </style>
</head>
<body>
<div class="header">
    <div><strong>கல்லூரி நிர்வாகி கட்டுப்பாட்டு அறை (Super Admin)</strong></div>
    <div><a href="/logout" style="color: #fde047; text-decoration: none; font-weight: bold;">வெளியேறு</a></div>
</div>
<div class="container">
    <h3>புதிய துறை கணக்கு உருவாக்குதல்</h3>
    <form method="POST" action="/admin/create_user" class="form-row">
        <input type="text" name="department" placeholder="துறை பெயர் (எ.கா: Tamil / CS)" required>
        <input type="text" name="username" placeholder="Username" required>
        <input type="text" name="password" placeholder="Password" required>
        <button type="submit" class="btn-add">+ அனுமதி உருவாக்கு</button>
    </form>
    <table>
        <tr><th>துறை</th><th>Username</th><th>Extension Token</th><th>நிலை</th><th>கட்டுப்பாடு</th></tr>
        {% for u in users %}
        <tr>
            <td>{{ u['department'] }}</td>
            <td><b>{{ u['username'] }}</b></td>
            <td><code style="color:#b91c1c; font-weight:bold;">{{ u['api_token'] }}</code></td>
            <td>{% if u['is_active'] == 1 %}<span class="badge-active">Active</span>{% else %}<span class="badge-blocked">Blocked</span>{% endif %}</td>
            <td>
                <form method="POST" action="/admin/toggle_user/{{ u['id'] }}" style="display:inline;">
                    {% if u['is_active'] == 1 %}<button class="btn-toggle btn-block">Block</button>{% else %}<button class="btn-toggle btn-allow">Allow</button>{% endif %}
                </form>
                <form method="POST" action="/admin/delete_user/{{ u['id'] }}" style="display:inline;" onsubmit="return confirm('நீக்கலாமா?');">
                    <button class="btn-toggle btn-del">நீக்கு</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
</body>
</html>"""

STAFF_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ user['department'] }} - Internal Marks</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1f497d; color: white; padding: 15px 25px; border-radius: 8px; max-width: 750px; margin: auto; }
        .container { max-width: 750px; margin: 20px auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .token-alert { background: #fef9c3; border-left: 4px solid #ca8a04; padding: 12px; margin-bottom: 20px; font-size: 14px; }
        label { font-weight: bold; display: block; margin-top: 15px; }
        input[type="text"], input[type="file"] { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background: #1f497d; color: white; border: none; padding: 12px; font-size: 16px; border-radius: 5px; cursor: pointer; margin-top: 20px; width: 100%; font-weight: bold; }
        .status-box { margin-top: 20px; padding: 15px; background: #e8f4fd; border-left: 4px solid #1f497d; line-height: 1.6; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
        th, td { border: 1px solid #cbd5e1; padding: 7px; text-align: center; }
        th { background: #1f497d; color: white; }
    </style>
</head>
<body>
<div class="header">
    <div><strong>{{ user['department'] }}</strong> ({{ user['username'] }})</div>
    <div><a href="/logout" style="color: #fde047; text-decoration: none; font-weight: bold;">வெளியேறு</a></div>
</div>

<div class="container">
    <div class="token-alert">
        <strong>உங்கள் Extension Token:</strong> <code style="font-size: 16px; color: #b91c1c; font-weight: bold;">{{ user['api_token'] }}</code>
    </div>

    <form id="uploadForm">
        <label>1. பாடக் குறியீடு (Subject Code - எ.கா: 26UACM13B):</label>
        <input type="text" id="subject_code" placeholder="26UACM13B" required>

        <label>2. எக்செல் கோப்பைத் தேர்ந்தெடுக்கவும் (marks.xlsx):</label>
        <input type="file" id="excel_file" accept=".xlsx, .xls" required>

        <button type="submit">மதிப்பெண்களைப் பதிவேற்றி சரிபார் (Upload & Preview)</button>
    </form>

    <div class="status-box" id="statusBox" style="display:none;"></div>
    <div id="previewArea"></div>
</div>

<script>
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData();
    formData.append('subject_code', document.getElementById('subject_code').value.trim().toUpperCase());
    formData.append('file', document.getElementById('excel_file').files[0]);

    const statusBox = document.getElementById('statusBox');
    statusBox.style.display = 'block';
    statusBox.innerHTML = 'எக்செல் தரவுகள் படிக்கப்படுகின்றன...';

    const res = await fetch('/api/staff/upload', { method: 'POST', body: formData });
    const data = await res.json();

    if (data.success) {
        statusBox.innerHTML = `<strong>தயார்!</strong> பாடம்: <b>${data.subject_code}</b> (ஷீட்: ${data.sheet}) | மொத்த மாணவர்கள்: <b>${data.count}</b>.<br>
        இப்போது TVU போர்ட்டல் பக்கத்தில் Chrome Extension-ஐத் திறந்து <b>"மதிப்பெண்களை நிரப்பு"</b> பட்டனை அழுத்தவும்.`;
        let html = '<table><tr><th>Register No</th><th>Attendance</th><th>Test</th><th>Assignment</th></tr>';
        data.preview.forEach(r => {
            html += `<tr><td>${r.reg}</td><td>${r.att}</td><td>${r.test}</td><td>${r.assgn}</td></tr>`;
        });
        html += '</table>';
        document.getElementById('previewArea').innerHTML = html;
    } else {
        statusBox.innerHTML = `<span style="color:red; font-weight:bold;">பிழை: ${data.error}</span>`;
    }
});
</script>
</body>
</html>"""

# ==============================================================================
# 4. Routes & API
# ==============================================================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        pwd = request.form.get('password', '').strip()

        if uname == SUPER_ADMIN_USER and pwd == SUPER_ADMIN_PASS:
            session['role'] = 'admin'
            return redirect(url_for('admin_panel'))

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (uname,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], pwd):
            if user['is_active'] == 0:
                return render_template_string(LOGIN_HTML, error="உங்கள் கணக்கு நிர்வாகியால் நிறுத்தப்பட்டுள்ளது!")
            session['role'] = 'staff'
            session['user_id'] = user['id']
            return redirect(url_for('staff_dashboard'))
        else:
            return render_template_string(LOGIN_HTML, error="தவறான பயனர் பெயர் அல்லது கடவுச்சொல்!")
    return render_template_string(LOGIN_HTML)

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, users=users)

@app.route('/admin/create_user', methods=['POST'])
def create_user():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    dept = request.form.get('department').strip()
    uname = request.form.get('username').strip()
    pwd = request.form.get('password').strip()
    token = "TVU-" + uuid.uuid4().hex[:8].upper()

    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password_hash, department, api_token, is_active) VALUES (?, ?, ?, ?, 1)",
                     (uname, generate_password_hash(pwd), dept, token))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/toggle_user/<int:user_id>', methods=['POST'])
def toggle_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute("SELECT is_active FROM users WHERE id = ?", (user_id,)).fetchone()
    if user:
        new_status = 0 if user['is_active'] == 1 else 1
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute("DELETE FROM user_marks WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/dashboard')
def staff_dashboard():
    if session.get('role') != 'staff':
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    if not user or user['is_active'] == 0:
        session.clear()
        return redirect(url_for('login'))
    return render_template_string(STAFF_DASHBOARD_HTML, user=user)

@app.route('/api/staff/upload', methods=['POST'])
def staff_upload():
    if session.get('role') != 'staff':
        return jsonify({"success": False, "error": "Unauthorized"})

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    subject_code = request.form.get('subject_code', '').strip().upper()
    file = request.files.get('file')

    try:
        xls = pd.ExcelFile(file)
        target_clean = re.sub(r'[^A-Za-z0-9]', '', subject_code).upper()
        actual_sheet = next((s for s in xls.sheet_names if target_clean in re.sub(r'[^A-Za-z0-9]', '', str(s)).upper()), None)

        if not actual_sheet:
            if len(xls.sheet_names) == 1:
                actual_sheet = xls.sheet_names[0]
            else:
                conn.close()
                return jsonify({"success": False, "error": f"'{subject_code}' என்ற ஷீட் எக்செல்லில் இல்லை. உள்ள ஷீட்கள்: {xls.sheet_names}"})

        df = pd.read_excel(xls, sheet_name=actual_sheet)
        df.columns = [str(c).strip() for c in df.columns]

        reg_col = next((c for c in df.columns if any(k in c.lower().replace(" ", "") for k in ["reg", "roll"])), None)
        if not reg_col:
            conn.close()
            return jsonify({"success": False, "error": "Register Number காலம் எக்செல்லில் இல்லை."})

        df = df.rename(columns={reg_col: 'Register Number'})
        for c in df.columns:
            cl = c.lower().replace(" ", "")
            if any(k in cl for k in ["test", "internal", "cia"]) and "Test Marks" not in df.columns:
                df = df.rename(columns={c: 'Test Marks'})
            elif "attend" in cl and "Attendance Marks" not in df.columns:
                df = df.rename(columns={c: 'Attendance Marks'})
            elif "assign" in cl and "Assignment Marks" not in df.columns:
                df = df.rename(columns={c: 'Assignment Marks'})

        records = []
        for _, r in df.iterrows():
            reg = str(r.get("Register Number", "")).strip().replace(".0", "")
            if reg and reg.lower() != "nan":
                records.append({
                    "reg": reg,
                    "att": str(r.get("Attendance Marks", "")).strip().replace(".0", ""),
                    "test": str(r.get("Test Marks", "")).strip().replace(".0", ""),
                    "assgn": str(r.get("Assignment Marks", "")).strip().replace(".0", "")
                })

        conn.execute("INSERT OR REPLACE INTO user_marks (user_id, subject_code, records_json) VALUES (?, ?, ?)",
                     (user['id'], subject_code, json.dumps(records)))
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "subject_code": subject_code,
            "sheet": actual_sheet,
            "count": len(records),
            "preview": records[:5]
        })
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/extension/get-marks', methods=['GET'])
def extension_get_marks():
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE api_token = ?", (token,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"success": False, "error": "தவறான User Token!"})
    if user['is_active'] == 0:
        conn.close()
        return jsonify({"success": False, "error": "நிர்வாகியால் உங்கள் அனுமதி நிறுத்தப்பட்டுள்ளது!"})

    marks_row = conn.execute("SELECT * FROM user_marks WHERE user_id = ?", (user['id'],)).fetchone()
    conn.close()
    if not marks_row:
        return jsonify({"success": False, "error": "இணையதளத்தில் மதிப்பெண்கள் இன்னும் பதிவேற்றப்படவில்லை!"})

    return jsonify({
        "success": True,
        "department": user['department'],
        "subject_code": marks_row['subject_code'],
        "records": json.loads(marks_row['records_json'])
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)