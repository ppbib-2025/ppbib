"""
Notifikasi via Resend.com (HTTPS — tidak diblokir Railway).

Env vars:
  RESEND_API_KEY = re_xxxxxxxxxxxx  (dari resend.com → API Keys)
  NOTIFY_EMAIL   = ditnug@gmail.com
"""

import os
import re
import requests
from datetime import datetime

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
NOTIFY_EMAIL   = os.getenv("NOTIFY_EMAIL", os.getenv("GMAIL_USER", ""))
GITHUB_TOKEN   = ""
GITHUB_REPO    = ""
GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")


def is_notifier_ready() -> bool:
    return bool(RESEND_API_KEY and NOTIFY_EMAIL)


def _extract_subject(text: str) -> str:
    for line in text.split("\n"):
        clean = line.strip().lstrip("*").rstrip("*").strip()
        clean = re.sub(r"[^\w\s\-–|:()%+./,]", "", clean).strip()
        if clean:
            return clean[:80]
    return "PPBIB Notifikasi"


def _to_html(text: str) -> str:
    lines  = text.split("\n")
    output = []
    for line in lines:
        line = re.sub(r"\*([^*]+)\*", r"<b>\1</b>", line)
        line = re.sub(r"_([^_]+)_",   r"<i>\1</i>", line)
        if line.strip() == "━━━━━━━━━━━━━━━━━━━━━━":
            output.append("<hr style='border:1px solid #ddd'>")
        elif line.strip() == "":
            output.append("<br>")
        else:
            output.append(line + "<br>")
    body = "\n".join(output)
    return f"""<html><body style="font-family:monospace;font-size:14px;
        background:#f9f9f9;padding:16px">
      <div style="max-width:600px;background:#fff;padding:20px;
          border-radius:8px;border:1px solid #e0e0e0">{body}</div>
    </body></html>"""


def send_notification(message: str, subject: str | None = None) -> bool:
    return _send(message, subject) is None


def _send(message: str, subject: str | None = None) -> str | None:
    if not RESEND_API_KEY:
        return "RESEND_API_KEY belum diset di Railway Variables"
    if not NOTIFY_EMAIL:
        return "NOTIFY_EMAIL belum diset di Railway Variables"

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "from":    "PPBIB Bot <onboarding@resend.dev>",
                "to":      [NOTIFY_EMAIL],
                "subject": subject or _extract_subject(message),
                "text":    message,
                "html":    _to_html(message),
            },
            timeout=15,
        )
        if resp.status_code in (200, 201):
            print(f"[Notifier] Email terkirim ke {NOTIFY_EMAIL} via Resend")
            return None
        err = f"Resend HTTP {resp.status_code}: {resp.text[:200]}"
        print(f"[Notifier] {err}")
        return err
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        print(f"[Notifier] {err}")
        return err
