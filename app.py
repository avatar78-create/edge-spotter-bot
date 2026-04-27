import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# ============================================================
# CREDENCIALES — vienen de variables de entorno en Render
# ============================================================
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SECRET_TOKEN    = os.getenv("SECRET_TOKEN")
CHANNEL_ID      = os.getenv("CHANNEL_ID")

# ============================================================
# SCHEMA — debe coincidir exactamente con el JSON del Pine Script
# ============================================================
class Signal(BaseModel):
    bot:         str
    ticker:      str
    action:      str
    signal_type: str
    mode:        str
    price:       float
    rsi:         float
    bar_time:    int
    secret:      str

# ============================================================
# HEALTHCHECK
# ============================================================
@app.get("/")
async def root():
    return {"status": "Edge Spotter Webhook — Activo"}

# ============================================================
# WEBHOOK PRINCIPAL
# ============================================================
@app.post("/webhook")
async def handle_webhook(signal: Signal):

    # Validación de clave secreta
    if signal.secret != SECRET_TOKEN:
        print(f"[ERROR] Secret incorrecto. Recibido: {signal.secret}")
        raise HTTPException(status_code=403, detail="Clave incorrecta")

    # Formato del mensaje Telegram
    emoji = "🟢" if signal.action == "BUY" else "🔴"
    text = (
        f"{emoji} *SEÑAL {signal.bot}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Instrumento: `{signal.ticker}`\n"
        f"Acción: *{signal.action}*\n"
        f"Tipo: {signal.signal_type}\n"
        f"Modo: {signal.mode}\n"
        f"Precio: `{signal.price}`\n"
        f"RSI: `{signal.rsi}`\n"
        f"━━━━━━━━━━━━━━━"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # Envío a chat personal
    resp_personal = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    )
    print(f"[LOG Personal] Status {resp_personal.status_code} — {resp_personal.text}")

    # Envío al canal (si está configurado)
    if CHANNEL_ID:
        resp_canal = requests.post(
            url,
            json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
        )
        print(f"[LOG Canal] Status {resp_canal.status_code} — {resp_canal.text}")

    return {"status": "ok", "telegram_status": resp_personal.status_code}
