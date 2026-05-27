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
# SCHEMA v7.3.2 — sincronizado con E-Spotter AIMFX
# ============================================================
class Signal(BaseModel):
    # --- Core (obligatorios) ---
    bot:          str
    ticker:       str
    action:       str
    signal_type:  str
    mode:         str
    entry:        float
    sl:           float
    bar_time:     int
    secret:       str

    # --- Core (opcionales por compatibilidad) ---
    instrument:   Optional[str]   = None
    author:       Optional[str]   = None
    disclaimer:   Optional[str]   = None

    # --- Precio al momento de la alerta ---
    price:        Optional[float] = None

    # --- TP: E-Spotter usa tp, Luna usa tp1/tp2 ---
    tp:           Optional[float] = None
    tp1:          Optional[float] = None
    tp2:          Optional[float] = None

    # --- R:R: E-Spotter lo calcula el webhook, Luna lo envia ---
    rr1:          Optional[float] = None
    rr2:          Optional[float] = None

    # --- Filtros originales ---
    rsi:          Optional[float] = None
    er:           Optional[float] = None
    atr_ratio:    Optional[float] = None

    # --- Campos nuevos v7.3.2 ---
    efi_val:      Optional[float] = None
    efi_dir:      Optional[str]   = None   # BULLISH | BEARISH | NEUTRAL
    htf_bias:     Optional[str]   = None   # BULL | BEAR
    htf_long:     Optional[bool]  = None
    htf_short:    Optional[bool]  = None
    regime:       Optional[str]   = None   # NORMAL | BULL | BEAR | VOLATIL

    # --- Identificador de modulo ---
    module:       Optional[str]   = None   # None = E-Spotter core | "Luna Scalper v1.2"

# ============================================================
# HELPERS
# ============================================================
def checkmark(val: Optional[bool]) -> str:
    if val is True:
        return "✅"
    if val is False:
        return "❌"
    return "—"

def regime_emoji(regime: Optional[str]) -> str:
    if regime == "BULL":    return "🐂"
    if regime == "BEAR":    return "🐻"
    if regime == "VOLATIL": return "⚡"
    return "〰️"   # NORMAL

def efi_emoji(efi_dir: Optional[str]) -> str:
    if efi_dir == "BULLISH": return "🟢"
    if efi_dir == "BEARISH": return "🔴"
    return "⚪"

# ============================================================
# HEALTHCHECK
# ============================================================
@app.get("/")
async def root():
    return {"status": "E-Spotter AIMFX Webhook — Active", "version": "7.3.2"}

