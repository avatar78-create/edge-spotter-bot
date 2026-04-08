import os
from flask import Flask, request
import requests

app = Flask(__name__)

# Render usa variables de entorno
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route('/webhook', methods=['POST'])
def webhook():
    # Obtenemos los datos inmediatamente
    data = request.get_json(force=True)
    
    if data:
        # Formato de mensaje para el canal
        mensaje = (
            f"🚨 *{data.get('status', 'ALERTA')}*\n\n"
            f"📈 *Activo:* {data.get('ticker')}\n"
            f"🏷️ *Precio:* {data.get('price')}\n"
            f"⏰ *Hora:* {data.get('time')}\n"
        )
        
        # Enviamos a Telegram
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        
        try:
            # Enviamos la notificación
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")
            
    # Respondemos "OK" rápido para que TradingView no corte la conexión
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
