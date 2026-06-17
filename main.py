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
from src.video_producer import (
    produce_todays_video,
    produce_trending_video,
    format_video_ready_tg,
    format_trending_video_tg,
)
from src.trending_feed_analyzer import analyze_trending_feed, format_trending_feed_wa
from src.telegram_notifier import send_telegram, send_video_telegram, is_telegram_configured
from src.whatsapp import send_whatsapp, is_wa_connected
from src.dashboard import app as flask_app
from src.gdrive_client import (
    is_gdrive_configured,
    sync_clips_from_drive,
    upload_video as gdrive_upload,
)

WA_NUMBER        = os.getenv("WHATSAPP_NUMBER", "")
REPORT_WA_NUMBER = os.getenv("REPORT_WA_NUMBER", WA_NUMBER)
_SF_KEY          = bool(os.getenv("SILICONFLOW_API_KEY"))
try:
    from src.video_composer import has_local_clips as _has_clips
    VIDEO_ENABLED = _SF_KEY or _has_clips() or is_gdrive_configured()
except Exception:
    VIDEO_ENABLED = _SF_KEY
TIKTOK_ENABLED  = bool(load_token())


def _send_wa(msg: str, label: str):
    if REPORT_WA_NUMBER and is_wa_connected():
        ok = send_whatsapp(REPORT_WA_NUMBER, msg)
        print(f"[WA] {label}: {'terkirim' if ok else 'GAGAL'}")
    else:
        print(f"[WA] Skip {label} (WA tidak terhubung).")


def _send_tg(msg: str, label: str):
    if is_telegram_configured():
        ok = send_telegram(msg)
        print(f"[Telegram] {label}: {'terkirim' if ok else 'GAGAL'}")
    else:
        print(f"[Telegram] Skip {label} (TELEGRAM_BOT_TOKEN/CHAT_ID belum diset).")


_TG_MAX_MB = 49   # Telegram limit 50MB


def _send_tg_video(video_path: str, caption: str, label: str):
    """
    Kirim video ke Telegram.
    - Jika <= 49MB  : upload langsung (bisa diputar inline)
    - Jika > 49MB   : upload ke Google Drive, kirim link
    """
    if not is_telegram_configured():
        print(f"[Telegram] Skip {label} (token belum diset).")
        return

    size_mb = os.path.getsize(video_path) / (1024 * 1024)

    if size_mb <= _TG_MAX_MB:
        ok = send_video_telegram(video_path, caption=caption)
        print(f"[Telegram] {label}: {'terkirim' if ok else 'GAGAL'}")
        return

    # File besar → upload ke Drive, kirim link
    print(f"[Telegram] Video {size_mb:.1f} MB > 49MB — upload ke Google Drive...")
    if not is_gdrive_configured():
        send_telegram(
            f"{caption}\n\n⚠️ Video {size_mb:.0f}MB terlalu besar untuk Telegram.\n"
            f"Set `GDRIVE_OUTPUT_FOLDER_ID` untuk auto-upload ke Drive.",
        )
        return
    try:
        drive_url = gdrive_upload(video_path)
        send_telegram(
            f"{caption}\n\n📥 *Download video* (Google Drive):\n{drive_url}",
        )
        print(f"[Telegram] {label}: link Drive terkirim")
    except Exception as e:
        print(f"[Telegram/Drive] ERROR upload: {e}")
        send_telegram(f"{caption}\n\n⚠️ Gagal upload ke Drive: {e}")


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


# ── Video Producer ────────────────────────────────────────────

def job_produce_video():
    if not VIDEO_ENABLED:
        return
    print("[Video] Produksi video harian...")
    try:
        info = produce_todays_video()
        if info:
            msg = format_video_ready_tg(info)
            print(msg)
            _send_tg(msg, "Video siap upload")
            _send_tg_video(info["video_path"], caption=f"🎬 {info['topic']}", label="File video")
    except Exception as e:
        print(f"[Video] ERROR: {e}")
        _send_tg(f"⚠️ Video gagal: {e}", "Error video producer")


