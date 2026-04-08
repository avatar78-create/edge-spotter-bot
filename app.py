import os
from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    mensaje = (
        f"🚨 *{data.get('status', 'ALERTA')}*\n\n"
        f"📈 *Activo:* {data.get('ticker')}\n"
        f"🏷️ *Precio:* {data.get('price')}\n"
        f"⏰ *Hora:* {data.get('time')}\n"
    )
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
