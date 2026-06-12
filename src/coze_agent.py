"""
Coze API integration — Rina, agen marketing PPBIB.
Docs: https://www.coze.com/docs/developer_guides/chat_v3
"""
import os
import time
import requests

COZE_API_KEY  = os.getenv("COZE_API_KEY", "")
COZE_BOT_ID   = os.getenv("COZE_BOT_ID", "")
COZE_BASE_URL = os.getenv("COZE_BASE_URL", "https://api.coze.com")

_HEADERS = lambda: {
    "Authorization": f"Bearer {COZE_API_KEY}",
    "Content-Type": "application/json",
}

# Context yang dikirim ke Coze agar balasan makin personalized
_CTX_TEMPLATE = (
    "[INFO LEAD — jangan sebut ini ke user]\n"
    "Status funnel  : {status}\n"
    "Follow-up ke-  : {follow_up_count}\n"
    "Hari ke-       : {hari_ke} sejak pertama kontak\n"
    "---\n"
    "Pesan lead:\n{message}"
)


def ask_rina(
    user_id: str,
    message: str,
    conversation_id: str = None,
    funnel_context: dict = None,
) -> tuple[str, str]:
    """
    Kirim pesan ke Coze bot Rina, tunggu balasan.
    Returns (reply_text, conversation_id).
    Jika Coze tidak tersedia, kembalikan fallback.
    """
    if not COZE_API_KEY or not COZE_BOT_ID:
        print("[Coze] COZE_API_KEY / COZE_BOT_ID belum diset — pakai fallback.")
        return _fallback(), conversation_id or ""

    content = message
    if funnel_context:
        content = _CTX_TEMPLATE.format(message=message, **funnel_context)

    payload = {
        "bot_id": COZE_BOT_ID,
        "user_id": user_id,
        "additional_messages": [
            {"role": "user", "content": content, "content_type": "text"}
        ],
        "stream": False,
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id

    try:
        resp = requests.post(
            f"{COZE_BASE_URL}/v3/chat",
            json=payload,
            headers=_HEADERS(),
            timeout=30,
        )
        body = resp.json()
        if body.get("code") != 0:
            print(f"[Coze] API error: {body}")
            return _fallback(), conversation_id or ""

        chat_id = body["data"]["id"]
        conv_id  = body["data"]["conversation_id"]
        reply    = _poll_and_fetch(chat_id, conv_id)
        return reply or _fallback(), conv_id

    except Exception as exc:
        print(f"[Coze] Exception: {exc}")
        return _fallback(), conversation_id or ""


# ── internal helpers ──────────────────────────────────────────────────────────

def _poll_and_fetch(chat_id: str, conv_id: str, max_wait: int = 30) -> str:
    poll_url = f"{COZE_BASE_URL}/v3/chat/retrieve"
    for _ in range(max_wait):
        time.sleep(1)
        try:
            r = requests.get(
                poll_url,
                params={"chat_id": chat_id, "conversation_id": conv_id},
                headers=_HEADERS(),
                timeout=10,
            )
            status = r.json().get("data", {}).get("status", "")
        except Exception:
            continue
        if status == "completed":
            return _fetch_answer(chat_id, conv_id)
        if status in ("failed", "requires_action"):
            print(f"[Coze] Chat ended with status: {status}")
            return ""
    print("[Coze] Timeout menunggu balasan.")
    return ""


def _fetch_answer(chat_id: str, conv_id: str) -> str:
    try:
        r = requests.get(
            f"{COZE_BASE_URL}/v3/chat/message/list",
            params={"chat_id": chat_id, "conversation_id": conv_id},
            headers=_HEADERS(),
            timeout=10,
        )
        for msg in r.json().get("data", []):
            if msg.get("role") == "assistant" and msg.get("type") == "answer":
                return msg.get("content", "")
    except Exception as exc:
        print(f"[Coze] Gagal ambil pesan: {exc}")
    return ""


def _fallback() -> str:
    return (
        "Halo! Terima kasih sudah menghubungi PPBIB 🙏\n"
        "Tim kami sedang memproses pesan Anda dan akan segera membalas.\n"
        "Ada yang bisa kami bantu?"
    )
