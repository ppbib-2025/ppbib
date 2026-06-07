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
from src.video_producer import produce_todays_video, format_video_ready_wa
from src.whatsapp import send_whatsapp, is_wa_connected

WA_NUMBER = os.getenv("WHATSAPP_NUMBER", "")
REPORT_WA_NUMBER = os.getenv("REPORT_WA_NUMBER", WA_NUMBER)
HIGGSFIELD_ENABLED = bool(os.getenv("HIGGSFIELD_API_KEY"))


def _send_wa(msg: str, label: str):
    if REPORT_WA_NUMBER and is_wa_connected():
        ok = send_whatsapp(REPORT_WA_NUMBER, msg)
        print(f"[WA] {label}: {'terkirim' if ok else 'GAGAL'}")
    else:
        print(f"[WA] Skip {label} (nomor kosong atau WA tidak terhubung).")


# ── Bot ──────────────────────────────────────────────────────────────────

def job_scan():
    scan_and_reply()

def job_followup():
    run_followups(WA_NUMBER)


# ── Analytics ───────────────────────────────────────────────────────────────

def job_collect_analytics():
    print("[Analytics] Snapshot harian...")
    collect_tiktok_metrics()
    collect_instagram_metrics()
    collect_facebook_metrics()

def job_daily_report():
    report = generate_daily_report()
    print(report)
    _send_wa(report, "Laporan harian")

def job_weekly_report():
    report = generate_weekly_report()
    print(report)
    _send_wa(report, "Laporan mingguan")


# ── Content Generator ───────────────────────────────────────────────────────

def job_generate_content():
    """Minggu 18:00 — generate rencana konten 1 minggu via Claude."""
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
    """07:00 — kirim script + caption hari ini ke WA."""
    content = get_todays_content()
    if content:
        msg = format_today_for_whatsapp(content)
        print(msg)
        _send_wa(msg, "Reminder konten harian")
    else:
        print("[Content] Tidak ada konten terjadwal hari ini.")


# ── Video Producer (Higgsfield) ──────────────────────────────────────────────

def job_produce_video():
    """
    08:00 — generate video hari ini via Higgsfield (jika API key di-set).
    Berjalan di background, WA dikirim saat video selesai (~5-10 menit).
    """
    if not HIGGSFIELD_ENABLED:
        print("[Video] Skip: HIGGSFIELD_API_KEY belum di-set.")
        return
    print("[Video] Memulai produksi video harian via Higgsfield...")
    try:
        info = produce_todays_video()
        if info:
            msg = format_video_ready_wa(info)
            print(msg)
            _send_wa(msg, "Video siap upload")
        else:
            print("[Video] Tidak ada video untuk diproduksi hari ini.")
    except Exception as e:
        print(f"[Video] ERROR: {e}")
        _send_wa(f"⚠️ Higgsfield error: {e}", "Error video producer")


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    token = load_token()
    if not token:
        print("=" * 50)
        print("TOKEN TIKTOK BELUM ADA. Buka URL ini di browser:")
        print(get_auth_url())
        print("=" * 50)
        print("Setelah login: python setup_token.py <code>")
    else:
        print("Token ditemukan. Bot berjalan...")
        higgsfield_status = "AKTIF" if HIGGSFIELD_ENABLED else "NONAKTIF (set HIGGSFIELD_API_KEY untuk aktifkan)"

        scheduler = BlockingScheduler()

        # Bot
        scheduler.add_job(job_scan,     "interval", minutes=15, id="scan")
        scheduler.add_job(job_followup, "interval", hours=6,    id="followup")

        # Analytics
        scheduler.add_job(job_collect_analytics, "cron", hour=19, minute=0,                   id="analytics_collect")
        scheduler.add_job(job_daily_report,      "cron", hour=20, minute=0,                   id="analytics_daily")
        scheduler.add_job(job_weekly_report,     "cron", day_of_week="mon", hour=7, minute=0, id="analytics_weekly")

        # Content
        scheduler.add_job(job_daily_content_reminder, "cron", hour=7,  minute=0,                    id="content_reminder")
        scheduler.add_job(job_generate_content,       "cron", day_of_week="sun", hour=18, minute=0, id="content_generate")

        # Video (Higgsfield)
        scheduler.add_job(job_produce_video, "cron", hour=8, minute=0, id="video_produce")

        print("Scheduler aktif:")
        print("  Bot:")
        print("    Scan komentar         : tiap 15 menit")
        print("    Follow-up lead        : tiap 6 jam")
        print("  Analytics (TikTok+IG+FB):")
        print("    Snapshot metrics      : tiap hari 19:00")
        print("    Laporan harian WA     : tiap hari 20:00")
        print("    Laporan mingguan WA   : Senin 07:00")
        print("  Konten:")
        print("    Reminder script+caption: tiap hari 07:00")
        print("    Generate rencana konten: Minggu 18:00 (Claude AI)")
        print(f"  Video Higgsfield [{higgsfield_status}]:")
        print("    Produksi video harian : tiap hari 08:00")
        scheduler.start()