# ============================================================
# WEBHOOK PRINCIPAL
# ============================================================
@app.post("/webhook")
async def handle_webhook(signal: Signal):

    # --- Validacion de clave secreta ---
    if signal.secret != SECRET_TOKEN:
        print(f"[ERROR] Wrong secret. Received: {signal.secret}")
        raise HTTPException(status_code=403, detail="Invalid key")

    is_luna = signal.module is not None

    # --- Emoji y etiqueta por tipo de senal ---
    if signal.signal_type == "PANIC_BUY":
        emoji   = "⚡🟢"
        s_label = "PANIC BUY"
    elif signal.signal_type == "PANIC_SELL":
        emoji   = "⚡🔴"
        s_label = "PANIC SELL"
    elif signal.signal_type == "LUNA_LONG":
        emoji   = "🌙🟢"
        s_label = "LUNA LONG"
    elif signal.signal_type == "LUNA_SHORT":
        emoji   = "🌙🔴"
        s_label = "LUNA SHORT"
    elif signal.action == "BUY":
        emoji   = "🟢"
        s_label = "LONG"
    else:
        emoji   = "🔴"
        s_label = "SHORT"

    # --- Modo ---
    mode_display = "Aggressive" if signal.mode.lower() in ["agresivo", "aggressive"] else signal.mode

    # --- Nombre del instrumento ---
    instrument_name = signal.instrument if signal.instrument else signal.ticker

    # ============================================================
    # BLOQUE DE PRECIO
    # ============================================================
    price_line = ""
    if signal.price is not None:
        price_line = f"💰 Price:     `{signal.price}`\n"

    # ============================================================
    # BLOQUE TP / SL / R:R
    # ============================================================
    if is_luna:
        # Luna envia tp1/tp2 y rr1/rr2 calculados
        tp_block = ""
        if signal.tp1 is not None:
            tp_block += f"✅ TP1:       `{signal.tp1}`\n"
        if signal.tp2 is not None:
            tp_block += f"✅ TP2:       `{signal.tp2}`\n"
        tp_block += f"🛑 SL:        `{signal.sl}`\n"
        if signal.rr1 is not None:
            tp_block += f"📐 R:R 1:     `{signal.rr1}:1`\n"
        if signal.rr2 is not None:
            tp_block += f"📐 R:R 2:     `{signal.rr2}:1`\n"
    else:
        # E-Spotter core: calcula rr en el webhook
        sl_pips = round(abs(signal.entry - signal.sl), 5)
        tp_pips = round(abs(signal.tp - signal.entry), 5) if signal.tp else 0
        rr      = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0
        tp_block = (
            f"✅ TP:        `{signal.tp}`\n"
            f"🛑 SL:        `{signal.sl}`\n"
            f"📐 R:R:       `{rr}:1`\n"
        )

    # ============================================================
    # BLOQUE DE REGIMEN / FILTROS
    # ============================================================
    regime_line = ""
    if signal.regime is not None:
        r_emoji = regime_emoji(signal.regime)
        regime_line = f"Regime:    {r_emoji} `{signal.regime}`\n"

    htf_line = ""
    if signal.htf_bias is not None:
        long_ck  = checkmark(signal.htf_long)
        short_ck = checkmark(signal.htf_short)
        htf_line = f"HTF 15M:   `{signal.htf_bias}`  L{long_ck} S{short_ck}\n"

    efi_line = ""
    if signal.efi_val is not None and signal.efi_dir is not None:
        e_emoji = efi_emoji(signal.efi_dir)
        efi_line = f"EFI:       {e_emoji} `{signal.efi_val}` ({signal.efi_dir})\n"

    er_line = ""
    if signal.er is not None:
        er_line = f"ER:        `{signal.er}`\n"

    atr_line = ""
    if signal.atr_ratio is not None:
        atr_line = f"ATR Ratio: `{signal.atr_ratio}x`\n"

    rsi_line = ""
    if signal.rsi is not None:
        rsi_line = f"RSI:       `{signal.rsi}`\n"

    # ============================================================
    # CABECERA DE MODULO
    # ============================================================
    module_header = ""
    if is_luna:
        module_header = f"┌ _{signal.module}_\n"

    # ============================================================
    # MENSAJE FINAL
    # ============================================================
    text = (
        f"{emoji} *{s_label} — {instrument_name}*\n"
        f"{module_header}"
        f"━━━━━━━━━━━━━━━\n"
        f"{price_line}"
        f"🎯 Entry:     `{signal.entry}`\n"
        f"{tp_block}"
        f"━━━━━━━━━━━━━━━\n"
        f"Mode:      {mode_display}\n"
        f"{regime_line}"
        f"{htf_line}"
        f"{efi_line}"
        f"{rsi_line}"
        f"{er_line}"
        f"{atr_line}"
        f"━━━━━━━━━━━━━━━\n"
        f"_A signal is not an order — it's an opportunity to validate\\._\n"
        f"— *E\\-Spotter | AIMFXTOOLS* —"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # --- Envio a chat personal ---
    resp_personal = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    )
    print(f"[LOG Personal] Status {resp_personal.status_code} — {resp_personal.text}")

    # --- Envio al canal ---
    if CHANNEL_ID:
        resp_canal = requests.post(
            url,
            json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
        )
        print(f"[LOG Canal] Status {resp_canal.status_code} — {resp_canal.text}")

    return {"status": "ok", "signal_type": signal.signal_type, "module": signal.module, "telegram_status": resp_personal.status_code}
