"""
Lead Analyzer — scan history WA, identifikasi lead hampir closing via AI.
Dijalankan otomatis tiap malam jam 21:00.
"""
import os
import json
import requests
from openai import OpenAI
from datetime import datetime

WA_API = os.getenv("WHATSAPP_URL", "http://ppbib.railway.internal:3000")

client = OpenAI(
    api_key=os.getenv("DINOIKI_API_KEY"),
    base_url="https://ai.dinoiki.com/v1",
)

PPBIB_CONTEXT = """PPBIB menjual produk digital untuk peternak itik:
- Ebook panduan budidaya itik: Rp 75.000
- Kalkulator pakan itik (tool digital)
Target: peternak itik Indonesia, skala 100-2.000 ekor."""


def analyze_leads() -> list:
    print("[LeadAnalyzer] Meminta analisis dari WhatsApp bot (semua chat)...")
    try:
        resp = requests.get(f"{WA_API}/analyze-leads", timeout=600)
        data = resp.json()
        leads = data.get("leads", [])
        total = data.get("total_scanned", "?")
        print(f"[LeadAnalyzer] Scan {total} chat selesai. Ditemukan {len(leads)} lead panas.")
        return leads
    except Exception as e:
        print(f"[LeadAnalyzer] Gagal: {e}")
        return []


def format_lead_report(leads: list) -> str:
    today = datetime.now().strftime("%d %b %Y")
    if not leads:
        return (
            f"✅ *Analisis Lead — {today}*\n\n"
            "Tidak ada lead panas terdeteksi malam ini.\n"
            "_Semua lead sudah closing atau belum menunjukkan minat kuat._"
        )

    lines = [
        f"🔥 *Lead Hampir Closing — {today}*",
        f"Ada *{len(leads)} lead* yang perlu di-follow up malam ini:",
        "─" * 30, ""
    ]
    for i, lead in enumerate(leads[:5], 1):
        lines += [
            f"*{i}. {lead['name']} ({lead['phone']})*",
            f"🎯 Score: {lead.get('score')}/10",
            f"📝 {lead.get('reason', '')}",
            f"💬 _{lead.get('last_intent', '')}_",
            "",
            "*Suggested reply:*",
            lead.get("suggested_reply", ""),
            "", "─" * 30, ""
        ]
    lines.append("_Analisis otomatis PPBIB Bot_")
    return "\n".join(lines)
