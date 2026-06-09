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


def fetch_chats() -> list:
    try:
        resp = requests.get(f"{WA_API}/chats", timeout=90)
        return resp.json()
    except Exception as e:
        print(f"[LeadAnalyzer] Gagal ambil chat: {e}")
        return []


def _analyze_one(chat: dict) -> dict | None:
    messages = chat.get("messages", [])
    if len(messages) < 2:
        return None

    conv = "\n".join(
        f"{m['from']}: {m['body']}"
        for m in messages[-20:]
        if m.get("body", "").strip()
    )
    if not conv.strip():
        return None

    prompt = f"""{PPBIB_CONTEXT}

Analisis percakapan WhatsApp ini:
---
{conv}
---

Apakah ini lead panas (minat beli tapi belum closing)?
Kriteria: tanya harga, minta info produk, bilang "nanti"/"pikir-pikir"/"mau konsultasi dulu", atau tidak balas setelah menunjukkan minat.

Return JSON saja tanpa teks lain:
{{"is_hot_lead": true/false, "score": 1-10, "reason": "alasan 1 kalimat", "last_intent": "apa yang terakhir mereka tanyakan", "suggested_reply": "follow-up natural max 3 kalimat Bahasa Indonesia"}}"""

    try:
        resp = client.chat.completions.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.choices[0].message.content.strip()
        result = json.loads(raw)
        if result.get("is_hot_lead") and result.get("score", 0) >= 6:
            return {"phone": chat["phone"], "name": chat.get("name", chat["phone"]), **result}
    except Exception as e:
        print(f"[LeadAnalyzer] Skip {chat.get('phone')}: {e}")
    return None


def analyze_leads() -> list:
    print("[LeadAnalyzer] Mengambil history chat WA...")
    chats = fetch_chats()
    if not chats:
        print("[LeadAnalyzer] Tidak ada chat ditemukan.")
        return []

    print(f"[LeadAnalyzer] Menganalisis {len(chats)} chat...")
    hot_leads = []
    for chat in chats:
        result = _analyze_one(chat)
        if result:
            hot_leads.append(result)

    hot_leads.sort(key=lambda x: x.get("score", 0), reverse=True)
    print(f"[LeadAnalyzer] Ditemukan {len(hot_leads)} lead panas.")
    return hot_leads


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
