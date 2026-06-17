"""
Health check harian — cek semua API token & koneksi kritis.
Kirim laporan via email setiap hari jam 09:00.

Env vars yang dibutuhkan:
  HEALTH_CHECK_EMAIL_TO   — alamat tujuan (contoh: admin@gmail.com)
  HEALTH_CHECK_EMAIL_FROM — akun Gmail pengirim
  HEALTH_CHECK_EMAIL_PASS — App Password Gmail (bukan password biasa)
"""
import os
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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

_ICON    = {"OK": "✅", "WARN": "⚠️", "ERROR": "❌"}
_ICON_H  = {"OK": "✅", "WARN": "⚠️", "ERROR": "❌"}  # sama, tapi HTML pakai tabel
_ROW_CLR = {"OK": "#d4edda", "WARN": "#fff3cd", "ERROR": "#f8d7da"}


def _build_report() -> tuple[list, list, list]:
    """Return (rows, errors, warnings). rows = list of (name, status, msg)."""
    rows, errors, warnings = [], [], []
    for name, fn in CHECKS:
        result = fn()
        rows.append((name, result["status"], result["msg"]))
        if result["status"] == "ERROR":
            errors.append(name)
        elif result["status"] == "WARN":
            warnings.append(name)
    return rows, errors, warnings


def _plain_text(rows: list, errors: list, warnings: list) -> str:
    now = datetime.now().strftime("%d %b %Y %H:%M")
    lines = [f"Health Check PPBIB — {now}\n"]
    for name, status, msg in rows:
        icon = _ICON.get(status, "?")
        lines.append(f"{icon} {name}: {msg}")
    lines.append("")
    if errors:
        lines.append(f"KRITIS ({len(errors)}): {', '.join(errors)}")
    elif warnings:
        lines.append(f"Peringatan ({len(warnings)}): {', '.join(warnings)}")
    else:
        lines.append("Semua sistem berjalan normal.")
    return "\n".join(lines)


def _html(rows: list, errors: list, warnings: list) -> str:
    now = datetime.now().strftime("%d %b %Y %H:%M")
    if errors:
        summary_bg, summary_txt = "#f8d7da", f"🚨 {len(errors)} masalah kritis: {', '.join(errors)}"
    elif warnings:
        summary_bg, summary_txt = "#fff3cd", f"⚠️ {len(warnings)} peringatan: {', '.join(warnings)}"
    else:
        summary_bg, summary_txt = "#d4edda", "✨ Semua sistem berjalan normal!"

    rows_html = ""
    for name, status, msg in rows:
        bg = _ROW_CLR.get(status, "#fff")
        icon = _ICON_H.get(status, "?")
        rows_html += f"""
        <tr style="background:{bg}">
          <td style="padding:8px 12px;font-weight:bold">{icon} {name}</td>
          <td style="padding:8px 12px">{msg}</td>
        </tr>"""

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2 style="color:#333">🏥 Health Check PPBIB</h2>
      <p style="color:#666;margin-top:-10px">{now}</p>
      <table style="width:100%;border-collapse:collapse;border:1px solid #dee2e6">
        <thead>
          <tr style="background:#343a40;color:#fff">
            <th style="padding:8px 12px;text-align:left">Layanan</th>
            <th style="padding:8px 12px;text-align:left">Status</th>
          </tr>
        </thead>
        <tbody>{rows_html}
        </tbody>
      </table>
      <p style="margin-top:16px;padding:10px;background:{summary_bg};border-radius:4px">
        {summary_txt}
      </p>
      <p style="color:#999;font-size:12px">PPBIB Automation System</p>
    </body></html>
    """


def send_health_check_email(plain: str, html: str, errors: list, warnings: list) -> bool:
    to_addr   = os.getenv("HEALTH_CHECK_EMAIL_TO")
    from_addr = os.getenv("HEALTH_CHECK_EMAIL_FROM")
    password  = os.getenv("HEALTH_CHECK_EMAIL_PASS")

    if not all([to_addr, from_addr, password]):
        print("[HealthCheck] Email tidak terkirim — set HEALTH_CHECK_EMAIL_TO/FROM/PASS di .env")
        return False

    if errors:
        subject = f"🚨 [PPBIB] Health Check — {len(errors)} masalah kritis!"
    elif warnings:
        subject = f"⚠️ [PPBIB] Health Check — {len(warnings)} peringatan"
    else:
        subject = "✅ [PPBIB] Health Check — Semua sistem normal"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_addr
    msg["To"]      = to_addr
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(from_addr, password)
            server.sendmail(from_addr, to_addr, msg.as_string())
        print(f"[HealthCheck] Email terkirim ke {to_addr}")
        return True
    except Exception as e:
        print(f"[HealthCheck] Gagal kirim email: {e}")
        return False


def run_health_check() -> str:
    rows, errors, warnings = _build_report()
    plain = _plain_text(rows, errors, warnings)
    html  = _html(rows, errors, warnings)

    print(plain)
    send_health_check_email(plain, html, errors, warnings)
    return plain
