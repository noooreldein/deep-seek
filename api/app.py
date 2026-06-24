import requests
import json
import random
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

API_URL = "https://api-preview.chatgot.io/api/v1/char-gpt/conversations"
SESSIONS = {}  # تخزين مؤقت للذاكرة (في Vercel سيكون لكل طلب مساحة منفصلة، لكن للاستخدام البسيط يعمل)

MY_OWNER = "@n_7_3_a"
MY_CHANNEL = "https://t.me/n_7_3_a_2"
MY_NAME = "Noor"

def get_headers():
    browsers = [
        ('"Chromium";v="122", "Google Chrome";v="122"', '"Windows"', "?0", 
         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"),
        ('"Chromium";v="120", "Google Chrome";v="120"', '"macOS"', "?0", 
         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"),
        ('"Google Chrome";v="121", "Chromium";v="121"', '"Android"', "?1", 
         "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 Chrome/121.0.0.0 Mobile Safari/537.36")
    ]
    ch, plat, mob, ua = random.choice(browsers)
    return {
        'User-Agent': ua,
        'Accept': "text/event-stream",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': plat,
        'sec-ch-ua': ch,
        'sec-ch-ua-mobile': mob,
        'origin': "https://deepseekfree.ai",
        'referer': "https://deepseekfree.ai/",
        'accept-language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7"
    }

@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "api": "DeepSeek Free by Noor",
        "usage": "/chat?q=سؤالك",
        "optional": "أضف &session_id=xxx للذاكرة",
        "owner": MY_OWNER,
        "channel": MY_CHANNEL,
        "developer": MY_NAME
    })

@app.route("/chat", methods=["GET"])
def chat():
    question = request.args.get("q", "") or request.args.get("text", "")
    session_id = request.args.get("session_id", str(uuid.uuid4())[:8])

    if not question:
        return jsonify({"status": "error", "message": "استخدم ?q=سؤالك"}), 400

    # استرجاع أو إنشاء جلسة
    if session_id not in SESSIONS:
        SESSIONS[session_id] = []

    memory = SESSIONS[session_id]
    memory.append({"role": "user", "content": question})

    payload = {
        "device_id": uuid.uuid4().hex,
        "model_id": 1,
        "include_reasoning": True,
        "messages": memory
    }

    try:
        res = requests.post(API_URL, json=payload, headers=get_headers(), stream=True, timeout=30)
        if res.status_code != 200:
            return jsonify({"status": "error", "message": f"خطأ من الخادم: {res.status_code}"}), 500

        full_response = ""
        reasoning = ""
        for line in res.iter_lines():
            if line and line.decode('utf-8').startswith("data: "):
                data = line.decode('utf-8')[6:]
                if data == "[DONE]":
                    break
                try:
                    d = json.loads(data).get("data", {})
                    if isinstance(d, dict):
                        r = d.get("reasoning_content")
                        c = d.get("content")
                        if r:
                            reasoning += r
                        if c:
                            full_response += c
                except:
                    pass

        if not full_response:
            return jsonify({"status": "error", "message": "لم يتم استلام رد"}), 500

        memory.append({"role": "assistant", "content": full_response})
        SESSIONS[session_id] = memory

        return jsonify({
            "status": "success",
            "reply": full_response,
            "reasoning": reasoning if reasoning else None,
            "session_id": session_id,
            "owner": MY_OWNER,
            "channel": MY_CHANNEL,
            "developer": MY_NAME
        })

    except Exception as e:
        if memory and memory[-1]["role"] == "user":
            memory.pop()
        return jsonify({"status": "error", "message": f"فشل الاتصال: {str(e)}"}), 500
