"""
Entry point: jalankan dengan `python main.py`
Flask dashboard jalan di thread terpisah; scheduler jalan di main thread.
"""
import os
import threading
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

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
from src.auto_research import run_weekly_evaluation
from src.video_producer import produce_todays_video, format_video_ready_wa
from src.whatsapp import send_whatsapp, is_wa_connected
from src.dashboard import app as flask_app
from src.stock_screener import run_screen, format_screen_report
from src.trading_sim import run_daily_trading, format_trading_report, reset_simulation

WA_NUMBER        = os.getenv("WHATSAPP_NUMBER", "")
REPORT_WA_NUMBER = os.getenv("REPORT_WA_NUMBER", WA_NUMBER)
VIDEO_ENABLED    = bool(os.getenv("FAL_KEY"))
TIKTOK_ENABLED   = bool(load_token())
STOCK_SCREEN_ENABLED  = bool(os.getenv("STOCK_SCREEN_ENABLED", "true"))
TRADING_SIM_ENABLED   = bool(os.getenv("TRADING_SIM_ENABLED", "true"))


def _send_wa(msg: str, label: str):
    if REPORT_WA_NUMBER and is_wa_connected():
        ok = send_whatsapp(REPORT_WA_NUMBER, msg)
        print(f"[WA] {label}: {'terkirim' if ok else 'GAGAL'}")
    else:
        print(f"[WA] Skip {label} (WA tidak terhubung).")


# ── Bot TikTok ────────────────────────────────────────────

def job_scan():
    if not TIKTOK_ENABLED:
        return
    from src.bot import scan_and_reply
    scan_and_reply()


def job_followup():
    if not TIKTOK_ENABLED:
        return
    from src.bot import run_followups
    run_followups(WA_NUMBER)


# ── Analytics ───────────────────────────────────────────

def job_collect_analytics():
    print("[Analytics] Snapshot harian...")
    if TIKTOK_ENABLED:
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


# ── Auto Research ─────────────────────────────────────────

def job_auto_research():
    """Sabtu 17:00 — evaluasi performa minggu ini, update strategi untuk minggu depan."""
    print("[AutoResearch] Evaluasi performa konten minggu ini...")
    try:
        insights = run_weekly_evaluation()
        iteration = insights.get("iteration", "?")
        wa_summary = insights.get("wa_summary", "Auto research selesai.")
        patterns = insights.get("top_performing_patterns", {})
        winning = ", ".join(patterns.get("winning_topics", [])[:2])
        msg = (
            f"\U0001f52c *Auto Research PPBIB — Iterasi #{iteration}*\n\n"
            f"{wa_summary}\n\n"
            f"\U0001f3af Topik pemenang: {winning or '-'}\n"
            f"_Strategi konten minggu depan sudah diperbarui._"
        )
        _send_wa(msg, "Auto research insights")
    except Exception as e:
        print(f"[AutoResearch] ERROR: {e}")
        _send_wa(f"⚠️ Auto research gagal: {e}", "Error auto research")


# ── Content Generator ────────────────────────────────────────

def job_generate_content():
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
    content = get_todays_content()
    if content:
        msg = format_today_for_whatsapp(content)
        print(msg)
        _send_wa(msg, "Reminder konten harian")
    else:
        print("[Content] Tidak ada konten terjadwal hari ini.")


# ── Trading Simulation ──────────────────────────────────────

def job_trading_sim():
    """Senin-Jumat 09:05 WIB — analisa & eksekusi simulasi trading."""
    if not TRADING_SIM_ENABLED:
        return
    print("[TradingSim] Menjalankan simulasi trading Momentum Dip...")
    try:
        result = run_daily_trading()
        report = format_trading_report(result)
        print(report)
        _send_wa(report, "Simulasi trading harian")
    except Exception as e:
        print(f"[TradingSim] ERROR: {e}")
        _send_wa(f"⚠️ Simulasi trading gagal: {e}", "Error trading sim")


# ── Stock Screener ───────────────────────────────────────────

def job_stock_screen():
    """Senin-Jumat 08:30 — screening saham IDX dengan BoW + Piotroski + Magic Formula."""
    if not STOCK_SCREEN_ENABLED:
        return
    print("[Screener] Menjalankan screening saham IDX...")
    try:
        results = run_screen()
        report  = format_screen_report(results)
        print(report)
        _send_wa(report, "Screening saham IDX")
    except Exception as e:
        print(f"[Screener] ERROR: {e}")
        _send_wa(f"⚠️ Screener saham gagal: {e}", "Error screener")


