import os
import requests
from flask import Flask, request
from datetime import datetime
import pytz

app = Flask(__name__)

# Configuración de Telegram (Cargada desde variables de entorno de Render)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

@app.route('/webhook', methods=['POST'])
def webhook():
    # force=True asegura que procese el JSON aunque el header sea distinto
    data = request.get_json(force=True)
    
    if data:
        # 1. Lógica de Bias (Sentido de la operación)
        status = data.get('status', '').upper()
        if "BUY" in status or "COMPRA" in status:
            bias_header = "🟢 ORDEN DE COMPRA"
        elif "SELL" in status or "VENTA" in status:
            bias_header = "🔴 ORDEN DE VENTA"
        else:
            bias_header = f"🔵 ALERTA: {status}"

        # 2. Gestión de la Hora (Zona Horaria Argentina UTC-3)
        try:
            arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')
            dt_arg = datetime.now(arg_tz)
            hora_local = dt_arg.strftime("%H:%M:%S")
        except Exception:
            hora_local = data.get('time', 'N/A')

        # 3. Construcción del Mensaje Estético
        mensaje = (
            f"**{bias_header}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📈 **Activo:** {data.get('ticker')}\n"
            f"🏷️ **Precio:** {data.get('price')}\n"
            f"⏰ **Hora:** {hora_local} (Arg)"
        )

        # 4. Envío a Telegram
        payload = {
            "chat_id": CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        
        try:
            requests.post(url, json=payload, timeout=5)
        except requests.exceptions.RequestException as e:
            print(f"Error enviando a Telegram: {e}")

    return "OK", 200

if __name__ == '__main__':
    # Render usa la variable PORT, por defecto 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
