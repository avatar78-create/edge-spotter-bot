import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

# ============================================================
# CREDENCIALES — variables de entorno en Render
# ============================================================
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SECRET_TOKEN     = os.getenv("SECRET_TOKEN")
CHANNEL_ID       = os.getenv("CHANNEL_ID")

# ============================================================
# ZONA HORARIA ARGENTINA (UTC-3)
# ============================================================
AR_TZ = timezone(timedelta(hours=-3))

# ============================================================
# ACUMULADOR DE SENALES DEL DIA
# ============================================================
daily_signals = []

# ============================================================
# SCHEMA v7.3.2
# ============================================================
class Signal(BaseModel):
    bot:          str
    ticker:       str
    action:       str
    signal_type:  str
    mode:         str
    entry:        float
    sl:           float
    bar_time:     int
    secret:       str
    instrument:   Optional[str]   = None
    author:       Optional[str]   = None
    disclaimer:   Optional[str]   = None
    price:        Optional[float] = None
    tp:           Optional[float] = None
    tp1:          Optional[float] = None
    tp2:          Optional[float] = None
    rr1:          Optional[float] = None
    rr2:          Optional[float] = None
    rsi:          Optional[float] = None
    er:           Optional[float] = None
    atr_ratio:    Optional[float] = None
    efi_val:      Optional[float] = None
    efi_dir:      Optional[str]   = None
    htf_bias:     Optional[str]   = None
    htf_long:     Optional[bool]  = None
    htf_short:    Optional[bool]  = None
    regime:       Optional[str]   = None
    module:       Optional[str]   = None

# ============================================================
# HELPERS
# ============================================================
def checkmark(val: Optional[bool]) -> str:
    if val is True:  return "V"
    if val is False: return "X"
    return "-"

def regime_label(regime: Optional[str]) -> str:
    if regime == "BULL":    return "BULL"
    if regime == "BEAR":    return "BEAR"
    if regime == "VOLATIL": return "VOLATIL"
    return "NORMAL"

def efi_label(efi_dir: Optional[str]) -> str:
    if efi_dir == "BULLISH": return "[+]"
    if efi_dir == "BEARISH": return "[-]"
    return "[~]"

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if TELEGRAM_CHAT_ID:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
        print(f"[LOG Personal] {r.status_code} - {r.text}")
    if CHANNEL_ID:
        r = requests.post(url, json={"chat_id": CHANNEL_ID, "text": text})
        print(f"[LOG Canal] {r.status_code} - {r.text}")

# ============================================================
# GENERADOR DE INFORME DIARIO
# ============================================================
def generate_daily_report():
    global daily_signals

    now_ar = datetime.now(AR_TZ)
    date_str = now_ar.strftime("%d %b %Y")

    if not daily_signals:
        msg = (
            f"DAILY REPORT - {date_str}\n"
            f"-- E-Spotter | AIMFXTOOLS --\n"
            f"---------------\n"
            f"[ES] Sin senales registradas en la sesion anterior.\n"
            f"[EN] No signals recorded in the previous session.\n"
            f"---------------\n"
            f"Precision over Frequency.\n"
            f"-- E-Spotter | AIMFXTOOLS --"
        )
        send_telegram(msg)
        daily_signals = []
        return

    # --- Conteo por instrumento ---
    instruments = {}
    regimes     = []
    long_count  = 0
    short_count = 0
    panic_count = 0

    signal_lines = ""
    for s in daily_signals:
        inst = s.get("instrument") or s.get("ticker", "?")
        stype = s.get("signal_type", "?")
        entry = s.get("entry", "-")
        tp    = s.get("tp") or s.get("tp1") or "-"
        sl    = s.get("sl", "-")
        reg   = s.get("regime", "NORMAL")
        htf   = s.get("htf_bias", "-")
        efi   = s.get("efi_dir", "-")

        instruments[inst] = instruments.get(inst, 0) + 1
        if reg: regimes.append(reg)
        if "LONG" in stype:  long_count  += 1
        if "SHORT" in stype: short_count += 1
        if "PANIC" in stype: panic_count += 1

        # Calculo RR
        try:
            sl_dist = abs(float(entry) - float(sl))
            tp_dist = abs(float(tp)    - float(entry)) if tp != "-" else 0
            rr = round(tp_dist / sl_dist, 2) if sl_dist > 0 else "-"
        except:
            rr = "-"

        signal_lines += (
            f"  {stype} | {inst}\n"
            f"  Entry:{entry}  TP:{tp}  SL:{sl}  RR:{rr}:1\n"
            f"  Regime:{reg}  HTF:{htf}  EFI:{efi}\n"
            f"\n"
        )

    # --- Regimen predominante ---
    regime_predominant = max(set(regimes), key=regimes.count) if regimes else "NORMAL"

    # --- Lectura ES ---
    total = len(daily_signals)
    bias_es = "alcista" if long_count > short_count else "bajista" if short_count > long_count else "neutral"
    bias_en = "bullish"  if long_count > short_count else "bearish"  if short_count > long_count else "neutral"

    inst_summary = ", ".join([f"{k}({v})" for k, v in instruments.items()])

    report = (
        f"DAILY REPORT - {date_str}\n"
        f"-- E-Spotter | AIMFXTOOLS --\n"
        f"===============\n"
        f"Instrumentos: {inst_summary}\n"
        f"Total senales: {total}  |  L:{long_count}  S:{short_count}  P:{panic_count}\n"
        f"Regimen predominante: {regime_predominant}\n"
        f"===============\n"
        f"SENALES:\n"
        f"{signal_lines}"
        f"===============\n"
        f"[ES] La sesion mostro un sesgo {bias_es} con {total} senal(es) activa(s). "
        f"Regimen {regime_predominant}. Precision sobre frecuencia.\n"
        f"\n"
        f"[EN] Session showed a {bias_en} bias with {total} active signal(s). "
        f"Regime: {regime_predominant}. Precision over frequency.\n"
        f"===============\n"
        f"A signal is not an order - it's an opportunity to validate.\n"
        f"-- E-Spotter | AIMFXTOOLS --"
    )

    send_telegram(report)
    daily_signals = []
    print(f"[REPORT] Daily report sent. Signals processed: {total}")

