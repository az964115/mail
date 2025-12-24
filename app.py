from flask import Flask, request, render_template
import requests
import sqlite3
import datetime
import smtplib
from email.message import EmailMessage
import threading
from config import SPAM_BASE_URL, ADMIN_EMAIL, REPORT_EMAIL, SMTP_HOST, SMTP_PORT, SMTP_SENDER

app = Flask(__name__)
DB_PATH = "release.db"

# ---------- 初始化 DB ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS release_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            rcpt TEXT,
            ip TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- 發送放行通知 ----------
def send_notify(key, rcpt, ip):
    msg = EmailMessage()
    msg["Subject"] = f"隔離郵件放行通知: {rcpt}"
    msg["From"] = SMTP_SENDER
    msg["To"] = ADMIN_EMAIL
    msg.set_content(f"""
郵件收件人: {rcpt}
KEY: {key}
放行 IP: {ip}
時間: {datetime.datetime.now().isoformat()}
""")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.send_message(msg)
    except Exception as e:
        print("[WARN] 發送通知信失敗:", e)

# ---------- 發送每日放行紀錄報告 ----------
def send_daily_report():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    c.execute("SELECT key, rcpt, ip, time FROM release_log WHERE time>=?", (yesterday.isoformat(),))
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("[INFO] 今天沒有放行紀錄，不寄送報告")
        return

    content = "最近 24 小時放行紀錄:\n\nKEY\tRCPT\tIP\tTIME\n"
    content += "\n".join(["\t".join(row) for row in rows])

    msg = EmailMessage()
    msg["Subject"] = "隔離郵件放行紀錄報告"
    msg["From"] = SMTP_SENDER
    msg["To"] = REPORT_EMAIL
    msg.set_content(content)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.send_message(msg)
        print("[INFO] 放行紀錄報告已寄送")
    except Exception as e:
        print("[WARN] 發送報告信失敗:", e)

# ---------- 定時排程，每天 09:00 寄報告 ----------
def schedule_report_thread():
    import schedule, time
    schedule.every().day.at("09:00").do(send_daily_report)
    while True:
        schedule.run_pending()
        time.sleep(30)

t = threading.Thread(target=schedule_report_thread)
t.daemon = True
t.start()

# ---------- 首頁，使用者輸入 KEY + RCPT ----------
@app.route("/")
def index():
    return render_template("index.html")

# ---------- 執行放行 ----------
@app.route("/api/release", methods=["POST"])
def do_release():
    key = request.form.get("KEY")
    rcpt = request.form.get("RCPT")
    ip = request.remote_addr

    if not key or not rcpt:
        return {"success": False, "message": "參數錯誤"}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 檢查同一 KEY 一小時內是否已放行
    c.execute("SELECT time FROM release_log WHERE key=? ORDER BY time DESC LIMIT 1", (key,))
    row = c.fetchone()
    if row:
        last_time = datetime.datetime.fromisoformat(row[0])
        if (datetime.datetime.now() - last_time).total_seconds() < 9999999999:
            conn.close()
            return {"success": False, "message": "⚠️ 此隔離郵件已放行過，只能放行一次"}

    # 放行到隔離系統
    params = {"KEY": key, "RCPT": rcpt, "s[1]": 1, "resend": 1}
    try:
        r = requests.get(SPAM_BASE_URL, params=params, verify=False, timeout=10)
        if r.status_code != 200:
            return {"success": False, "message": "放行失敗"}
    except Exception as e:
        return {"success": False, "message": f"放行系統連線失敗: {e}"}

    # 紀錄 DB
    c.execute("INSERT INTO release_log (key, rcpt, ip, time) VALUES (?, ?, ?, ?)",
              (key, rcpt, ip, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

    # 發送即時通知
    send_notify(key, rcpt, ip)

    return {"success": True, "message": "✅ 放行完成"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
