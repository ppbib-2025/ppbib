"""
Webhook Messenger from Meta — terima pesan masuk dari Facebook Page.
Verifikasi: GET /webhook/messenger (hub.verify_token + hub.challenge).
Pesan: POST /webhook/messenger → disimpan ke data/messenger_messages.json.
Belum ada auto-reply — baca dulu, balas manual dari Page.
"""
import json
import os
from datetime import datetime

MESSAGES_FILE = "data/messenger_messages.json"


def _load() -> list:
    if not os.path.exists(MESSAGES_FILE):
        return []
    try:
        with open(MESSAGES_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(messages: list):
    os.makedirs(os.path.dirname(MESSAGES_FILE), exist_ok=True)
    with open(MESSAGES_FILE, "w") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


def verify_token(hub_token: str) -> bool:
    expected = os.getenv("MESSENGER_VERIFY_TOKEN", "")
    return bool(expected) and hub_token == expected


def handle_messenger_webhook(payload: dict) -> dict:
    """Simpan setiap pesan masuk. Return ringkasan."""
    stored = _load()
    count = 0
    for entry in payload.get("entry", []):
        for ev in entry.get("messaging", []):
            sender = (ev.get("sender") or {}).get("id", "")
            msg = ev.get("message") or {}
            text = msg.get("text", "")
            if not sender or not text:
                continue
            stored.append({
                "sender_psid": sender,
                "text": text,
                "mid": msg.get("mid", ""),
                "time": datetime.now().isoformat(),
                "replied": False,
            })
            count += 1
    if count:
        _save(stored[-500:])  # batasi 500 terakhir
    return {"status": "ok", "received": count}