# ── Trending Feed + Video ────────────────────────────────

def job_analyze_trending_feed():
    """Tiap hari 10:00 — ambil sinyal tren & simpan ke trending_feed.json."""
    print("[TrendingFeed] Menganalisis tren konten hari ini...")
    try:
        feed = analyze_trending_feed()
        msg = format_trending_feed_wa(feed)
        print(msg)
        _send_tg(msg, "Trending feed harian")
    except Exception as e:
        print(f"[TrendingFeed] ERROR: {e}")
        _send_tg(f"⚠️ Trending feed gagal: {e}", "Error trending feed")


def job_produce_trending_video():
    """Tiap hari 11:00 — produksi 1 video reaktif berdasarkan trending feed."""
    if not VIDEO_ENABLED:
        return
    print("[TrendingVideo] Produksi video trending...")
    try:
        info = produce_trending_video(urgency_filter="HIGH")
        if info:
            msg = format_trending_video_tg(info)
            print(msg)
            _send_tg(msg, "Trending video siap upload")
            _send_tg_video(info["video_path"], caption=f"📈 {info['topic']}", label="File trending video")
    except Exception as e:
        print(f"[TrendingVideo] ERROR: {e}")
        _send_tg(f"⚠️ Trending video error: {e}", "Error trending video")


# ── Main ────────────────────────────────────────────────

if __name__ == "__main__":
    # Pastikan BGM tersedia (download otomatis jika belum ada)
    try:
        from scripts.download_bgm import ensure_bgm
        ensure_bgm(min_files=1)
    except Exception as _e:
        print(f"[BGM] Skip auto-download: {_e}")

    # Sync clip sumber dari Google Drive (jika dikonfigurasi)
    if is_gdrive_configured():
        try:
            sync_clips_from_drive("assets/clips")
        except Exception as _e:
            print(f"[GDrive] Sync clip gagal: {_e}")

    print("=" * 50)
    print("PPBIB Bot mulai...")
    print(f"  TikTok   : {'AKTIF' if TIKTOK_ENABLED else 'NONAKTIF (setup token dulu)'}")
    if _SF_KEY:
        _video_mode = "AI (SiliconFlow Wan 2.2)"
    elif is_gdrive_configured():
        _video_mode = "Clip dari Google Drive"
    elif VIDEO_ENABLED:
        _video_mode = "Clip Lokal (assets/clips/)"
    else:
        _video_mode = "NONAKTIF"
    print(f"  Video    : {_video_mode}")
    print(f"  GDrive   : {'AKTIF' if is_gdrive_configured() else 'NONAKTIF (opsional)'}")
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

    scheduler.add_job(job_collect_analytics,      "cron", hour=19, minute=0,                    id="analytics_collect")
    scheduler.add_job(job_daily_report,           "cron", hour=20, minute=0,                    id="analytics_daily")
    scheduler.add_job(job_weekly_report,          "cron", day_of_week="mon", hour=7,  minute=0, id="analytics_weekly")
    scheduler.add_job(job_daily_content_reminder, "cron", hour=7,  minute=0,                    id="content_reminder")
    scheduler.add_job(job_auto_research,          "cron", day_of_week="sat", hour=17, minute=0, id="auto_research")
    scheduler.add_job(job_generate_content,       "cron", day_of_week="sun", hour=18, minute=0, id="content_generate")
    scheduler.add_job(job_produce_video,          "cron", hour=8,  minute=0,                    id="video_produce")
    scheduler.add_job(job_analyze_trending_feed,  "cron", hour=10, minute=0,                    id="trending_feed")
    scheduler.add_job(job_produce_trending_video, "cron", hour=11, minute=0,                    id="trending_video")

    print("Scheduler aktif:")
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
    print("  - Analisis tren feed  : tiap hari 10:00")
    if VIDEO_ENABLED:
        print("  - Video trending      : tiap hari 11:00")
    print()
    print("Bot berjalan... (Ctrl+C untuk berhenti)")
    scheduler.start()
