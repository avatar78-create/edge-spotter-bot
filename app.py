import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 1. Definimos la aplicación (la pieza que faltaba)
app = FastAPI()

# 2. Cargamos las credenciales desde Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# 3. Estructura de los datos que vienen de TradingView
class Signal(BaseModel):
    bot: str
    ticker: str
    action: str
    signal_type: str
    mode: str
    price: float
    rsi: float
    bar_time: int
    secret: str

@app.get("/")
async def root():
    return {"status": "Servidor de Alejandro Activo"}

@app.post("/webhook")
async def handle_webhook(signal: Signal):
    # Validamos la clave secreta
    if signal.secret != SECRET_TOKEN:
        print(f"ERROR: Clave secreta incorrecta. Recibido: {signal.secret}")
        raise HTTPException(status_code=403, detail="Clave incorrecta")

    # Formateamos el mensaje para Telegram
    emoji = "🟢" if signal.action == "BUY" else "🔴"
    text = (f"{emoji} *SEÑAL {signal.bot}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Instrumento: `{signal.ticker}`\n"
            f"Acción: *{signal.action}*\n"
            f"Precio: `{signal.price}`\n"
            f"Modo: {signal.mode}\n"
            f"━━━━━━━━━━━━━━━")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # 4. Envío a tu chat personal y LOG de respuesta
    resp_personal = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"})
    print(f"LOG Personal: Status {resp_personal.status_code} - {resp_personal.text}")
    
    # 5. Envío al Canal de Transmisión y LOG de respuesta
    if CHANNEL_ID:
        resp_canal = requests.post(url, json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"})
        print(f"LOG Canal: Status {resp_canal.status_code} - {resp_canal.text}")

    return {"status": "ok", "personal_resp": resp_personal.status_code}
