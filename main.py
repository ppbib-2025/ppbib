"""
Entry point: jalankan dengan `python main.py`
"""
import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

from src.bot import scan_and_reply, run_followups
from src.tiktok_auth import get_auth_url, load_token

WA_NUMBER = os.getenv("WHATSAPP_NUMBER", "")


def job_scan():
    scan_and_reply()


def job_followup():
    run_followups(WA_NUMBER)


if __name__ == "__main__":
    token = load_token()
    if not token:
        print("=" * 50)
        print("TOKEN BELUM ADA. Buka URL ini di browser untuk login TikTok:")
        print(get_auth_url())
        print("=" * 50)
        print("Setelah login, jalankan: python setup_token.py <code_dari_url>")
    else:
        print("Token ditemukan. Bot berjalan...")
        scheduler = BlockingScheduler()
        scheduler.add_job(job_scan, "interval", minutes=15, id="scan")
        scheduler.add_job(job_followup, "interval", hours=6, id="followup")
        print("Scheduler aktif: scan tiap 15 menit, follow-up tiap 6 jam.")
        scheduler.start()
