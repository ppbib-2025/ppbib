"""
Entry point: jalankan dengan `python main.py`
Flask webhook (port 5000) + APScheduler background jobs.
"""
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

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
from src.video_producer import produce_todays_video, format_video_ready_wa
from src.whatsapp import send_whatsapp, is_wa_connected
from src.wa_handler import handle_incoming, run_wa_followups

WA_NUMBER       = os.getenv("WHATSAPP_NUMBER", "")
REPORT_WA_NUMBER = os.getenv("REPORT_WA_NUMBER", WA_NUMBER)
VIDEO_ENABLED   = bool(os.getenv("FAL_KEY"))
TIKTOK_ENABLED  = bool(load_token())
FLASK_PORT      = int(os.getenv("FLASK_PORT", "5000"))

app = Flask(__name__)


# ── Flask webhook ─────────────────────────────────────────────────────────────

@app.route("/wa/incoming", methods=["POST"])
def wa_incoming():
    """
    Endpoint yang dipanggil oleh whatsapp/bot.js setiap ada pesan masuk.
    Body JSON: { "phone": "628xxx", "message": "teks pesan" }
    """
    data = request.get_json(silent=True) or {}
    phone   = data.get("phone", "").strip()
    message = data.get("message", "").strip()

    if not phone or not message:
        return jsonify({"error": "phone dan message wajib"}), 400

    handle_incoming(phone, message)
    return jsonify({"ok": True})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ── Scheduled jobs ────────────────────────────────────────────────────────────

def _send_wa(msg: str, label: str):
    if REPORT_WA_NUMBER and is_wa_connected():
        ok = send_whatsapp(REPORT_WA_NUMBER, msg)
        print(f"[WA] {label}: {'terkirim' if ok else 'GAGAL'}")
    else:
        print(f"[WA] Skip {label} (WA tidak terhubung).")


def job_scan():
    if not TIKTOK_ENABLED:
        return
    from src.bot import scan_and_reply
    scan_and_reply()


def job_followup():
    """Follow-up WA via Coze (Rina) untuk semua lead yang idle."""
    run_wa_followups()
    if TIKTOK_ENABLED:
        from src.bot import run_followups
        run_followups(WA_NUMBER)


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


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("PPBIB Bot mulai...")
    print(f"  TikTok   : {'AKTIF' if TIKTOK_ENABLED else 'NONAKTIF'}")
    print(f"  Video AI : {'AKTIF' if VIDEO_ENABLED else 'NONAKTIF'}")
    print(f"  WA Report: {REPORT_WA_NUMBER or 'BELUM DISET'}")
    coze_ok = bool(os.getenv("COZE_API_KEY") and os.getenv("COZE_BOT_ID"))
    print(f"  Coze/Rina: {'AKTIF' if coze_ok else 'NONAKTIF (set COZE_API_KEY + COZE_BOT_ID)'}")
    print("=" * 55)

    if not TIKTOK_ENABLED:
        print("[INFO] TikTok token tidak ditemukan — bot tetap jalan tanpa TikTok.")
        print("[INFO] Untuk setup TikTok nanti, buka URL ini di browser:")
        print(get_auth_url())
        print()

    scheduler = BackgroundScheduler()

    scheduler.add_job(job_scan,     "interval", minutes=15, id="scan")
    scheduler.add_job(job_followup, "interval", hours=6,    id="followup")

    scheduler.add_job(job_collect_analytics,      "cron", hour=19, minute=0,                    id="analytics_collect")
    scheduler.add_job(job_daily_report,           "cron", hour=20, minute=0,                    id="analytics_daily")
    scheduler.add_job(job_weekly_report,          "cron", day_of_week="mon", hour=7, minute=0,  id="analytics_weekly")
    scheduler.add_job(job_daily_content_reminder, "cron", hour=7,  minute=0,                    id="content_reminder")
    scheduler.add_job(job_generate_content,       "cron", day_of_week="sun", hour=18, minute=0, id="content_generate")
    scheduler.add_job(job_produce_video,          "cron", hour=8,  minute=0,                    id="video_produce")

    scheduler.start()

    print("Scheduler aktif:")
    print("  - Follow-up WA (Coze)  : tiap 6 jam")
    print("  - Snapshot metrics     : tiap hari 19:00")
    print("  - Laporan harian WA    : tiap hari 20:00")
    print("  - Laporan mingguan     : Senin 07:00")
    print("  - Reminder konten      : tiap hari 07:00")
    print("  - Generate konten      : Minggu 18:00")
    if TIKTOK_ENABLED:
        print("  - Scan komentar TikTok : tiap 15 menit")
    if VIDEO_ENABLED:
        print("  - Produksi video       : tiap hari 08:00")
    print()
    print(f"Flask webhook berjalan di http://0.0.0.0:{FLASK_PORT}")
    print("  POST /wa/incoming  — terima pesan masuk WA")
    print("  GET  /health       — health check")
    print()
    print("Bot berjalan... (Ctrl+C untuk berhenti)")

    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
