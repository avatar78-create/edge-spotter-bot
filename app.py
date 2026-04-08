import os
from flask import Flask, request
import requests

app = Flask(__name__)

# Render usa estas variables de entorno que configuraste
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route('/webhook', methods=['POST'])
def webhook():
    # force=True evita el error 'Unsupported Media Type' de TradingView
    data = request.get_json(force=True)
    
    if data:
        # Estructura del mensaje para Telegram
        mensaje = (
            f"🚨 *{data.get('status', 'ALERTA')}*\n\n"
            f"📈 *Activo:* {data.get('ticker')}\n"
            f"🏷️ *Precio:* {data.get('price')}\n"
            f"⏰ *Hora:* {data.get('time')}\n"
        )
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        
        try:
            # Enviamos a Telegram con un timeout corto
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")
            
    # Respondemos "OK" de inmediato para que TradingView no de Timeout
    return "OK", 200

if __name__ == "__main__":
    # Render asigna el puerto dinámicamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
