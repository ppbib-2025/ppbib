import json
import os
from datetime import datetime

LEADS_FILE = "data/leads.json"


def load_leads() -> dict:
    if not os.path.exists(LEADS_FILE):
        return {}
    with open(LEADS_FILE) as f:
        return json.load(f)


def save_leads(leads: dict):
    os.makedirs(os.path.dirname(LEADS_FILE), exist_ok=True)
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


def add_lead(username: str, source_video: str, comment: str, score: int = 5, intent: str = ""):
    leads = load_leads()
    if username not in leads:
        leads[username] = {
            "username": username,
            "source_video": source_video,
            "comment": comment,
            "status": "new",
            "score": score,
            "intent": intent,
            "priority": "medium",
            "phone": "",
            "created_at": datetime.now().isoformat(),
            "last_contact": datetime.now().isoformat(),
            "notes": "",
        }
        save_leads(leads)
        print(f"[CRM] Lead baru: {username} (skor: {score})")
    return leads[username]


def update_status(username: str, status: str, note: str = ""):
    leads = load_leads()
    if username in leads:
        leads[username]["status"] = status
        leads[username]["last_contact"] = datetime.now().isoformat()
        if note:
            leads[username]["notes"] += f"\n{datetime.now().date()}: {note}"
        save_leads(leads)


def set_phone(username: str, phone: str):
    """Simpan nomor HP lead setelah diketahui dari WhatsApp."""
    leads = load_leads()
    if username in leads:
        leads[username]["phone"] = phone
        save_leads(leads)


def mark_paid(username: str, phone: str = ""):
    """Tandai lead sebagai sudah bayar dan mulai alur delivery."""
    leads = load_leads()
    if username in leads:
        leads[username]["status"] = "paid"
        leads[username]["paid_at"] = datetime.now().isoformat()
        leads[username]["last_contact"] = datetime.now().isoformat()
        if phone:
            leads[username]["phone"] = phone
        leads[username]["notes"] += f"\n{datetime.now().date()}: Pembayaran dikonfirmasi"
        save_leads(leads)
        print(f"[CRM] Lead bayar: {username}")


def get_leads_by_status(status: str) -> list:
    leads = load_leads()
    return [l for l in leads.values() if l["status"] == status]


def get_lead_by_phone(phone: str) -> dict | None:
    """Cari lead berdasarkan nomor HP (untuk incoming WA message)."""
    clean = phone.replace("+", "").replace("-", "").replace(" ", "")
    for lead in load_leads().values():
        lead_phone = lead.get("phone", "").replace("+", "").replace("-", "").replace(" ", "")
        if lead_phone and lead_phone == clean:
            return lead
    return None


def get_high_priority_leads() -> list:
    """Ambil semua lead dengan prioritas tinggi yang belum closed."""
    closed_statuses = {"closed", "paid", "onboarding_d1", "onboarding_d3", "onboarding_d7", "alumni_upsell"}
    leads = load_leads()
    return [
        l for l in leads.values()
        if l.get("priority") == "high" and l["status"] not in closed_statuses
    ]
