"""
Telegram notifikasi — alternatif/pelengkap WhatsApp.
Setup:
  1. Chat @BotFather di Telegram → /newbot → dapat BOT_TOKEN
  2. Kirim pesan ke bot-mu, lalu buka:
     https://api.telegram.org/bot<TOKEN>/getUpdates
     Ambil nilai chat.id → itu TELEGRAM_CHAT_ID
  3. Set di .env:
     TELEGRAM_BOT_TOKEN=123456:ABC-xxx
     TELEGRAM_CHAT_ID=123456789
"""
import os
import requests

TELEGRAM_API = "https://api.telegram.org"


def _token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "")


def _chat_id() -> str:
    return os.getenv("TELEGRAM_CHAT_ID", "")


def is_telegram_configured() -> bool:
    return bool(_token() and _chat_id())


def send_telegram(message: str) -> bool:
    if not is_telegram_configured():
        print("[Telegram] Token/chat_id belum diset.")
        return False
    try:
        resp = requests.post(
            f"{TELEGRAM_API}/bot{_token()}/sendMessage",
            json={
                "chat_id": _chat_id(),
                "text": message,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            return True
        print(f"[Telegram] Gagal: {data.get('description')}")
        return False
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return False
