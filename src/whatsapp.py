"""
WhatsApp client menggunakan WAHA (WhatsApp HTTP API).
Variabel env: WAHA_URL, WAHA_API_KEY, WAHA_SESSION
"""
import os
import requests

WAHA_URL = os.getenv("WAHA_URL", "").rstrip("/")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")


def _headers() -> dict:
    return {"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"}


def send_whatsapp(phone: str, message: str) -> bool:
    # Format nomor: 628xxx → 628xxx@c.us
    clean = phone.replace("+", "").replace("-", "").replace(" ", "")
    chat_id = clean + "@c.us"
    try:
        resp = requests.post(
            f"{WAHA_URL}/api/sendText",
            headers=_headers(),
            json={"chatId": chat_id, "text": message, "session": WAHA_SESSION},
            timeout=15,
        )
        resp.raise_for_status()
        print(f"[WA] Terkirim ke {phone}")
        return True
    except Exception as e:
        print(f"[WA] Gagal kirim ke {phone}: {e}")
        return False


def is_wa_connected() -> bool:
    try:
        resp = requests.get(
            f"{WAHA_URL}/api/sessions/{WAHA_SESSION}",
            headers=_headers(),
            timeout=5,
        )
        data = resp.json()
        return data.get("status") in ("WORKING", "CONNECTED")
    except Exception:
        return False
