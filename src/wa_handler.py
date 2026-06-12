"""
Handler pesan masuk WhatsApp → Coze (Rina) → balas.
Dipanggil oleh Flask webhook /wa/incoming.
"""
import re
from datetime import datetime

from src.crm import (
    get_lead_by_phone, add_lead_wa, update_lead, update_status,
    get_all_wa_leads, increment_followup,
)
from src.coze_agent import ask_rina
from src.whatsapp import send_whatsapp

# Lead yang punya status ini tidak dibalas otomatis
_SKIP_STATUSES = {"closing", "cold"}

# Jam minimum tidak ada interaksi sebelum follow-up dikirim
FOLLOWUP_IDLE_HOURS  = int(__import__("os").getenv("FOLLOWUP_IDLE_HOURS", "6"))
FOLLOWUP_MAX_COUNT   = int(__import__("os").getenv("FOLLOWUP_MAX_COUNT", "5"))


def normalize_phone(phone: str) -> str:
    return re.sub(r"[^0-9]", "", phone)


# ── Incoming handler ──────────────────────────────────────────────────────────

def handle_incoming(phone: str, message: str):
    """
    Proses pesan masuk dari lead.
    1. Lookup / buat lead
    2. Kirim ke Coze (Rina)
    3. Balas via WA
    4. Update CRM
    """
    phone = normalize_phone(phone)
    print(f"[WA-IN] {phone}: {message[:80]}")

    lead = get_lead_by_phone(phone)
    if not lead:
        lead = add_lead_wa(phone, message)

    if lead.get("status") in _SKIP_STATUSES:
        print(f"[WA-IN] Skip {phone} — status {lead['status']}")
        return

    context = _build_context(lead)
    reply, conv_id = ask_rina(
        user_id=phone,
        message=message,
        conversation_id=lead.get("conversation_id") or None,
        funnel_context=context,
    )

    if not reply:
        print(f"[WA-IN] Tidak ada balasan dari Coze untuk {phone}")
        return

    ok = send_whatsapp(phone, reply)
    if ok:
        updates = {"conversation_id": conv_id}
        # Naikkan status dari new → qualified setelah pertama balas
        if lead.get("status") == "new":
            updates["status"] = "qualified"
        update_lead(phone, updates)
        print(f"[WA-OUT] Terkirim ke {phone}")
    else:
        print(f"[WA-OUT] GAGAL kirim ke {phone}")


# ── Scheduled follow-up ───────────────────────────────────────────────────────

def run_wa_followups():
    """
    Cek semua lead WA yang idle > FOLLOWUP_IDLE_HOURS jam dan belum closing.
    Generate follow-up via Coze lalu kirim.
    Dipanggil oleh APScheduler tiap beberapa jam.
    """
    now = datetime.now()
    for lead in get_all_wa_leads():
        phone  = lead.get("phone") or lead.get("key")
        status = lead.get("status", "new")

        if status in _SKIP_STATUSES:
            continue

        fu_count = lead.get("follow_up_count", 0)
        if fu_count >= FOLLOWUP_MAX_COUNT:
            update_status(phone, "cold", f"Max follow-up ({FOLLOWUP_MAX_COUNT}x) tercapai")
            continue

        last = lead.get("last_interaction") or lead.get("created_at")
        try:
            idle_hours = (now - datetime.fromisoformat(last)).total_seconds() / 3600
        except Exception:
            continue

        if idle_hours < FOLLOWUP_IDLE_HOURS:
            continue

        _send_followup(phone, lead)


def _send_followup(phone: str, lead: dict):
    fu_count = lead.get("follow_up_count", 0)
    context  = _build_context(lead)

    # Prompt khusus follow-up — Coze akan generate pesan natural
    prompt = (
        f"Ini adalah follow-up ke-{fu_count + 1} untuk lead ini. "
        "Kirim pesan follow-up yang natural dan tidak terkesan spam. "
        "Tanyakan apakah ada yang bisa dibantu, ingatkan soal program PPBIB, "
        "dan ciptakan urgensi ringan jika follow-up ke-3 atau lebih."
    )

    reply, conv_id = ask_rina(
        user_id=phone,
        message=prompt,
        conversation_id=lead.get("conversation_id") or None,
        funnel_context=context,
    )

    if not reply:
        return

    ok = send_whatsapp(phone, reply)
    if ok:
        increment_followup(phone)
        updates = {"conversation_id": conv_id}
        update_lead(phone, updates)
        print(f"[FU] Follow-up ke-{fu_count + 1} terkirim ke {phone}")
    else:
        print(f"[FU] GAGAL kirim follow-up ke {phone}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_context(lead: dict) -> dict:
    try:
        created  = datetime.fromisoformat(lead["created_at"])
        hari_ke  = (datetime.now() - created).days + 1
    except Exception:
        hari_ke  = 1
    return {
        "status":         lead.get("status", "new"),
        "follow_up_count": lead.get("follow_up_count", 0),
        "hari_ke":        hari_ke,
    }