# ── Video Producer ────────────────────────────────────────────

def job_produce_video():
    if not VIDEO_ENABLED:
        return
    print("[Video] Produksi video harian via Seedance...")
    try:
        info = produce_todays_video()
        if info:
            msg = format_video_ready_wa(info)
            print(msg)
            _send_wa(msg, "Video siap upload")
    except Exception as e:
        print(f"[Video] ERROR: {e}")
        _send_wa(f"⚠️ Seedance error: {e}", "Error video producer")


# ── Main ────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("PPBIB Bot mulai...")
    print(f"  TikTok   : {'AKTIF' if TIKTOK_ENABLED else 'NONAKTIF (setup token dulu)'}")
    print(f"  Video AI : {'AKTIF' if VIDEO_ENABLED else 'NONAKTIF (set FAL_KEY untuk aktifkan)'}")
    print(f"  WA Report: {REPORT_WA_NUMBER or 'BELUM DISET'}")
    print("=" * 50)

    if not TIKTOK_ENABLED:
        print("[INFO] TikTok token tidak ditemukan — bot tetap jalan tanpa TikTok.")
        print("[INFO] Untuk setup TikTok nanti, buka URL ini di browser:")
        print(get_auth_url())
        print()

    # Jalankan Flask di background thread
    port = int(os.getenv("PORT", 8080))
    flask_thread = threading.Thread(
        target=lambda: flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False),
        daemon=True,
        name="flask-dashboard",
    )
    flask_thread.start()
    print(f"[Dashboard] Analytics tersedia di http://localhost:{port}/analytics")

    scheduler = BlockingScheduler()

    scheduler.add_job(job_scan,     "interval", minutes=15, id="scan")
    scheduler.add_job(job_followup, "interval", hours=6,    id="followup")

    scheduler.add_job(job_trading_sim,  "cron", day_of_week="mon-fri", hour=9, minute=5,  id="trading_sim")
    scheduler.add_job(job_stock_screen, "cron", day_of_week="mon-fri", hour=8, minute=30, id="stock_screen")
    scheduler.add_job(job_collect_analytics,      "cron", hour=19, minute=0,                    id="analytics_collect")
    scheduler.add_job(job_daily_report,           "cron", hour=20, minute=0,                    id="analytics_daily")
    scheduler.add_job(job_weekly_report,          "cron", day_of_week="mon", hour=7,  minute=0, id="analytics_weekly")
    scheduler.add_job(job_daily_content_reminder, "cron", hour=7,  minute=0,                    id="content_reminder")
    scheduler.add_job(job_auto_research,          "cron", day_of_week="sat", hour=17, minute=0, id="auto_research")
    scheduler.add_job(job_generate_content,       "cron", day_of_week="sun", hour=18, minute=0, id="content_generate")
    scheduler.add_job(job_produce_video,          "cron", hour=8,  minute=0,                    id="video_produce")

    print(f"  Stock Screener: {'AKTIF' if STOCK_SCREEN_ENABLED else 'NONAKTIF'}")
    print(f"  Trading Sim   : {'AKTIF' if TRADING_SIM_ENABLED else 'NONAKTIF (set TRADING_SIM_ENABLED=false)'}")
    print("=" * 50)

    print("Scheduler aktif:")
    print("  - Simulasi trading     : Senin-Jumat 09:05 (buka bursa)")
    print("  - Screener saham IDX   : Senin-Jumat 08:30")
    print("  - Snapshot metrics    : tiap hari 19:00")
    print("  - Laporan harian WA   : tiap hari 20:00")
    print("  - Laporan mingguan    : Senin 07:00")
    print("  - Reminder konten     : tiap hari 07:00")
    print("  - Auto research       : Sabtu 17:00")
    print("  - Generate konten     : Minggu 18:00")
    if TIKTOK_ENABLED:
        print("  - Scan komentar TikTok: tiap 15 menit")
    if VIDEO_ENABLED:
        print("  - Produksi video      : tiap hari 08:00")
    print()
    print("Bot berjalan... (Ctrl+C untuk berhenti)")
    scheduler.start()
