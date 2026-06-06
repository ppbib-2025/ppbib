"""
Entry point: jalankan dengan `python main.py`
"""
import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

from src.bot import scan_and_reply, run_followups
from src.tiktok_auth import get_auth_url, load_token
from src.analytics import collect_tiktok_metrics, collect_instagram_metrics, generate_report

WA_NUMBER = os.getenv("WHATSAPP_NUMBER", "")


def job_scan():
    scan_and_reply()


def job_followup():
    run_followups(WA_NUMBER)


def job_collect_analytics():
    """Snapshot metrics harian TikTok + Instagram."""
    print("[Analytics] Mengambil metrics harian...")
    collect_tiktok_metrics()
    collect_instagram_metrics()


def job_weekly_report():
    """Buat laporan mingguan dan print ke console (bisa diarahkan ke WhatsApp/email)."""
    print("[Analytics] Membuat laporan mingguan...")
    report = generate_report()
    print(report)


if __name__ == "__main__":
    token = load_token()
    if not token:
        print("=" * 50)
        print("TOKEN TIKTOK BELUM ADA. Buka URL ini di browser untuk login TikTok:")
        print(get_auth_url())
        print("=" * 50)
        print("Setelah login, jalankan: python setup_token.py <code_dari_url>")
    else:
        print("Token ditemukan. Bot berjalan...")
        scheduler = BlockingScheduler()

        # Bot comment
        scheduler.add_job(job_scan, "interval", minutes=15, id="scan")
        scheduler.add_job(job_followup, "interval", hours=6, id="followup")

        # Analytics: snapshot harian jam 23:00, laporan mingguan tiap Senin jam 07:00
        scheduler.add_job(job_collect_analytics, "cron", hour=23, minute=0, id="analytics_daily")
        scheduler.add_job(job_weekly_report, "cron", day_of_week="mon", hour=7, minute=0, id="analytics_report")

        print("Scheduler aktif:")
        print("  - Scan komentar  : tiap 15 menit")
        print("  - Follow-up lead : tiap 6 jam")
        print("  - Snapshot metrics: tiap hari jam 23:00")
        print("  - Laporan mingguan: tiap Senin jam 07:00")
        scheduler.start()
