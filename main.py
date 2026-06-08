"""
Entry point: jalankan dengan `python main.py`
"""
import os
import threading

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

from src.bot import scan_and_reply, run_followups, handle_incoming_wa
from src.delivery import run_delivery
from src.tiktok_auth import get_auth_url, load_token

WA_NUMBER = os.getenv("WHATSAPP_NUMBER", "")

# ── Flask app untuk menerima incoming WA dari Node.js ─────────────────────────
flask_app = Flask(__name__)


@flask_app.route("/ai-reply", methods=["POST"])
def ai_reply():
    data = request.get_json()
    phone = data.get("phone", "")
    message = data.get("message", "")
    if not phone or not message:
        return jsonify({"error": "phone dan message wajib"}), 400
    try:
        response = handle_incoming_wa(phone, message)
        return jsonify({"success": True, "response": response})
    except Exception as e:
        print(f"[Flask] Error ai-reply: {e}")
        return jsonify({"error": str(e)}), 500


@flask_app.route("/mark-paid", methods=["POST"])
def mark_paid_endpoint():
    """Endpoint untuk menandai lead sebagai sudah bayar (panggil manual/dari payment gateway)."""
    data = request.get_json()
    username = data.get("username", "")
    phone = data.get("phone", "")
    if not username:
        return jsonify({"error": "username wajib"}), 400
    from src.crm import mark_paid
    mark_paid(username, phone)
    return jsonify({"success": True, "message": f"{username} ditandai sebagai paid"})


@flask_app.route("/status", methods=["GET"])
def status():
    from src.crm import load_leads
    leads = load_leads()
    summary = {}
    for lead in leads.values():
        s = lead["status"]
        summary[s] = summary.get(s, 0) + 1
    return jsonify({"total_leads": len(leads), "by_status": summary})


def run_flask():
    flask_app.run(host="0.0.0.0", port=5000, use_reloader=False)


# ── Scheduler jobs ─────────────────────────────────────────────────────────────
def job_scan():
    scan_and_reply()


def job_followup():
    run_followups(WA_NUMBER)


def job_delivery():
    run_delivery()


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

        # Jalankan Flask di background thread
        t = threading.Thread(target=run_flask, daemon=True)
        t.start()
        print("Flask API aktif di http://localhost:5000")

        # Scheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(job_scan, "interval", minutes=15, id="scan")
        scheduler.add_job(job_followup, "interval", hours=6, id="followup")
        scheduler.add_job(job_delivery, "interval", hours=6, id="delivery")
        scheduler.start()
        print("Scheduler aktif: scan tiap 15 menit, follow-up & delivery tiap 6 jam.")

        # Tetap hidup
        try:
            import time
            while True:
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            print("\nBot dihentikan.")
