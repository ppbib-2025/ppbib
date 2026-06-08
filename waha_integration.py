"""
PPBIB WhatsApp Webhook — WAHA + Claude via Dinoiki
+ TikTok Comment Scanner (APScheduler, tiap 15 menit)
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
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

WAHA_URL         = os.getenv("WAHA_URL", "")
WAHA_API_KEY     = os.getenv("WAHA_API_KEY", "")
WAHA_SESSION     = os.getenv("WAHA_SESSION", "default")
DINOIKI_API_KEY  = os.getenv("DINOIKI_API_KEY", "")
DINOIKI_BASE_URL = "https://ai.dinoiki.com/v1"
CLAUDE_MODEL     = "claude-sonnet-4-6"
WA_NUMBER        = os.getenv("WHATSAPP_NUMBER", "")

RATE_LIMIT_SECONDS = 3
REPLY_DELAY_MIN    = int(os.getenv("REPLY_DELAY_MIN", "4"))
REPLY_DELAY_MAX    = int(os.getenv("REPLY_DELAY_MAX", "9"))
MAX_HISTORY        = 10
LOG_FILE           = Path(__file__).parent / "leads_log.json"
DRAFT_LOG_FILE     = Path(__file__).parent / "draft_replies.json"
REPLIED_FILE       = Path(__file__).parent / "data" / "replied_comments.txt"

BOT_ENABLED  = os.getenv("BOT_ENABLED",  "true").strip().lower() == "true"
BOT_LEARNING = os.getenv("BOT_LEARNING", "false").strip().lower() == "true"

_raw_excluded = os.getenv("EXCLUDED_NUMBERS", "")
EXCLUDED_NUMBERS: set[str] = {
    n.strip().lstrip("+").replace("-", "") + "@c.us"
    for n in _raw_excluded.split(",") if n.strip()
}

SYSTEM_PROMPT_FILES = [
    Path(__file__).parent / "ppbib_agents.md",
    Path(__file__).parent / "leads_flow.md",
]

KEYWORDS_MINAT = [
    "info", "daftar", "harga", "berapa", "gimana", "cara", "mau", "ikut",
    "join", "bisa", "pelatihan", "ppbib", "kursus", "belajar", "biaya",
    "minat", "tertarik", "pengen", "pengin", "tanya", "kapan", "dimana",
    "online", "offline", "sertifikat", "hemat", "pakan", "kolam", "lele",
    "gurami", "nila", "patin", "budidaya", "ternak", "ayam", "ikan",
]

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SERVER_START_TIME = time.time()

# ── In-memory state ───────────────────────────────────────────────────────────

rate_limit_store: dict[str, float] = {}
conversation_history: dict[str, list[dict]] = {}

# ── System prompt ─────────────────────────────────────────────────────────────

def load_system_prompt() -> str:
    parts = []
    for path in SYSTEM_PROMPT_FILES:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8").strip())
        else:
            logger.warning("System prompt tidak ditemukan: %s", path)
    return "\n\n---\n\n".join(parts)

SYSTEM_PROMPT = load_system_prompt()

# ── Rate limiter ──────────────────────────────────────────────────────────────

def is_rate_limited(nomor: str) -> bool:
    return (time.time() - rate_limit_store.get(nomor, 0)) < RATE_LIMIT_SECONDS

def update_rate_limit(nomor: str) -> None:
    rate_limit_store[nomor] = time.time()

# ── Conversation history ──────────────────────────────────────────────────────

def append_history(nomor: str, role: str, content: str) -> None:
    history = conversation_history.setdefault(nomor, [])
    history.append({"role": role, "content": content})
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
        model=CLAUDE_MODEL, max_tokens=1024, messages=messages,
    )
    reply = response.choices[0].message.content.strip()
    append_history(nomor, "assistant", reply)
    return reply

# ── WAHA sender ───────────────────────────────────────────────────────────────

def is_saved_contact(nomor: str) -> bool:
    try:
        resp = requests.get(
            f"{WAHA_URL.rstrip('/')}/api/contacts",
            headers={"X-Api-Key": WAHA_API_KEY},
            params={"contactId": nomor, "session": WAHA_SESSION},
            timeout=5,
        )
        if resp.status_code != 200:
            return False
        name = (resp.json().get("name") or "")
        return bool(name) and not name.replace("+", "").replace(" ", "").replace("-", "").isdigit()
    except Exception as e:
        logger.warning("Gagal cek kontak %s: %s", nomor, e)
        return False

def kirim_pesan_wa(nomor: str, teks: str) -> bool:
    try:
        resp = requests.post(
            f"{WAHA_URL.rstrip('/')}/api/sendText",
            headers={"Content-Type": "application/json", "X-Api-Key": WAHA_API_KEY},
            json={"session": WAHA_SESSION, "chatId": nomor, "text": teks},
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("Pesan WA terkirim ke %s", nomor)
        return True
    except requests.RequestException as e:
        logger.error("Gagal kirim WA ke %s: %s", nomor, e)
        return False

# ── TikTok Scanner ────────────────────────────────────────────────────────────

def _load_replied() -> set:
    REPLIED_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not REPLIED_FILE.exists():
        return set()
    return set(REPLIED_FILE.read_text().splitlines())

def _mark_replied(comment_id: str):
    REPLIED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPLIED_FILE, "a") as f:
        f.write(comment_id + "\n")

def _is_interested(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in KEYWORDS_MINAT)

def _reply_tiktok(username: str) -> str:
    wa = WA_NUMBER or "628"
    return (
        f"Halo @{username}! Makasih udah tertarik 😊 "
        f"Info lengkap pelatihan PPBIB langsung chat kami via WA ya "
        f"👉 wa.me/{wa} — tim kami siap bantu kamu!"
    )

def scan_tiktok():
    """Scan komentar TikTok, reply yang berminat, arahkan ke WA."""
    try:
        from src.tiktok_api import get_my_videos, get_comments, reply_comment
        from src.tiktok_auth import load_token
    except Exception as e:
        logger.error("[TikTok] Import error: %s", e)
        return

    token = load_token()
    if not token:
        logger.warning("[TikTok] Token belum ada. Buka /tiktok-auth untuk login.")
        return

    logger.info("[TikTok] Scanning komentar...")
    replied = _load_replied()

    try:
        videos = get_my_videos()
    except Exception as e:
        logger.error("[TikTok] Gagal ambil video: %s", e)
        return

    for video in videos:
        video_id = video.get("id")
        try:
            result = get_comments(video_id)
            comments = result.get("data", {}).get("comments", [])
        except Exception as e:
            logger.error("[TikTok] Gagal ambil komentar video %s: %s", video_id, e)
            continue

        for comment in comments:
            cid      = comment.get("id")
            text     = comment.get("text", "")
            username = comment.get("username", "user")

            if cid in replied or not _is_interested(text):
                continue

            reply_text = _reply_tiktok(username)
            try:
                reply_comment(video_id, cid, reply_text)
                _mark_replied(cid)
                logger.info("[TikTok] Reply → @%s: %s", username, text[:50])
            except Exception as e:
                logger.error("[TikTok] Gagal reply ke @%s: %s", username, e)

    logger.info("[TikTok] Scan selesai.")

# ── Logger ────────────────────────────────────────────────────────────────────

def log_draft(nomor, pesan_masuk, draft_reply, funnel_stage="unknown"):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "nomor": nomor, "pesan_masuk": pesan_masuk,
        "draft_reply": draft_reply, "funnel_stage": funnel_stage,
        "status": "draft_tidak_terkirim",
    }
    _append_json(DRAFT_LOG_FILE, entry)

def log_leads(nomor, pesan_masuk, reply, funnel_stage="unknown"):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "nomor": nomor, "pesan_masuk": pesan_masuk,
        "reply_terkirim": reply, "funnel_stage": funnel_stage,
    }
    _append_json(LOG_FILE, entry)

def _append_json(path: Path, entry: dict):
    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = []
    existing.append(entry)
    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

# ── Funnel detector ───────────────────────────────────────────────────────────

def deteksi_funnel_stage(pesan: str) -> str:
    p = pesan.lower()
    if any(w in p for w in ["harga", "biaya", "berapa", "daftar", "bayar", "ikut", "transfer"]):
        return "F4"
    if any(w in p for w in ["lahan", "modal", "target", "mulai bulan", "rencana"]):
        return "F3"
    if any(w in p for w in ["nila", "lele", "gurame", "mas", "patin", "fcr", "pakan", "kolam"]):
        return "F2"
    return "F1"

# ── Flask app ─────────────────────────────────────────────────────────────────

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "bot_enabled": BOT_ENABLED,
        "bot_learning": BOT_LEARNING,
        "waha_url": WAHA_URL,
        "waha_session": WAHA_SESSION,
        "system_prompt_loaded": bool(SYSTEM_PROMPT),
        "dinoiki_key_set": bool(DINOIKI_API_KEY),
        "tiktok_token": bool(_load_token_safe()),
        "leads_logged": _count_json(LOG_FILE),
        "drafts_logged": _count_json(DRAFT_LOG_FILE),
    })


@app.route("/tiktok-auth", methods=["GET"])
def tiktok_auth():
    """Langkah 1: Dapatkan URL login TikTok."""
    try:
        from src.tiktok_auth import get_auth_url
        url = get_auth_url()
        return jsonify({"auth_url": url, "petunjuk": "Buka auth_url di browser, login TikTok, lalu copy 'code' dari URL redirect ke /tiktok-callback?code=..."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tiktok-callback", methods=["GET"])
def tiktok_callback():
    """Langkah 2: Tukar code TikTok dengan token."""
    code = request.args.get("code", "")
    if not code:
        return jsonify({"error": "Parameter 'code' tidak ada"}), 400
    try:
        from src.tiktok_auth import exchange_code_for_token
        result = exchange_code_for_token(code)
        if "data" in result:
            return jsonify({"success": True, "message": "Token TikTok berhasil disimpan! Scanner aktif 15 menit lagi."})
        return jsonify({"error": result}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tiktok-scan", methods=["POST"])
def tiktok_scan_now():
    """Trigger scan TikTok manual (tanpa nunggu 15 menit)."""
    import threading
    threading.Thread(target=scan_tiktok, daemon=True).start()
    return jsonify({"status": "scanning dimulai"})


@app.route("/webhook", methods=["POST"])
def webhook():
    if not BOT_ENABLED and not BOT_LEARNING:
        return jsonify({"status": "paused"}), 200

    data    = request.get_json(silent=True) or {}
    if data.get("event") != "message":
        return jsonify({"status": "ignored"}), 200

    payload = data.get("payload", {})
    nomor   = payload.get("from", "")
    teks    = (payload.get("body") or "").strip()

    if nomor in EXCLUDED_NUMBERS:
        return jsonify({"status": "ignored", "reason": "dikecualikan"}), 200
    if is_saved_contact(nomor):
        return jsonify({"status": "ignored", "reason": "kontak tersimpan"}), 200
    if "@g.us" in nomor or not teks or payload.get("fromMe"):
        return jsonify({"status": "ignored"}), 200

    msg_ts = payload.get("timestamp", 0)
    if msg_ts and msg_ts < SERVER_START_TIME:
        return jsonify({"status": "ignored", "reason": "pesan lama"}), 200

    logger.info("WA masuk dari %s: %s", nomor, teks[:80])

    if is_rate_limited(nomor):
        return jsonify({"status": "rate_limited"}), 200

    try:
        reply = get_ai_reply(nomor, teks)
    except Exception as e:
        logger.error("Error AI: %s", e)
        return jsonify({"status": "error"}), 500

    funnel = deteksi_funnel_stage(teks)

    if BOT_LEARNING:
        log_draft(nomor, teks, reply, funnel)
        return jsonify({"status": "learning", "funnel_stage": funnel}), 200

    delay = random.uniform(REPLY_DELAY_MIN, REPLY_DELAY_MAX)
    time.sleep(delay)

    terkirim = kirim_pesan_wa(nomor, reply)
    if terkirim:
        update_rate_limit(nomor)
    log_leads(nomor, teks, reply, funnel)

    return jsonify({"status": "ok", "funnel_stage": funnel, "reply_sent": terkirim}), 200


# ── Helper ────────────────────────────────────────────────────────────────────

def _count_json(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return 0

def _load_token_safe() -> dict | None:
    try:
        from src.tiktok_auth import load_token
        return load_token()
    except Exception:
        return None

# ── Scheduler (TikTok scan tiap 15 menit) ────────────────────────────────────

scheduler = BackgroundScheduler()
scheduler.add_job(scan_tiktok, "interval", minutes=15, id="tiktok_scan")
scheduler.start()
logger.info("TikTok scanner aktif — scan tiap 15 menit.")

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
