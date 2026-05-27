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


def add_lead(username: str, source_video: str, comment: str):
    leads = load_leads()
    if username not in leads:
        leads[username] = {
            "username": username,
            "source_video": source_video,
            "comment": comment,
            "status": "new",          # new → dm_sent → followup_d1 → d3 → d7 → closed
            "created_at": datetime.now().isoformat(),
            "last_contact": datetime.now().isoformat(),
            "notes": "",
        }
        save_leads(leads)
        print(f"[CRM] Lead baru: {username}")
    return leads[username]


def update_status(username: str, status: str, note: str = ""):
    leads = load_leads()
    if username in leads:
        leads[username]["status"] = status
        leads[username]["last_contact"] = datetime.now().isoformat()
        if note:
            leads[username]["notes"] += f"\n{datetime.now().date()}: {note}"
        save_leads(leads)


def get_leads_by_status(status: str) -> list:
    leads = load_leads()
    return [l for l in leads.values() if l["status"] == status]
