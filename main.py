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
    collect_facebook_metrics,
    generate_daily_report,
    generate_weekly_report,
)
from src.content_generator import (
    generate_weekly_plan,
    format_plan_for_whatsapp,
    get_todays_content,
    format_today_for_whatsapp,
)
from src.whatsapp import send_whatsapp, is_wa_connected

WA_NUMBER = os.getenv("WHATSAPP_NUMBER", "")
REPORT_WA_NUMBER = os.getenv("REPORT_WA_NUMBER", WA_NUMBER)


def _send_wa(msg: str, label: str):
    if REPORT_WA_NUMBER and is_wa_connected():
        ok = send_whatsapp(REPORT_WA_NUMBER, msg)
        print(f"[WA] {label}: {'terkirim' if ok else 'GAGAL'} ke {REPORT_WA_NUMBER}")
    else:
        print(f"[WA] Skip {label} (nomor kosong atau WA tidak terhubung).")


# ── Bot Jobs ────────────────────────────────────────────────────────────────

def job_scan():
    scan_and_reply()


def job_followup():
    run_followups(WA_NUMBER)


# ── Analytics Jobs ──────────────────────────────────────────────────────────

def job_collect_analytics():
    """Snapshot metrics harian: TikTok + Instagram + Facebook (19:00)."""
    print("[Analytics] Mengambil metrics harian...")
    collect_tiktok_metrics()
    collect_instagram_metrics()
    collect_facebook_metrics()


def job_daily_report():
    """Laporan harian ringkas via WA (20:00)."""
    print("[Analytics] Membuat laporan harian...")
    report = generate_daily_report()
    print(report)
    _send_wa(report, "Laporan harian")


def job_weekly_report():
    """Laporan mingguan lengkap via WA (Senin 07:00)."""
    print("[Analytics] Membuat laporan mingguan...")
    report = generate_weekly_report()
    print(report)
    _send_wa(report, "Laporan mingguan")


# ── Content Generator Jobs ─────────────────────────────────────────────────────

def job_generate_content():
    """
    Tiap Minggu jam 18:00: ambil insight mingguan → Claude generate
    rencana konten 7 hari → kirim ringkasan ke WA.
    """
    print("[Content] Membuat rencana konten minggu depan...")
    try:
        plan = generate_weekly_plan()
        summary = format_plan_for_whatsapp(plan)
        print(summary)
        _send_wa(summary, "Rencana konten mingguan")
    except Exception as e:
        print(f"[Content] ERROR: {e}")
        _send_wa(f"⚠️ Gagal generate konten: {e}", "Error content generator")


def job_daily_content_reminder():
    """
    Tiap hari jam 07:00: kirim konten hari ini ke WA sebagai reminder posting.
    """
    content = get_todays_content()
    if content:
        msg = format_today_for_whatsapp(content)
        print(msg)
        _send_wa(msg, "Reminder konten harian")
    else:
        print("[Content] Tidak ada konten terjadwal hari ini.")


# ── Main ───────────────────────────────────────────────────────────────────────

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

        # Bot
        scheduler.add_job(job_scan,     "interval", minutes=15, id="scan")
        scheduler.add_job(job_followup, "interval", hours=6,    id="followup")

        # Analytics
        scheduler.add_job(job_collect_analytics, "cron", hour=19, minute=0,                  id="analytics_collect")
        scheduler.add_job(job_daily_report,      "cron", hour=20, minute=0,                  id="analytics_daily")
        scheduler.add_job(job_weekly_report,     "cron", day_of_week="mon", hour=7, minute=0, id="analytics_weekly")

        # Content Generator
        scheduler.add_job(job_daily_content_reminder, "cron", hour=7,  minute=0,                   id="content_reminder")
        scheduler.add_job(job_generate_content,       "cron", day_of_week="sun", hour=18, minute=0, id="content_generate")

        print("Scheduler aktif:")
        print("  Bot:")
        print("    - Scan komentar       : tiap 15 menit")
        print("    - Follow-up lead      : tiap 6 jam")
        print("  Analytics:")
        print("    - Snapshot metrics    : tiap hari 19:00 (TikTok + IG + FB)")
        print("    - Laporan harian      : tiap hari 20:00 via WA")
        print("    - Laporan mingguan    : tiap Senin 07:00 via WA")
        print("  Konten:")
        print("    - Reminder posting    : tiap hari 07:00 via WA")
        print("    - Generate konten baru: tiap Minggu 18:00 via Claude AI")
        scheduler.start()
