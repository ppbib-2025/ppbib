import base64
import requests

WA_API = "http://localhost:3000"


def send_whatsapp(phone: str, message: str) -> bool:
    try:
        resp = requests.post(
            f"{WA_API}/send",
            json={"phone": phone, "message": message},
            timeout=10,
        )
        return resp.json().get("success", False)
    except Exception as e:
        print(f"[WA] Gagal kirim ke {phone}: {e}")
        return False


def send_whatsapp_image(phone: str, image_bytes: bytes, caption: str = "") -> bool:
    """Kirim gambar chart ke WhatsApp. image_bytes harus PNG."""
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        resp = requests.post(
            f"{WA_API}/send-image",
            json={"phone": phone, "imageBase64": b64, "caption": caption},
            timeout=30,
        )
        return resp.json().get("success", False)
    except Exception as e:
        print(f"[WA] Gagal kirim gambar ke {phone}: {e}")
        return False


def is_wa_connected() -> bool:
    try:
        resp = requests.get(f"{WA_API}/status", timeout=5)
        return resp.json().get("status") == "connected"
    except Exception:
        return False
