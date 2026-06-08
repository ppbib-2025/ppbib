"""
PPBIB WhatsApp Webhook — WAHA + Claude via Dinoiki
Terima pesan WA via WAHA, proses dengan Claude, kirim reply balik.
"""

import json
import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path

import openai
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

WAHA_URL        = os.getenv("WAHA_URL",    "https://waha-qelypbwuouqo.cgk-srikandi.sumopod.my.id")
WAHA_API_KEY    = os.getenv("WAHA_API_KEY", "pYYp3LKM09t6yHulcUarEWtSIWdPDHkL")
WAHA_SESSION    = os.getenv("WAHA_SESSION", "default")
DINOIKI_API_KEY = os.getenv("DINOIKI_API_KEY", "")
DINOIKI_BASE_URL = "https://ai.dinoiki.com/v1"
CLAUDE_MODEL    = "claude-sonnet-4-6"

RATE_LIMIT_SECONDS = 3           # cegah duplikat webhook, bukan batasi percakapan
REPLY_DELAY_MIN    = int(os.getenv("REPLY_DELAY_MIN", "4"))   # detik minimum jeda
REPLY_DELAY_MAX    = int(os.getenv("REPLY_DELAY_MAX", "9"))   # detik maksimum jeda
MAX_HISTORY        = 10         # pesan terakhir yang disimpan per nomor
LOG_FILE           = Path(__file__).parent / "leads_log.json"
DRAFT_LOG_FILE     = Path(__file__).parent / "draft_replies.json"

# On/off switch
BOT_ENABLED  = os.getenv("BOT_ENABLED",  "false").strip().lower() == "true"
# Learning mode: baca + generate reply tapi tidak kirim, simpan ke draft_replies.json
BOT_LEARNING = os.getenv("BOT_LEARNING", "true").strip().lower() == "true"

# Nomor yang dikecualikan dari auto-reply (teman, keluarga, dll)
# Format di env: "6281234567890,6289876543210" (tanpa @c.us)
_raw_excluded = os.getenv("EXCLUDED_NUMBERS", "")
EXCLUDED_NUMBERS: set[str] = {
    n.strip().lstrip("+").replace("-", "") + "@c.us"
    for n in _raw_excluded.split(",") if n.strip()
}
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

SERVER_START_TIME = time.time()  # abaikan pesan lama sebelum server nyala

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

# ── Claude via Dinoiki ────────────────────────────────────────────────────────

def get_ai_reply(nomor: str, pesan: str) -> str:
    append_history(nomor, "user", pesan)
    client = openai.OpenAI(api_key=DINOIKI_API_KEY, base_url=DINOIKI_BASE_URL)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(nomor)
    response = client.chat.completions.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=messages,
    )
    reply = response.choices[0].message.content.strip()
    append_history(nomor, "assistant", reply)
    return reply

# ── WAHA sender ───────────────────────────────────────────────────────────────

def is_saved_contact(nomor: str) -> bool:
    """Cek apakah nomor sudah tersimpan di kontak (punya nama di address book)."""
    try:
        url = f"{WAHA_URL.rstrip('/')}/api/contacts"
        headers = {"X-Api-Key": WAHA_API_KEY}
        params = {"contactId": nomor, "session": WAHA_SESSION}
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        if resp.status_code != 200:
            return False
        contact = resp.json()
        name = contact.get("name", "") or ""
        # Kontak tersimpan punya nama yang bukan sekadar angka/nomor telepon
        return bool(name) and not name.replace("+", "").replace(" ", "").replace("-", "").isdigit()
    except Exception as e:
        logger.warning("Gagal cek kontak %s: %s", nomor, e)
        return False  # Kalau gagal cek, proses normal saja

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