# ============================================================
# SCHEDULER — 9am Argentina = 12:00 UTC
# ============================================================
scheduler = BackgroundScheduler()
scheduler.add_job(generate_daily_report, "cron", hour=12, minute=0, timezone="UTC")
scheduler.start()

# ============================================================
# HEALTHCHECK
# ============================================================
@app.get("/")
async def root():
    return {"status": "E-Spotter AIMFX Webhook — Active", "version": "7.3.2"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok"}
# ============================================================
# ENDPOINT MANUAL (para testear el informe sin esperar las 9am)
# ============================================================
@app.get("/daily-report")
async def trigger_report():
    generate_daily_report()
    return {"status": "report sent"}

# ============================================================
# WEBHOOK PRINCIPAL
# ============================================================
@app.post("/webhook")
async def handle_webhook(signal: Signal):

    if signal.secret != SECRET_TOKEN:
        print(f"[ERROR] Wrong secret: {signal.secret}")
        raise HTTPException(status_code=403, detail="Invalid key")

    # --- Acumular senal del dia ---
    daily_signals.append(signal.dict())

    is_luna = signal.module is not None

    # --- Label ---
    if signal.signal_type == "PANIC_BUY":    s_label = "PANIC BUY"
    elif signal.signal_type == "PANIC_SELL": s_label = "PANIC SELL"
    elif signal.signal_type == "LUNA_LONG":  s_label = "LUNA LONG"
    elif signal.signal_type == "LUNA_SHORT": s_label = "LUNA SHORT"
    elif signal.action == "BUY":             s_label = "LONG"
    else:                                    s_label = "SHORT"

    mode_display    = "Aggressive" if signal.mode.lower() in ["agresivo", "aggressive"] else signal.mode
    instrument_name = signal.instrument if signal.instrument else signal.ticker

    # --- TP / SL / RR ---
    if is_luna:
        tp_block  = f"TP1:      {signal.tp1}\n" if signal.tp1 else ""
        tp_block += f"TP2:      {signal.tp2}\n" if signal.tp2 else ""
        tp_block += f"SL:       {signal.sl}\n"
        tp_block += f"RR1:      {signal.rr1}:1\n" if signal.rr1 else ""
        tp_block += f"RR2:      {signal.rr2}:1\n" if signal.rr2 else ""
    else:
        sl_pips  = round(abs(signal.entry - signal.sl), 5)
        tp_pips  = round(abs(signal.tp - signal.entry), 5) if signal.tp else 0
        rr       = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0
        tp_block = f"TP:       {signal.tp}\nSL:       {signal.sl}\nRR:       {rr}:1\n"

    # --- Lineas opcionales ---
    price_line  = f"Price:    {signal.price}\n"        if signal.price     else ""
    regime_line = f"Regime:   {signal.regime}\n"       if signal.regime    else ""
    htf_line    = f"HTF 15M:  {signal.htf_bias}  L:{checkmark(signal.htf_long)} S:{checkmark(signal.htf_short)}\n" if signal.htf_bias else ""
    efi_line    = f"EFI:      {efi_label(signal.efi_dir)} {signal.efi_val} ({signal.efi_dir})\n" if signal.efi_val and signal.efi_dir else ""
    rsi_line    = f"RSI:      {signal.rsi}\n"          if signal.rsi       else ""
    er_line     = f"ER:       {signal.er}\n"           if signal.er        else ""
    atr_line    = f"ATR Ratio:{signal.atr_ratio}x\n"  if signal.atr_ratio else ""
    mod_line    = f"[ {signal.module} ]\n"             if is_luna          else ""

    text = (
        f"{s_label} - {instrument_name}\n"
        f"{mod_line}"
        f"---------------\n"
        f"{price_line}"
        f"Entry:    {signal.entry}\n"
        f"{tp_block}"
        f"---------------\n"
        f"Mode:     {mode_display}\n"
        f"{regime_line}"
        f"{htf_line}"
        f"{efi_line}"
        f"{rsi_line}"
        f"{er_line}"
        f"{atr_line}"
        f"---------------\n"
        f"A signal is not an order - it's an opportunity to validate.\n"
        f"-- E-Spotter | AIMFXTOOLS --"
    )

    send_telegram(text)

    return {"status": "ok", "signal_type": signal.signal_type, "module": signal.module, "telegram_status": 200}
