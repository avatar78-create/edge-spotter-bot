import os
from flask import Flask, request
import requests
from datetime import datetime
import pytz

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    
    if data:
        # Ajuste de hora: Convertimos UTC a horario de Argentina (UTC-3)
        try:
            hora_utc = data.get('time') # Recibe 2026-04-08T12:48:00Z
            dt_utc = datetime.strptime(hora_utc, "%Y-%m-%dT%H:%M:%SZ")
            dt_utc = pytz.utc.localize(dt_utc)
            
            # Cambiamos a zona horaria de Argentina
            tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
            dt_arg = dt_utc.astimezone(tz_arg)
            hora_formateada = dt_arg.strftime("%H:%M:%S") # Muestra solo HH:MM:SS
            fecha_formateada = dt_arg.strftime("%d/%m/%Y") # Muestra DD/MM/AAAA
        except:
            hora_formateada = data.get('time')
            fecha_formateada = ""

        mensaje = (
            f"🚨 *{data.get('status', 'ALERTA')}*\n\n"
            f"📈 *Activo:* {data.get('ticker')}\n"
            f"🏷️ *Precio:* {data.get('price')}\n"
            f"📅 *Fecha:* {fecha_formateada}\n"
            f"⏰ *Hora:* {hora_formateada} (Arg)\n"
        )
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error: {e}")
            
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
