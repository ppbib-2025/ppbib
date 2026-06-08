"""
Main bot: scan komentar, reply, catat leads, jadwalkan follow-up.
"""
from datetime import datetime, timedelta

from src.tiktok_api import get_my_videos, get_comments, reply_comment
from src.crm import add_lead, update_status, get_leads_by_status
from src.whatsapp import send_whatsapp
from src.ai_scorer import score_lead, generate_wa_response
from templates.funnel import (
    is_interested, reply_komentar, pesan_dm_awal,
    followup_d1, followup_d3, followup_d7,
)

REPLIED_FILE = "data/replied_comments.txt"


def load_replied() -> set:
    try:
        with open(REPLIED_FILE) as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()


def mark_replied(comment_id: str):
    with open(REPLIED_FILE, "a") as f:
        f.write(comment_id + "\n")


def scan_and_reply():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning komentar...")
    replied = load_replied()
    videos = get_my_videos()

    for video in videos:
        video_id = video["id"]
        result = get_comments(video_id)
        comments = result.get("data", {}).get("comments", [])

        for comment in comments:
            cid = comment["id"]
            if cid in replied:
                continue

            text = comment.get("text", "")
            username = comment.get("username", "user")

            if not is_interested(text):
                continue

            # AI scoring untuk prioritas lead
            ai_result = score_lead(username, text)
            score = ai_result.get("score", 5)
            intent = ai_result.get("intent", "")
            priority = ai_result.get("priority", "medium")

            print(f"  → @{username} | skor: {score}/10 | {intent[:40]}")

            # Reply di TikTok
            reply = reply_komentar(username)
            reply_comment(video_id, cid, reply)
            mark_replied(cid)

            # Simpan lead dengan skor AI
            lead = add_lead(username, video_id, text, score=score, intent=intent)

            # Update priority di CRM
            from src.crm import load_leads, save_leads
            leads = load_leads()
            if username in leads:
                leads[username]["priority"] = priority
                save_leads(leads)

            # Kirim DM awal via WhatsApp jika nomor diketahui
            # (nomor belum ada di tahap ini — di-update saat mereka balas WA)
            update_status(username, "dm_sent", f"TikTok reply terkirim. Skor: {score}/10 — {intent}")
            print(f"  ✓ Reply terkirim, lead disimpan (prioritas: {priority}).")

    print("Scan selesai.")


def run_followups(wa_number: str):
    """Kirim pesan follow-up WhatsApp ke lead sesuai jadwal D1/D3/D7."""
    now = datetime.now()

    # Follow-up D1 — 1 hari setelah TikTok reply
    for lead in get_leads_by_status("dm_sent"):
        created = datetime.fromisoformat(lead["created_at"])
        if now - created < timedelta(days=1):
            continue
        phone = lead.get("phone", "")
        msg = followup_d1(lead["username"])
        if phone:
            sent = send_whatsapp(phone, msg)
            note = "Follow-up D1 dikirim via WA" if sent else "Follow-up D1 GAGAL kirim WA"
        else:
            sent = False
            note = "Follow-up D1 — nomor HP belum ada"
        print(f"[FU D1] {lead['username']}: {'✓' if sent else '✗ (no phone)'}")
        update_status(lead["username"], "followup_d1", note)

    # Follow-up D3 — 2 hari setelah D1
    for lead in get_leads_by_status("followup_d1"):
        last = datetime.fromisoformat(lead["last_contact"])
        if now - last < timedelta(days=2):
            continue
        phone = lead.get("phone", "")
        msg = followup_d3(lead["username"], wa_number)
        if phone:
            sent = send_whatsapp(phone, msg)
            note = "Follow-up D3 dikirim via WA" if sent else "Follow-up D3 GAGAL kirim WA"
        else:
            sent = False
            note = "Follow-up D3 — nomor HP belum ada"
        print(f"[FU D3] {lead['username']}: {'✓' if sent else '✗ (no phone)'}")
        update_status(lead["username"], "followup_d3", note)

    # Follow-up D7 — 4 hari setelah D3
    for lead in get_leads_by_status("followup_d3"):
        last = datetime.fromisoformat(lead["last_contact"])
        if now - last < timedelta(days=4):
            continue
        phone = lead.get("phone", "")
        msg = followup_d7(lead["username"], wa_number)
        if phone:
            sent = send_whatsapp(phone, msg)
            note = "Follow-up D7 dikirim via WA" if sent else "Follow-up D7 GAGAL kirim WA"
        else:
            sent = False
            note = "Follow-up D7 — nomor HP belum ada"
        print(f"[FU D7] {lead['username']}: {'✓' if sent else '✗ (no phone)'}")
        update_status(lead["username"], "followup_d7", note)


def handle_incoming_wa(phone: str, message: str) -> str:
    """
    Dipanggil dari Flask endpoint saat ada pesan WA masuk.
    Cari lead by phone, generate AI response, kirim balik via WA.
    """
    from src.crm import get_lead_by_phone, set_phone, load_leads, save_leads

    lead = get_lead_by_phone(phone)
    username = lead["username"] if lead else phone

    if not lead:
        # Lead belum ada nomor — coba update lead terbaru tanpa phone
        print(f"[WA IN] Pesan dari nomor tidak dikenal: {phone}")
        response = (
            "Halo! Terima kasih sudah menghubungi PPBIB 😊\n"
            "Boleh kami tahu nama kamu dan dari mana kamu tahu tentang PPBIB?"
        )
    else:
        # Update phone jika belum ada
        if not lead.get("phone"):
            set_phone(username, phone)

        # Generate AI response
        response = generate_wa_response(username, message, lead)

        # Catat di CRM
        update_status(username, lead["status"], f"Pesan masuk WA: {message[:80]}")

    # Kirim balik
    send_whatsapp(phone, response)
    print(f"[WA IN] Reply AI → {phone}: {response[:60]}...")
    return response
