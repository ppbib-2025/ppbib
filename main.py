"""
Entry point: jalankan dengan `python main.py`
"""
import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

from src.bot import scan_and_reply, run_followups
from src.tiktok_auth import get_auth_url, load_token
from src.analytics import (
    collect_tiktok_metrics,
    collect_instagram_metrics,
    generate_daily_report,
    generate_weekly_report,
)
from src.whatsapp import send_whatsapp, is_wa_connected

WA_NUMBER = os.getenv("WHATSAPP_NUMBER", "")
REPORT_WA_NUMBER = os.getenv("REPORT_WA_NUMBER", WA_NUMBER)  # nomor penerima laporan


def job_scan():
    scan_and_reply()


def job_followup():
    run_followups(WA_NUMBER)


def job_collect_analytics():
    """Snapshot metrics harian TikTok + Instagram (jam 19:00)."""
    print("[Analytics] Mengambil metrics harian...")
    collect_tiktok_metrics()
    collect_instagram_metrics()


def job_daily_report():
    """
    Laporan harian ringkas dikirim via WhatsApp tiap malam jam 20:00.
    Snapshot diambil 1 jam sebelumnya (job_collect_analytics jam 19:00).
    """
    print("[Analytics] Membuat laporan harian...")
    report = generate_daily_report()
    print(report)

    if REPORT_WA_NUMBER and is_wa_connected():
        ok = send_whatsapp(REPORT_WA_NUMBER, report)
        print(f"[WA] Laporan harian {'terkirim' if ok else 'GAGAL'} ke {REPORT_WA_NUMBER}")
    else:
        print("[WA] Skip kirim WA (nomor kosong atau WA tidak terhubung).")


def job_weekly_report():
    """
    Laporan mingguan lengkap dikirim via WhatsApp tiap Senin jam 07:00.
    """
    print("[Analytics] Membuat laporan mingguan...")
    report = generate_weekly_report()
    print(report)

    if REPORT_WA_NUMBER and is_wa_connected():
        ok = send_whatsapp(REPORT_WA_NUMBER, report)
        print(f"[WA] Laporan mingguan {'terkirim' if ok else 'GAGAL'} ke {REPORT_WA_NUMBER}")
    else:
        print("[WA] Skip kirim WA (nomor kosong atau WA tidak terhubung).")


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

        # Bot komentar & follow-up
        scheduler.add_job(job_scan,     "interval", minutes=15, id="scan")
        scheduler.add_job(job_followup, "interval", hours=6,    id="followup")

        # Analytics pipeline:
        #   19:00 → snapshot metrics (TikTok + IG)
        #   20:00 → kirim laporan harian via WA
        #   Senin 07:00 → kirim laporan mingguan via WA
        scheduler.add_job(job_collect_analytics, "cron", hour=19, minute=0,  id="analytics_collect")
        scheduler.add_job(job_daily_report,      "cron", hour=20, minute=0,  id="analytics_daily")
        scheduler.add_job(job_weekly_report,     "cron", day_of_week="mon", hour=7, minute=0, id="analytics_weekly")

        print("Scheduler aktif:")
        print("  - Scan komentar    : tiap 15 menit")
        print("  - Follow-up lead   : tiap 6 jam")
        print("  - Snapshot metrics : tiap hari jam 19:00")
        print("  - Laporan HARIAN   : tiap hari jam 20:00 (via WhatsApp)")
        print("  - Laporan MINGGUAN : tiap Senin jam 07:00 (via WhatsApp)")
        scheduler.start()
