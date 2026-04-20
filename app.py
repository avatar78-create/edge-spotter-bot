from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# Tus llaves que ya configuraste en la pestaña Environment de Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

class Signal(BaseModel):
    bot: str
    ticker: str
    action: str
    signal_type: str
    mode: str
    price: float
    rsi: float
    bar_time: int
    secret: str  # <-- La llave ahora viaja aquí adentro

@app.post("/webhook")
async def handle_webhook(signal: Signal):
    # Validamos que la clave coincida
    if signal.secret != SECRET_TOKEN:
        print(f"Intento de acceso fallido con clave: {signal.secret}")
        raise HTTPException(status_code=403, detail="Clave incorrecta")

    # Formateamos el mensaje para que se vea profesional en Telegram
    emoji = "🟢" if signal.action == "BUY" else "🔴"
    text = (f"{emoji} *SEÑAL {signal.bot}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Instrumento: `{signal.ticker}`\n"
            f"Acción: *{signal.action}*\n"
            f"Precio: `{signal.price}`\n"
            f"RSI: {signal.rsi}\n"
            f"━━━━━━━━━━━━━━━")

    # Envío a Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

    return {"status": "ok"}
