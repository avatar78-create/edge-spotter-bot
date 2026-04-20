from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import requests  # <-- Agregamos esta que es la que te pide el error
import os

app = FastAPI()

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

@app.post("/webhook")
async def handle_webhook(signal: Signal, x_tv_token: str = Header(None)):
    if x_tv_token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado")

    emoji = "🟢" if signal.action == "BUY" else "🔴"
    text = (f"{emoji} *SEÑAL {signal.bot}*\n"
            f"Instrumento: {signal.ticker}\n"
            f"Tipo: {signal.signal_type}\n"
            f"Precio: {signal.price}")

    # Usamos requests para enviar el mensaje
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"})

    return {"status": "ok"}
