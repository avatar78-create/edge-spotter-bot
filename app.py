# ... (todo lo anterior igual) ...

# 1. Definimos el ID del canal (lo cargamos desde Render)
CHANNEL_ID = os.getenv("CHANNEL_ID") 

@app.post("/webhook")
async def handle_webhook(signal: Signal):
    if signal.secret != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Clave incorrecta")

    emoji = "🟢" if signal.action == "BUY" else "🔴"
    text = (f"{emoji} *SEÑAL {signal.bot}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Instrumento: `{signal.ticker}`\n"
            f"Acción: *{signal.action}*\n"
            f"Precio: `{signal.price}`\n"
            f"Modo: {signal.mode}\n"
            f"━━━━━━━━━━━━━━━")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # ENVÍO 1: A tu chat personal (el que ya funciona)
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"})
    
    # ENVÍO 2: Al canal de transmisión
    if CHANNEL_ID:
        requests.post(url, json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"})

    return {"status": "ok"}
