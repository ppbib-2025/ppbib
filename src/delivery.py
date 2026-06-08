"""
Otomasi pengiriman materi pelatihan pasca pembayaran dan upsell alumni.
"""
from datetime import datetime, timedelta

from src.crm import get_leads_by_status, update_status
from src.whatsapp import send_whatsapp
from templates.funnel import materi_hari1, materi_hari3, materi_hari7, pesan_upsell_alumni


def run_delivery():
    """Kirim materi bertahap ke peserta bayar dan upsell ke alumni."""
    now = datetime.now()

    # Onboarding D1 — segera setelah status berubah ke "paid"
    for lead in get_leads_by_status("paid"):
        phone = lead.get("phone", "")
        if not phone:
            continue
        msg = materi_hari1(lead["username"])
        if send_whatsapp(phone, msg):
            update_status(lead["username"], "onboarding_d1", "Materi Hari 1 dikirim")
            print(f"[DELIVERY] Materi D1 → {lead['username']}")

    # Onboarding D3 — 2 hari setelah D1
    for lead in get_leads_by_status("onboarding_d1"):
        phone = lead.get("phone", "")
        if not phone:
            continue
        last = datetime.fromisoformat(lead["last_contact"])
        if now - last >= timedelta(days=2):
            msg = materi_hari3(lead["username"])
            if send_whatsapp(phone, msg):
                update_status(lead["username"], "onboarding_d3", "Materi Hari 3 dikirim")
                print(f"[DELIVERY] Materi D3 → {lead['username']}")

    # Onboarding D7 — 4 hari setelah D3
    for lead in get_leads_by_status("onboarding_d3"):
        phone = lead.get("phone", "")
        if not phone:
            continue
        last = datetime.fromisoformat(lead["last_contact"])
        if now - last >= timedelta(days=4):
            msg = materi_hari7(lead["username"])
            if send_whatsapp(phone, msg):
                update_status(lead["username"], "onboarding_d7", "Materi Hari 7 dikirim")
                print(f"[DELIVERY] Materi D7 → {lead['username']}")

    # Upsell alumni — 30 hari setelah selesai onboarding
    for lead in get_leads_by_status("onboarding_d7"):
        phone = lead.get("phone", "")
        if not phone:
            continue
        last = datetime.fromisoformat(lead["last_contact"])
        if now - last >= timedelta(days=30):
            msg = pesan_upsell_alumni(lead["username"])
            if send_whatsapp(phone, msg):
                update_status(lead["username"], "alumni_upsell", "Upsell alumni dikirim")
                print(f"[DELIVERY] Upsell alumni → {lead['username']}")
