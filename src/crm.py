import json
import os
from datetime import datetime

LEADS_FILE = "data/leads.json"

# Status pipeline WA
# new → qualified → offer_sent → negotiating → closing → cold
STATUS_FLOW = ["new", "qualified", "offer_sent", "negotiating", "closing", "cold"]


def load_leads() -> dict:
    if not os.path.exists(LEADS_FILE):
        return {}
    with open(LEADS_FILE) as f:
        return json.load(f)


def save_leads(leads: dict):
    os.makedirs(os.path.dirname(LEADS_FILE), exist_ok=True)
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


# ── TikTok lead (lama) ────────────────────────────────────────────────────────

def add_lead(username: str, source_video: str, comment: str) -> dict:
    leads = load_leads()
    if username not in leads:
        leads[username] = _new_lead(username, source=f"tiktok:{source_video}", note=comment)
        save_leads(leads)
        print(f"[CRM] Lead baru (TikTok): {username}")
    return leads[username]


# ── WhatsApp lead ─────────────────────────────────────────────────────────────

def add_lead_wa(phone: str, first_message: str = "") -> dict:
    """Buat lead baru dari nomor WA. Key = phone number."""
    leads = load_leads()
    if phone not in leads:
        leads[phone] = _new_lead(phone, source="whatsapp", note=first_message)
        save_leads(leads)
        print(f"[CRM] Lead baru (WA): {phone}")
    return leads[phone]


def get_lead_by_phone(phone: str) -> dict | None:
    return load_leads().get(phone)


def update_lead(key: str, fields: dict):
    """Update field-field tertentu pada lead (merge, bukan overwrite)."""
    leads = load_leads()
    if key in leads:
        leads[key].update(fields)
        leads[key]["last_interaction"] = datetime.now().isoformat()
        save_leads(leads)


# ── Shared helpers ────────────────────────────────────────────────────────────

def update_status(key: str, status: str, note: str = ""):
    leads = load_leads()
    if key in leads:
        leads[key]["status"] = status
        leads[key]["last_interaction"] = datetime.now().isoformat()
        if note:
            ts = datetime.now().date().isoformat()
            leads[key]["notes"] += f"\n{ts}: {note}"
        save_leads(leads)


def get_leads_by_status(status: str) -> list:
    return [l for l in load_leads().values() if l["status"] == status]


def get_all_wa_leads() -> list:
    """Semua lead yang punya nomor WA (source whatsapp atau ada field phone)."""
    return [
        l for l in load_leads().values()
        if l.get("source", "").startswith("whatsapp") or l.get("phone")
    ]


def increment_followup(key: str):
    leads = load_leads()
    if key in leads:
        leads[key]["follow_up_count"] = leads[key].get("follow_up_count", 0) + 1
        leads[key]["last_followup"] = datetime.now().isoformat()
        save_leads(leads)


# ── Private ───────────────────────────────────────────────────────────────────

def _new_lead(key: str, source: str = "", note: str = "") -> dict:
    now = datetime.now().isoformat()
    return {
        "key": key,
        "phone": key if source.startswith("whatsapp") else "",
        "username": key,
        "source": source,
        "status": "new",
        "conversation_id": "",   # Coze conversation ID
        "follow_up_count": 0,
        "created_at": now,
        "last_interaction": now,
        "last_followup": "",
        "notes": note,
    }
