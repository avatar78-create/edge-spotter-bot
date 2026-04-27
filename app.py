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


# ╔══════════════════════════════════════════════════════════════╗
# ║  BLOQUE DE PRUEBA — BORRAR ANTES DE PRODUCCIÓN FINAL        ║
# ║  Endpoint: GET /test                                        ║
# ║  Simula una señal LONG real y la manda a Telegram           ║
# ║  Uso: abrí https://TU-APP.onrender.com/test en el browser   ║
# ╚══════════════════════════════════════════════════════════════╝
@app.get("/test")
async def test_webhook():

    # Payload de prueba — replica exactamente lo que manda TradingView
    fake_signal = Signal(
        bot         = "Edge Spotter v7.2",
        ticker      = "XAUUSD",
        action      = "BUY",
        signal_type = "LONG",
        mode        = "Confirmado",
        price       = 4703.265,
        rsi         = 45.23,
        bar_time    = 1745000000,
        secret      = SECRET_TOKEN  # usa el mismo secret de Render
    )

    # Reutiliza la lógica del webhook real
    result = await handle_webhook(fake_signal)

    return {
        "test": "completado",
        "payload_enviado": fake_signal.dict(),
        "resultado": result
    }
# ╔══════════════════════════════════════════════════════════════╗
# ║  FIN BLOQUE DE PRUEBA                                       ║
# ╚══════════════════════════════════════════════════════════════╝
