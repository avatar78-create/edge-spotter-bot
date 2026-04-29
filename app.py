import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# ============================================================
# CREDENCIALES — variables de entorno en Render
# ============================================================
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SECRET_TOKEN     = os.getenv("SECRET_TOKEN")
CHANNEL_ID       = os.getenv("CHANNEL_ID")

# ============================================================
# SCHEMA v7.2.2 — sincronizado con E-Spotter AIMFX
# Campos nuevos:  instrument | author | entry | tp | sl | er | atr_ratio | disclaimer
# Campo removido: price (reemplazado por entry)
# Campos Optional: compatibilidad con alertas legacy si las hay
# ============================================================
class Signal(BaseModel):
    bot:          str
    ticker:       str
    action:       str
    signal_type:  str
    mode:         str
    entry:        float
    tp:           float
    sl:           float
    rsi:          float
    bar_time:     int
    secret:       str
    instrument:   Optional[str]   = None
    author:       Optional[str]   = None
    er:           Optional[float] = None
    atr_ratio:    Optional[float] = None
    disclaimer:   Optional[str]   = None
    price:        Optional[float] = None  # legacy — mantener por si llega alguna alerta vieja

# ============================================================
# HEALTHCHECK
# ============================================================
@app.get("/")
async def root():
    return {"status": "E-Spotter AIMFX Webhook — Activo", "version": "7.2.2"}

# ============================================================
# WEBHOOK PRINCIPAL
# ============================================================
@app.post("/webhook")
async def handle_webhook(signal: Signal):

    # Validacion de clave secreta
    if signal.secret != SECRET_TOKEN:
        print(f"[ERROR] Secret incorrecto. Recibido: {signal.secret}")
        raise HTTPException(status_code=403, detail="Clave incorrecta")

    # Emoji y etiqueta por tipo de senal
    if signal.signal_type == "PANIC_BUY":
        emoji  = "⚡🟢"
        s_label = "PANICO COMPRA"
    elif signal.signal_type == "PANIC_SELL":
        emoji  = "⚡🔴"
        s_label = "PANICO VENTA"
    elif signal.action == "BUY":
        emoji  = "🟢"
        s_label = "LONG"
    else:
        emoji  = "🔴"
        s_label = "SHORT"

    # Nombre del instrumento — usa description si viene, si no usa ticker
    instrument_name = signal.instrument if signal.instrument else signal.ticker

    # Calculo de distancias para contexto
    sl_pips = round(abs(signal.entry - signal.sl), 2)
    tp_pips = round(abs(signal.tp   - signal.entry), 2)
    rr      = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0

    # Formato del mensaje Telegram
    text = (
        f"{emoji} *{s_label} — {instrument_name}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 Entry:  `{signal.entry}`\n"
        f"✅ TP:     `{signal.tp}`\n"
        f"🛑 SL:     `{signal.sl}`\n"
        f"📐 R:R:    `{rr}:1`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Modo:      {signal.mode}\n"
        f"RSI:       `{signal.rsi}`\n"
    )

    # ER y ATR Ratio si vienen (opcionales)
    if signal.er is not None:
        text += f"ER:        `{signal.er}`\n"
    if signal.atr_ratio is not None:
        text += f"ATR Ratio: `{signal.atr_ratio}x`\n"

    text += (
        f"━━━━━━━━━━━━━━━\n"
        f"_{signal.disclaimer if signal.disclaimer else 'Una senal no es una orden, es una oportunidad a validar.'}_\n"
        f"— *E\\-Spotter | AIMFX | HemepinCrawlerFX* —"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # Envio a chat personal
    resp_personal = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    )
    print(f"[LOG Personal] Status {resp_personal.status_code} — {resp_personal.text}")

    # Envio al canal (si esta configurado)
    if CHANNEL_ID:
        resp_canal = requests.post(
            url,
            json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
        )
        print(f"[LOG Canal] Status {resp_canal.status_code} — {resp_canal.text}")

    return {"status": "ok", "telegram_status": resp_personal.status_code}
