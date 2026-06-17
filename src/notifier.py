"""
Notifikasi via Gmail SMTP.

Env vars yang dibutuhkan di .env:
  GMAIL_USER         = pengirim@gmail.com
  GMAIL_APP_PASSWORD = xxxx xxxx xxxx xxxx  (Google App Password, bukan password biasa)
  NOTIFY_EMAIL       = penerima@gmail.com   (boleh sama dengan GMAIL_USER)

Cara dapat App Password:
  1. Aktifkan 2FA di Google Account
  2. Buka myaccount.google.com → Security → App passwords
  3. Buat app baru → copy 16 karakter
"""

import os
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
NOTIFY_EMAIL   = os.getenv("NOTIFY_EMAIL", GMAIL_USER)


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
    """Kirim notifikasi ke NOTIFY_EMAIL via Gmail SMTP. Return True jika berhasil."""
    err = _send(message, subject)
    return err is None


def _send(message: str, subject: str | None = None) -> str | None:
    """
    Kirim email. Return None jika sukses, string error jika gagal.
    """
    if not GMAIL_USER or not GMAIL_PASSWORD:
        return "GMAIL_USER / GMAIL_APP_PASSWORD belum diset"
    if not NOTIFY_EMAIL:
        return "NOTIFY_EMAIL belum diset"

    subj = subject or _extract_subject(message)
    html = _markdown_to_html(message)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subj
    msg["From"]    = GMAIL_USER
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(message, "plain", "utf-8"))
    msg.attach(MIMEText(html,    "html",  "utf-8"))

    err587 = None
    err465 = None

    # Coba port 587 (STARTTLS)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        print(f"[Notifier] Email terkirim ke {NOTIFY_EMAIL} (port 587)")
        return None
    except Exception as e:
        err587 = str(e)
        print(f"[Notifier] Port 587 gagal: {err587}")

    # Fallback port 465 (SSL)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        print(f"[Notifier] Email terkirim ke {NOTIFY_EMAIL} (port 465)")
        return None
    except Exception as e:
        err465 = str(e)
        print(f"[Notifier] Port 465 gagal: {err465}")

    err = f"Port587: {err587} | Port465: {err465}"
    return err


def is_notifier_ready() -> bool:
    return bool(GMAIL_USER and GMAIL_PASSWORD and NOTIFY_EMAIL)
