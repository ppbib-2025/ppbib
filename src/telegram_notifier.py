"""
Telegram Notifier — kirim pesan teks & file video ke Telegram via Bot API.

Env vars yang dibutuhkan:
  TELEGRAM_BOT_TOKEN  — token dari @BotFather
  TELEGRAM_CHAT_ID    — chat/group/channel ID tujuan
"""
import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

_BASE = "https://api.telegram.org/bot{token}/{method}"

TG_MAX_VIDEO_MB = 49   # Telegram limit 50MB, pakai 49 untuk safety margin


def is_telegram_configured() -> bool:
    return bool(BOT_TOKEN and CHAT_ID)


def send_telegram(message: str, chat_id: str | None = None, parse_mode: str = "Markdown") -> bool:
    """
    Kirim pesan teks ke Telegram. Return True jika berhasil.
    """
    token  = BOT_TOKEN
    target = chat_id or CHAT_ID
    if not token or not target:
        print("[Telegram] TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum diset.")
        return False
    try:
        url  = _BASE.format(token=token, method="sendMessage")
        resp = requests.post(url, json={
            "chat_id":    target,
            "text":       message,
            "parse_mode": parse_mode,
        }, timeout=10)
        if resp.status_code == 200:
            return True
        print(f"[Telegram] Gagal kirim teks: {resp.status_code} — {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return False


def send_video_telegram(
    video_path: str,
    caption:    str = "",
    chat_id:    str | None = None,
) -> bool:
    """
    Kirim file video MP4 ke Telegram.
    - Jika <= 49MB : upload langsung via sendVideo (bisa langsung diputar & didownload di HP)
    - Jika > 49MB  : kirim sebagai dokumen via sendDocument (tetap bisa didownload)
    Return True jika berhasil.
    """
    token  = BOT_TOKEN
    target = chat_id or CHAT_ID
    if not token or not target:
        print("[Telegram] Token atau chat_id belum diset.")
        return False
    if not os.path.exists(video_path):
        print(f"[Telegram] File tidak ditemukan: {video_path}")
        return False

    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    method  = "sendVideo" if size_mb <= TG_MAX_VIDEO_MB else "sendDocument"
    field   = "video"     if size_mb <= TG_MAX_VIDEO_MB else "document"

    print(f"[Telegram] Kirim video ({size_mb:.1f} MB) via {method}...")
    try:
        url = _BASE.format(token=token, method=method)
        with open(video_path, "rb") as f:
            resp = requests.post(
                url,
                data={"chat_id": target, "caption": caption, "parse_mode": "Markdown"},
                files={field: (os.path.basename(video_path), f, "video/mp4")},
                timeout=180,   # video bisa besar, beri waktu lebih
            )
        if resp.status_code == 200:
            print(f"[Telegram] ✅ Video terkirim ke Telegram")
            return True
        print(f"[Telegram] Gagal kirim video: {resp.status_code} — {resp.text[:300]}")
        return False
    except Exception as e:
        print(f"[Telegram] Error kirim video: {e}")
        return False
