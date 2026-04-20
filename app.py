@app.post("/webhook")
async def handle_webhook(signal: Signal):
    if signal.secret != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Clave incorrecta")

    emoji = "🟢" if signal.action == "BUY" else "🔴"
    text = (f"{emoji} *SEÑAL {signal.bot}*\n"
            f"Instrumento: `{signal.ticker}`\n"
            f"Precio: `{signal.price}`")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Intentamos enviar a tu chat personal
    resp_personal = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"})
    print(f"Respuesta Telegram Personal: {resp_personal.status_code} - {resp_personal.text}")

    # Intentamos enviar al canal
    if CHANNEL_ID:
        resp_canal = requests.post(url, json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"})
        print(f"Respuesta Telegram Canal: {resp_canal.status_code} - {resp_canal.text}")

    return {"status": "ok"}
