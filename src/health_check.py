"""
Health check harian — cek semua API token & koneksi kritis.
Kirim notif WhatsApp jika ada yang bermasalah.
"""
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Checker per layanan ──────────────────────────────────────────────────────

def _check_tiktok() -> dict:
    from src.tiktok_auth import load_token
    token = load_token()
    if not token:
        return {"status": "ERROR", "msg": "Token tidak ada — perlu re-auth TikTok"}

    try:
        resp = requests.post(
            "https://open.tiktokapis.com/v2/video/list/",
            headers={"Authorization": f"Bearer {token['access_token']}"},
            json={"max_count": 1},
            params={"fields": "id"},
            timeout=10,
        )
        err_code = resp.json().get("error", {}).get("code", "")
        if err_code in ("access_token_invalid", "access_token_expired"):
            return {"status": "ERROR", "msg": "Token expired/invalid — jalankan refresh token"}
        return {"status": "OK", "msg": "Token valid"}
    except Exception as e:
        return {"status": "WARN", "msg": f"Tidak bisa reach TikTok API: {e}"}


def _check_instagram_facebook() -> dict:
    from src.instagram_auth import load_token
    token = load_token()
    if not token:
        return {"status": "ERROR", "msg": "Token tidak ada — perlu setup Instagram auth"}

    saved_at_str = token.get("saved_at")
    expires_in = token.get("expires_in", 0)

    if saved_at_str and expires_in:
        saved_at = datetime.fromisoformat(saved_at_str)
        expiry = saved_at + timedelta(seconds=int(expires_in))
        days_left = (expiry - datetime.now()).days

        if days_left <= 0:
            return {"status": "ERROR", "msg": "Token EXPIRED — perlu re-auth sekarang"}
        if days_left <= 7:
            return {"status": "WARN", "msg": f"Token akan expire dalam {days_left} hari — segera renew"}
        return {"status": "OK", "msg": f"Token valid, expire {days_left} hari lagi"}

    # Fallback: live check ke Graph API
    try:
        resp = requests.get(
            "https://graph.facebook.com/v19.0/me/accounts",
            params={"access_token": token["access_token"]},
            timeout=10,
        )
        data = resp.json()
        if "error" in data:
            err_msg = data["error"].get("message", "unknown error")
            return {"status": "ERROR", "msg": f"Token invalid: {err_msg}"}
        return {"status": "OK", "msg": "Token valid (tanpa info expiry)"}
    except Exception as e:
        return {"status": "WARN", "msg": f"Tidak bisa reach Facebook API: {e}"}


def _check_whatsapp() -> dict:
    from src.whatsapp import is_wa_connected
    if is_wa_connected():
        return {"status": "OK", "msg": "Terhubung"}
    return {"status": "ERROR", "msg": "TIDAK terhubung — cek server WhatsApp (localhost:3000)"}


def _check_anthropic() -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"status": "ERROR", "msg": "ANTHROPIC_API_KEY tidak diset di env"}
    if not api_key.startswith("sk-ant-"):
        return {"status": "WARN", "msg": "ANTHROPIC_API_KEY format tidak dikenal"}
    return {"status": "OK", "msg": "API key tersedia"}


def _check_fal() -> dict:
    if not os.getenv("FAL_KEY"):
        return {"status": "WARN", "msg": "FAL_KEY tidak diset — video AI nonaktif"}
    return {"status": "OK", "msg": "FAL_KEY tersedia — video AI aktif"}


def _check_env_vars() -> dict:
    required = [
        "TIKTOK_CLIENT_KEY",
        "TIKTOK_CLIENT_SECRET",
        "INSTAGRAM_APP_ID",
        "INSTAGRAM_APP_SECRET",
        "ANTHROPIC_API_KEY",
        "WHATSAPP_NUMBER",
    ]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        return {"status": "ERROR", "msg": f"Env var hilang: {', '.join(missing)}"}
    return {"status": "OK", "msg": "Semua env var wajib tersedia"}


# ── Entry point ──────────────────────────────────────────────────────────────

CHECKS = [
    ("TikTok API",          _check_tiktok),
    ("Instagram/Facebook",  _check_instagram_facebook),
    ("WhatsApp",            _check_whatsapp),
    ("Anthropic AI",        _check_anthropic),
    ("Video AI (FAL)",      _check_fal),
    ("Env Variables",       _check_env_vars),
]

_ICON = {"OK": "✅", "WARN": "⚠️", "ERROR": "❌"}


def run_health_check() -> str:
    now = datetime.now().strftime("%d %b %Y %H:%M")
    lines = [f"🏥 *Health Check PPBIB*\n_{now}_\n"]

    errors, warnings = [], []

    for name, fn in CHECKS:
        result = fn()
        icon = _ICON.get(result["status"], "❓")
        lines.append(f"{icon} *{name}*: {result['msg']}")
        if result["status"] == "ERROR":
            errors.append(name)
        elif result["status"] == "WARN":
            warnings.append(name)

    lines.append("")
    if errors:
        lines.append(f"🚨 *{len(errors)} masalah kritis* perlu ditangani:")
        for e in errors:
            lines.append(f"  • {e}")
    elif warnings:
        lines.append(f"⚠️ *{len(warnings)} peringatan* (tidak mengganggu operasi):")
        for w in warnings:
            lines.append(f"  • {w}")
    else:
        lines.append("✨ Semua sistem berjalan normal!")

    report = "\n".join(lines)
    print(report)
    return report
