"""
Entry point: jalankan dengan `python main.py`
"""
import os
import threading
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify

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

WA_NUMBER = os.getenv("WHATSAPP_NUMBER", "")
REPORT_WA_NUMBER = os.getenv("REPORT_WA_NUMBER", WA_NUMBER)
VIDEO_ENABLED = bool(os.getenv("FAL_KEY"))
TIKTOK_ENABLED = bool(load_token())


def _send_wa(msg: str, label: str):
    if REPORT_WA_NUMBER and is_wa_connected():
        ok = send_whatsapp(REPORT_WA_NUMBER, msg)
        print(f"[WA] {label}: {'terkirim' if ok else 'GAGAL'}")
    else:
        print(f"[WA] Skip {label} (WA tidak terhubung).")


# ── Bot TikTok ────────────────────────────────────────────────────────────────

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


# ── Analytics ───────────────────────────────────────────────────────────────

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


# ── Content Generator ─────────────────────────────────────────────────────

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


# ── Video Producer ───────────────────────────────────────────────────────────

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


# ── Lead Analyzer ────────────────────────────────────────────────────────────

def job_analyze_leads():
    print("[LeadAnalyzer] Memulai analisis lead...")
    try:
        from src.lead_analyzer import analyze_leads, format_lead_report
        leads = analyze_leads()
        report = format_lead_report(leads)
        print(report)
        _send_wa(report, "Analisis lead")
    except Exception as e:
        print(f"[LeadAnalyzer] ERROR: {e}")


# ── Flask trigger API ─────────────────────────────────────────────────────────

app = Flask(__name__)

JOBS = {
    "lead":      job_analyze_leads,
    "daily":     job_daily_report,
    "weekly":    job_weekly_report,
    "content":   job_generate_content,
    "reminder":  job_daily_content_reminder,
    "analytics": job_collect_analytics,
    "video":     job_produce_video,
}


@app.get("/")
def index():
    return jsonify({
        "status": "ok",
        "trigger_url": "/trigger/<job>",
        "jobs": list(JOBS.keys()),
    })


@app.route("/trigger/<job_name>", methods=["GET", "POST"])
def trigger(job_name):
    fn = JOBS.get(job_name)
    if not fn:
        return jsonify({"error": f"Job '{job_name}' tidak ada. Pilihan: {list(JOBS.keys())}"}), 404
    threading.Thread(target=fn, daemon=True).start()
    return jsonify({"ok": True, "job": job_name, "status": "started"})


@app.get("/debug/lead")
def debug_lead():
    """Tampilkan hasil analisis lead langsung di browser (tidak kirim WA)."""
    try:
        from src.lead_analyzer import analyze_leads, format_lead_report
        from src.whatsapp import is_wa_connected
        wa_status = is_wa_connected()
        leads = analyze_leads()
        report = format_lead_report(leads)
        return jsonify({
            "wa_connected": wa_status,
            "lead_count": len(leads),
            "leads": leads,
            "report_preview": report[:500],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/debug/status")
def debug_status():
    """Cek status koneksi WA dan env vars."""
    from src.whatsapp import is_wa_connected
    return jsonify({
        "wa_connected": is_wa_connected(),
        "wa_number": REPORT_WA_NUMBER or "BELUM DISET",
        "dinoiki_key": "SET" if os.getenv("DINOIKI_API_KEY") else "TIDAK ADA",
        "whatsapp_url": os.getenv("WHATSAPP_URL", "http://ppbib.railway.internal:3000"),
    })


# ── Main ────────────────────────────────────────────────────────────────────

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

    scheduler = BackgroundScheduler(timezone="Asia/Jakarta")

    scheduler.add_job(job_scan,     "interval", minutes=15, id="scan")
    scheduler.add_job(job_followup, "interval", hours=6,    id="followup")

    scheduler.add_job(job_collect_analytics,      "cron", hour=19, minute=0,                    id="analytics_collect")
    scheduler.add_job(job_daily_report,           "cron", hour=20, minute=0,                    id="analytics_daily")
    scheduler.add_job(job_weekly_report,          "cron", day_of_week="mon", hour=7, minute=0,  id="analytics_weekly")
    scheduler.add_job(job_daily_content_reminder, "cron", hour=7,  minute=0,                    id="content_reminder")
    scheduler.add_job(job_generate_content,       "cron", day_of_week="sun", hour=18, minute=0, id="content_generate")
    scheduler.add_job(job_produce_video,          "cron", hour=8,  minute=0,                    id="video_produce")
    scheduler.add_job(job_analyze_leads,          "cron", hour=21, minute=0,                    id="lead_analyze")

    scheduler.start()

    print("Scheduler aktif:")
    print("  - Snapshot metrics  : tiap hari 19:00")
    print("  - Laporan harian WA : tiap hari 20:00")
    print("  - Laporan mingguan  : Senin 07:00")
    print("  - Reminder konten   : tiap hari 07:00")
    print("  - Generate konten   : Minggu 18:00")
    print("  - Analisis lead WA  : tiap hari 21:00")
    if TIKTOK_ENABLED:
        print("  - Scan komentar TikTok : tiap 15 menit")
    if VIDEO_ENABLED:
        print("  - Produksi video : tiap hari 08:00")
    print()
    print("Trigger manual: POST /trigger/<job>")
    print("Bot berjalan...")

    PORT = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=PORT)
