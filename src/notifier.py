"""
Notifikasi via Resend.com (HTTP API — tidak diblokir Railway).

Env vars yang dibutuhkan:
  RESEND_API_KEY = re_xxxxxxxxxxxx   (dari resend.com → API Keys)
  NOTIFY_EMAIL   = penerima@gmail.com

Cara setup (2 menit):
  1. Daftar di resend.com
  2. API Keys → Create → copy key
  3. Tambah ke Railway Variables
"""

import os
import re
import requests
from datetime import datetime

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
NOTIFY_EMAIL   = os.getenv("NOTIFY_EMAIL", os.getenv("GMAIL_USER", ""))
GMAIL_USER     = os.getenv("GMAIL_USER", "")      # tetap ada untuk kompatibilitas
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")


def _markdown_to_html(text: str) -> str:
    """Konversi format sederhana ke HTML untuk email yang lebih mudah dibaca."""
    lines  = text.split("\n")
    output = []
    for line in lines:
        # Bold: *teks* → <b>teks</b>
        line = re.sub(r"\*([^*]+)\*", r"<b>\1</b>", line)
        # Italic: _teks_ → <i>teks</i>
        line = re.sub(r"_([^_]+)_", r"<i>\1</i>", line)
        # Separator
        if line.strip() == "━━━━━━━━━━━━━━━━━━━━━━":
            output.append("<hr style='border:1px solid #ddd; margin:8px 0'>")
            continue
        # Emoji baris kosong
        if line.strip() == "":
            output.append("<br>")
            continue
        output.append(line + "<br>")

    body = "\n".join(output)
    return f"""
    <html><body style="font-family: monospace; font-size: 14px;
                        background:#f9f9f9; padding:16px;">
      <div style="max-width:600px; background:#fff; padding:20px;
                  border-radius:8px; border:1px solid #e0e0e0;">
        {body}
      </div>
    </body></html>
    """


def _extract_subject(text: str) -> str:
    """Ambil baris pertama sebagai subject email."""
    for line in text.split("\n"):
        clean = line.strip().lstrip("*").rstrip("*").strip()
        # Hapus emoji dan karakter kontrol
        clean = re.sub(r"[^\w\s\-–|:()%+./,]", "", clean).strip()
        if clean:
            return clean[:80]
    return "PPBIB Notifikasi"


def send_notification(message: str, subject: str | None = None) -> bool:
    """Kirim notifikasi via Resend.com. Return True jika berhasil."""
    return _send(message, subject) is None


def _send(message: str, subject: str | None = None) -> str | None:
    """Kirim email via Resend API. Return None jika sukses, string error jika gagal."""
    if not RESEND_API_KEY:
        return "RESEND_API_KEY belum diset di Railway Variables"
    if not NOTIFY_EMAIL:
        return "NOTIFY_EMAIL belum diset di Railway Variables"

    subj = subject or _extract_subject(message)
    html = _markdown_to_html(message)

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from":    "PPBIB Bot <onboarding@resend.dev>",
                "to":      [NOTIFY_EMAIL],
                "subject": subj,
                "text":    message,
                "html":    html,
            },
            timeout=15,
        )
        if resp.status_code in (200, 201):
            print(f"[Notifier] Email terkirim ke {NOTIFY_EMAIL} via Resend")
            return None
        err = f"Resend HTTP {resp.status_code}: {resp.text}"
        print(f"[Notifier] {err}")
        return err
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        print(f"[Notifier] {err}")
        return err


def is_notifier_ready() -> bool:
    return bool(RESEND_API_KEY and NOTIFY_EMAIL)
