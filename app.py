import os  # <--- Esta es la pieza que faltaba
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

# Cargamos las credenciales desde Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID") 

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

@app.post("/webhook")
async def handle_webhook(signal: Signal):
    # Validamos la clave secreta
    if signal.secret != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Clave incorrecta")

    # Formateamos el mensaje
    emoji = "🟢" if signal.action == "BUY" else "🔴"
    text = (f"{emoji} *SEÑAL {signal.bot}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Instrumento: `{signal.ticker}`\n"
            f"Acción: *{signal.action}*\n"
            f"Precio: `{signal.price}`\n"
            f"Modo: {signal.mode}\n"
            f"━━━━━━━━━━━━━━━")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # 1. Envío a tu chat personal
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"})
    
    # 2. Envío al Canal de Transmisión (si está configurado)
    if CHANNEL_ID:
        requests.post(url, json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"})

    return {"status": "ok"}
