"""
Telegram Notifier — kirim pesan teks ke Telegram via Bot API.

Env vars yang dibutuhkan:
  TELEGRAM_BOT_TOKEN  — token dari @BotFather
  TELEGRAM_CHAT_ID    — chat/group/channel ID tujuan
"""
import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def is_telegram_configured() -> bool:
    return bool(BOT_TOKEN and CHAT_ID)


def send_telegram(message: str, chat_id: str | None = None, parse_mode: str = "Markdown") -> bool:
    """
    Kirim pesan ke Telegram. Return True jika berhasil.
    chat_id opsional — default pakai TELEGRAM_CHAT_ID dari env.
    """
    token = BOT_TOKEN
    target = chat_id or CHAT_ID
    if not token or not target:
        print("[Telegram] TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum diset.")
        return False
    try:
        url = API_URL.format(token=token)
        resp = requests.post(url, json={
            "chat_id": target,
            "text": message,
            "parse_mode": parse_mode,
        }, timeout=10)
        if resp.status_code == 200:
            return True
        print(f"[Telegram] Gagal: {resp.status_code} — {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return False
