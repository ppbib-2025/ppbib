"""
Main bot: scan komentar, reply, catat leads, jadwalkan follow-up.
"""
import time
from datetime import datetime, timedelta

from src.tiktok_api import get_my_videos, get_comments, reply_comment
from src.crm import add_lead, update_status, get_leads_by_status
from templates.funnel import is_interested, reply_komentar, followup_d1, followup_d3, followup_d7

REPLIED_FILE = "data/replied_comments.txt"


def load_replied() -> set:
    try:
        with open(REPLIED_FILE) as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()


def mark_replied(comment_id: str):
    with open(REPLIED_FILE, "a") as f:
        f.write(comment_id + "\n")


def scan_and_reply():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning komentar...")
    replied = load_replied()
    videos = get_my_videos()

    for video in videos:
        video_id = video["id"]
        result = get_comments(video_id)
        comments = result.get("data", {}).get("comments", [])

        for comment in comments:
            cid = comment["id"]
            if cid in replied:
                continue

            text = comment.get("text", "")
            username = comment.get("username", "user")

            if is_interested(text):
                print(f"  → Komentar berminat dari @{username}: {text[:50]}")
                reply = reply_komentar(username)
                reply_comment(video_id, cid, reply)
                mark_replied(cid)
                add_lead(username, video_id, text)
                print(f"  ✓ Reply terkirim, lead disimpan.")

    print("Scan selesai.")


def run_followups(wa_number: str):
    now = datetime.now()

    # Follow-up D1
    for lead in get_leads_by_status("dm_sent"):
        created = datetime.fromisoformat(lead["created_at"])
        if now - created >= timedelta(days=1):
            msg = followup_d1(lead["username"])
            print(f"[FU D1] {lead['username']}: {msg[:60]}...")
            update_status(lead["username"], "followup_d1", "Follow-up D1 dikirim")

    # Follow-up D3
    for lead in get_leads_by_status("followup_d1"):
        last = datetime.fromisoformat(lead["last_contact"])
        if now - last >= timedelta(days=2):
            msg = followup_d3(lead["username"], wa_number)
            print(f"[FU D3] {lead['username']}: {msg[:60]}...")
            update_status(lead["username"], "followup_d3", "Follow-up D3 dikirim")

    # Follow-up D7
    for lead in get_leads_by_status("followup_d3"):
        last = datetime.fromisoformat(lead["last_contact"])
        if now - last >= timedelta(days=4):
            msg = followup_d7(lead["username"], wa_number)
            print(f"[FU D7] {lead['username']}: {msg[:60]}...")
            update_status(lead["username"], "followup_d7", "Follow-up D7 dikirim")
