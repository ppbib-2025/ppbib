"""
Notifikasi via GitHub Issues API (HTTPS — tidak diblokir Railway).

Setiap notifikasi = 1 GitHub Issue baru di repo.
GitHub otomatis kirim email ke pemilik/watcher repo.

Env vars:
  GITHUB_NOTIFY_TOKEN = ghp_xxxxxxxxxxxx  (Personal Access Token, scope: repo)
  GITHUB_NOTIFY_REPO  = ppbib-2025/ppbib
  NOTIFY_EMAIL        = (tidak dipakai, tapi tetap ada untuk kompatibilitas)
"""

import os
import re
import requests
from datetime import datetime

GITHUB_TOKEN   = os.getenv("GITHUB_NOTIFY_TOKEN", "")
GITHUB_REPO    = os.getenv("GITHUB_NOTIFY_REPO", "ppbib-2025/ppbib")
NOTIFY_EMAIL   = os.getenv("NOTIFY_EMAIL", "")
GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")


def is_notifier_ready() -> bool:
    return bool(GITHUB_TOKEN and GITHUB_REPO)


def _extract_subject(text: str) -> str:
    for line in text.split("\n"):
        clean = line.strip().lstrip("*").rstrip("*").strip()
        clean = re.sub(r"[^\w\s\-–|:()%+./,]", "", clean).strip()
        if clean:
            return clean[:80]
    return "PPBIB Notifikasi"


def _to_markdown(text: str) -> str:
    """Konversi format pesan ke Markdown GitHub."""
    lines  = text.split("\n")
    output = []
    for line in lines:
        line = re.sub(r"\*([^*]+)\*", r"**\1**", line)   # *bold* → **bold**
        line = re.sub(r"_([^_]+)_",   r"*\1*",   line)   # _italic_ → *italic*
        if line.strip() == "━━━━━━━━━━━━━━━━━━━━━━":
            output.append("---")
        else:
            output.append(line)
    return "\n".join(output)


def send_notification(message: str, subject: str | None = None) -> bool:
    """Buat GitHub Issue sebagai notifikasi. Return True jika berhasil."""
    return _send(message, subject) is None


def _send(message: str, subject: str | None = None) -> str | None:
    """Buat Issue di GitHub repo. Return None jika sukses, string error jika gagal."""
    if not GITHUB_TOKEN:
        return "GITHUB_NOTIFY_TOKEN belum diset di Railway Variables"
    if not GITHUB_REPO:
        return "GITHUB_NOTIFY_REPO belum diset di Railway Variables"

    title = subject or _extract_subject(message)
    body  = _to_markdown(message)
    now   = datetime.now().strftime("%d %b %Y %H:%M")

    # Label otomatis berdasarkan konten
    labels = ["bot-notif"]
    if "Trading" in title or "trading" in title:
        labels.append("trading-sim")
    elif "Screener" in title or "screener" in title:
        labels.append("screener")

    try:
        resp = requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/issues",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept":        "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "title": f"[{now}] {title}",
                "body":  body,
                "labels": labels,
            },
            timeout=15,
        )
        if resp.status_code == 201:
            issue_url = resp.json().get("html_url", "")
            print(f"[Notifier] Issue dibuat: {issue_url}")
            return None
        err = f"GitHub API HTTP {resp.status_code}: {resp.text[:200]}"
        print(f"[Notifier] {err}")
        return err
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        print(f"[Notifier] {err}")
        return err
