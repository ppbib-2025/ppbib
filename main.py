"""
Entry point: jalankan dengan `python main.py`
Railway: Flask sebagai web server utama, scheduler di background thread.
"""
import os
import threading
import time

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

from src.bot import scan_and_reply, run_followups, handle_incoming_wa
from src.delivery import run_delivery
from src.tiktok_auth import get_auth_url, load_token

WA_NUMBER = os.getenv("WHATSAPP_NUMBER", "")
PORT = int(os.getenv("PORT", 5000))

flask_app = Flask(__name__)


# ── Webhook WAHA: terima pesan WA masuk ───────────────────────────────────────
@flask_app.route("/webhook/waha", methods=["POST"])
def waha_webhook():
    """
    WAHA mengirim POST ke sini setiap ada pesan masuk.
    Set webhook URL di dashboard WAHA: https://app-kamu.railway.app/webhook/waha
    """
    data = request.get_json(silent=True) or {}
    event = data.get("event", "")

    if event != "message":
        return jsonify({"ok": True})

    payload = data.get("payload", {})
    from_id = payload.get("from", "")       # format: 628xxx@c.us
    body = payload.get("body", "").strip()
    msg_type = payload.get("type", "")

    # Abaikan pesan dari grup dan non-teks
    if "@g.us" in from_id or not body or msg_type != "chat":
        return jsonify({"ok": True})

    phone = from_id.replace("@c.us", "")

    print(f"[WA IN] {phone}: {body[:60]}")
    try:
        threading.Thread(
            target=handle_incoming_wa, args=(phone, body), daemon=True
        ).start()
    except Exception as e:
        print(f"[WA IN] Error: {e}")

    return jsonify({"ok": True})


# ── Mark paid (manual / dari payment gateway) ─────────────────────────────────
@flask_app.route("/mark-paid", methods=["POST"])
def mark_paid_endpoint():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    phone = data.get("phone", "")
    if not username:
        return jsonify({"error": "username wajib"}), 400
    from src.crm import mark_paid
    mark_paid(username, phone)
    return jsonify({"success": True, "message": f"{username} ditandai sebagai paid"})


# ── Dashboard status leads ─────────────────────────────────────────────────────
@flask_app.route("/status", methods=["GET"])
def status():
    from src.crm import load_leads
    from src.whatsapp import is_wa_connected
    leads = load_leads()
    summary = {}
    for lead in leads.values():
        s = lead["status"]
        summary[s] = summary.get(s, 0) + 1
    return jsonify({
        "total_leads": len(leads),
        "by_status": summary,
        "wa_connected": is_wa_connected(),
    })


@flask_app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "PPBIB Bot", "status": "running"})


# ── Scheduler ─────────────────────────────────────────────────────────────────
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scan_and_reply, "interval", minutes=15, id="scan")
    scheduler.add_job(lambda: run_followups(WA_NUMBER), "interval", hours=6, id="followup")
    scheduler.add_job(run_delivery, "interval", hours=6, id="delivery")
    scheduler.start()
    print("Scheduler aktif: scan tiap 15 menit, follow-up & delivery tiap 6 jam.")
    return scheduler


if __name__ == "__main__":
    token = load_token()
    if not token:
        print("=" * 50)
        print("TOKEN BELUM ADA. Buka URL ini di browser untuk login TikTok:")
        print(get_auth_url())
        print("=" * 50)
        print("Setelah login, set variabel TIKTOK_TOKEN di Railway.")
    else:
        print("Token ditemukan. Bot berjalan...")

    scheduler = start_scheduler()

    try:
        flask_app.run(host="0.0.0.0", port=PORT, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("\nBot dihentikan.")
