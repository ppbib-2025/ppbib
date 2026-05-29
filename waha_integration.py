"""
PPBIB WhatsApp Webhook — WAHA + Groq
Terima pesan WA via WAHA, proses dengan Groq (llama-3.1-8b-instant), kirim reply balik.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import openai
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

WAHA_URL     = os.getenv("WAHA_URL",    "https://waha-qelypbwuouqo.cgk-srikandi.sumopod.my.id")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "pYYp3LKM09t6yHulcUarEWtSIWdPDHkL")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL    = "llama-3.1-8b-instant"

RATE_LIMIT_SECONDS = 300        # 5 menit per nomor
MAX_HISTORY        = 10         # pesan terakhir yang disimpan per nomor
LOG_FILE           = Path(__file__).parent / "leads_log.json"
SYSTEM_PROMPT_FILES = [
    Path(__file__).parent / "ppbib_agents.md",
    Path(__file__).parent / "leads_flow.md",
]

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── In-memory state ───────────────────────────────────────────────────────────

# { nomor: last_reply_timestamp }
rate_limit_store: dict[str, float] = {}

# { nomor: [{"role": "user"|"assistant", "content": "..."}] }
conversation_history: dict[str, list[dict]] = {}

# ── System prompt ─────────────────────────────────────────────────────────────

def load_system_prompt() -> str:
    parts = []
    for path in SYSTEM_PROMPT_FILES:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8").strip())
        else:
            logger.warning("System prompt file tidak ditemukan: %s", path)
    return "\n\n---\n\n".join(parts)

SYSTEM_PROMPT = load_system_prompt()

# ── Rate limiter ──────────────────────────────────────────────────────────────

def is_rate_limited(nomor: str) -> bool:
    last = rate_limit_store.get(nomor, 0)
    return (time.time() - last) < RATE_LIMIT_SECONDS

def update_rate_limit(nomor: str) -> None:
    rate_limit_store[nomor] = time.time()

# ── Conversation history ──────────────────────────────────────────────────────

def append_history(nomor: str, role: str, content: str) -> None:
    history = conversation_history.setdefault(nomor, [])
    history.append({"role": role, "content": content})
    # Pertahankan hanya MAX_HISTORY pesan terakhir
    if len(history) > MAX_HISTORY:
        conversation_history[nomor] = history[-MAX_HISTORY:]

def get_history(nomor: str) -> list[dict]:
    return conversation_history.get(nomor, [])

# ── Groq ──────────────────────────────────────────────────────────────────────

def get_ai_reply(nomor: str, pesan: str) -> str:
    append_history(nomor, "user", pesan)
    client = openai.OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(nomor)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=1024,
        messages=messages,
    )
    reply = response.choices[0].message.content.strip()
    append_history(nomor, "assistant", reply)
    return reply

# ── WAHA sender ───────────────────────────────────────────────────────────────

def kirim_pesan_wa(nomor: str, teks: str) -> bool:
    url = f"{WAHA_URL.rstrip('/')}/api/sendText"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": WAHA_API_KEY,
    }
    payload = {
        "session": WAHA_SESSION,
        "chatId": nomor,
        "text": teks,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        logger.info("Pesan terkirim ke %s", nomor)
        return True
    except requests.RequestException as e:
        logger.error("Gagal kirim ke %s: %s", nomor, e)
        return False

# ── Logger ke JSON ────────────────────────────────────────────────────────────

def log_leads(nomor: str, pesan_masuk: str, reply: str, funnel_stage: str = "unknown") -> None:
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "nomor": nomor,
        "pesan_masuk": pesan_masuk,
        "reply_terkirim": reply,
        "funnel_stage": funnel_stage,
    }
    existing: list[dict] = []
    if LOG_FILE.exists():
        try:
            existing = json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = []
    existing.append(entry)
    LOG_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

# ── Funnel stage detector (heuristik ringan) ──────────────────────────────────

def deteksi_funnel_stage(pesan: str) -> str:
    pesan_lower = pesan.lower()
    if any(w in pesan_lower for w in ["harga", "biaya", "berapa", "daftar", "bayar", "ikut", "transfer"]):
        return "F4"
    if any(w in pesan_lower for w in ["lahan", "modal", "target", "mulai bulan", "rencana"]):
        return "F3"
    if any(w in pesan_lower for w in ["nila", "lele", "gurame", "mas", "patin", "fcr", "pakan", "kolam"]):
        return "F2"
    return "F1"

# ── Flask app ─────────────────────────────────────────────────────────────────

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "waha_url": WAHA_URL,
        "waha_session": WAHA_SESSION,
        "system_prompt_loaded": bool(SYSTEM_PROMPT),
        "groq_key_set": bool(GROQ_API_KEY),
        "leads_logged": _count_logs(),
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    # Filter: hanya proses event type "message"
    if data.get("event") != "message":
        return jsonify({"status": "ignored", "reason": "bukan event message"}), 200

    payload = data.get("payload", {})
    nomor   = payload.get("from", "")
    teks    = payload.get("body", "").strip()

    # Filter: abaikan pesan grup
    if "@g.us" in nomor:
        return jsonify({"status": "ignored", "reason": "pesan grup"}), 200

    # Filter: pesan kosong
    if not teks:
        return jsonify({"status": "ignored", "reason": "pesan kosong"}), 200

    # Filter: pesan dari diri sendiri (status broadcast, dll)
    if payload.get("fromMe"):
        return jsonify({"status": "ignored", "reason": "pesan dari bot sendiri"}), 200

    logger.info("Pesan masuk dari %s: %s", nomor, teks[:80])

    # Rate limit
    if is_rate_limited(nomor):
        logger.info("Rate limited: %s", nomor)
        return jsonify({"status": "rate_limited", "nomor": nomor}), 200

    # Dapatkan reply dari OpenAI
    try:
        reply = get_ai_reply(nomor, teks)
    except Exception as e:
        logger.error("Error Groq API: %s", e)
        return jsonify({"status": "error", "detail": "groq api error"}), 500

    # Kirim reply via WAHA
    terkirim = kirim_pesan_wa(nomor, reply)
    if terkirim:
        update_rate_limit(nomor)

    # Log ke file
    funnel = deteksi_funnel_stage(teks)
    log_leads(nomor, teks, reply, funnel)

    return jsonify({
        "status": "ok",
        "nomor": nomor,
        "funnel_stage": funnel,
        "reply_sent": terkirim,
    }), 200


def _count_logs() -> int:
    if not LOG_FILE.exists():
        return 0
    try:
        return len(json.loads(LOG_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return 0


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("System prompt dimuat: %d karakter", len(SYSTEM_PROMPT))
    logger.info("Log file: %s", LOG_FILE)
    app.run(host="0.0.0.0", port=5000, debug=False)