def log_draft(nomor: str, pesan_masuk: str, draft_reply: str, funnel_stage: str = "unknown") -> None:
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "nomor": nomor,
        "pesan_masuk": pesan_masuk,
        "draft_reply": draft_reply,
        "funnel_stage": funnel_stage,
        "status": "draft_tidak_terkirim",
    }
    existing: list[dict] = []
    if DRAFT_LOG_FILE.exists():
        try:
            existing = json.loads(DRAFT_LOG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = []
    existing.append(entry)
    DRAFT_LOG_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

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
        "bot_enabled": BOT_ENABLED,
        "waha_url": WAHA_URL,
        "waha_session": WAHA_SESSION,
        "system_prompt_loaded": bool(SYSTEM_PROMPT),
        "dinoiki_key_set": bool(DINOIKI_API_KEY),
        "bot_learning": BOT_LEARNING,
        "leads_logged": _count_logs(),
        "drafts_logged": _count_drafts(),
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    if not BOT_ENABLED and not BOT_LEARNING:
        return jsonify({"status": "paused", "reason": "bot dinonaktifkan"}), 200

    data = request.get_json(silent=True) or {}

    # Filter: hanya proses event type "message"
    if data.get("event") != "message":
        return jsonify({"status": "ignored", "reason": "bukan event message"}), 200

    payload = data.get("payload", {})
    nomor   = payload.get("from", "")
    teks    = (payload.get("body") or "").strip()

    # Filter: nomor dikecualikan manual (teman/keluarga)
    if nomor in EXCLUDED_NUMBERS:
        logger.info("Nomor dikecualikan manual: %s", nomor)
        return jsonify({"status": "ignored", "reason": "nomor dikecualikan"}), 200

    # Filter: kontak tersimpan (ada nama di address book = bukan leads asing)
    if is_saved_contact(nomor):
        logger.info("Kontak tersimpan diabaikan: %s", nomor)
        return jsonify({"status": "ignored", "reason": "kontak tersimpan"}), 200

    # Filter: abaikan pesan grup
    if "@g.us" in nomor:
        return jsonify({"status": "ignored", "reason": "pesan grup"}), 200

    # Filter: pesan kosong
    if not teks:
        return jsonify({"status": "ignored", "reason": "pesan kosong"}), 200

    # Filter: pesan dari diri sendiri (status broadcast, dll)
    if payload.get("fromMe"):
        return jsonify({"status": "ignored", "reason": "pesan dari bot sendiri"}), 200

    # Filter: pesan lama (sebelum server nyala) — hindari replay saat WAHA reconnect
    msg_timestamp = payload.get("timestamp", 0)
    if msg_timestamp and msg_timestamp < SERVER_START_TIME:
        logger.info("Pesan lama diabaikan dari %s (ts=%s)", nomor, msg_timestamp)
        return jsonify({"status": "ignored", "reason": "pesan lama"}), 200

    logger.info("Pesan masuk dari %s: %s", nomor, teks[:80])

    # Rate limit
    if is_rate_limited(nomor):
        logger.info("Rate limited: %s", nomor)
        return jsonify({"status": "rate_limited", "nomor": nomor}), 200

    try:
        reply = get_ai_reply(nomor, teks)
    except Exception as e:
        logger.error("Error Claude API: %s", e)
        return jsonify({"status": "error", "detail": "claude api error"}), 500

    funnel = deteksi_funnel_stage(teks)

    # Learning mode — simpan draft, jangan kirim
    if BOT_LEARNING:
        log_draft(nomor, teks, reply, funnel)
        logger.info("Learning mode: draft disimpan untuk %s", nomor)
        return jsonify({"status": "learning", "nomor": nomor, "funnel_stage": funnel}), 200

    # Jeda acak sebelum kirim — biar terasa lebih human
    delay = random.uniform(REPLY_DELAY_MIN, REPLY_DELAY_MAX)
    logger.info("Jeda %.1f detik sebelum kirim ke %s", delay, nomor)
    time.sleep(delay)

    # Kirim reply via WAHA
    terkirim = kirim_pesan_wa(nomor, reply)
    if terkirim:
        update_rate_limit(nomor)

    # Log ke file
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


def _count_drafts() -> int:
    if not DRAFT_LOG_FILE.exists():
        return 0
    try:
        return len(json.loads(DRAFT_LOG_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return 0


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("System prompt dimuat: %d karakter", len(SYSTEM_PROMPT))
    logger.info("Log file: %s", LOG_FILE)
    app.run(host="0.0.0.0", port=5000, debug=False)
