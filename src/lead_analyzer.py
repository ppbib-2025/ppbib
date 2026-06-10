"""
Lead Analyzer — trigger analisis WA lead via bot.js yang handle semuanya.
"""
import os
import requests

WA_API = os.getenv("WHATSAPP_URL", "http://ppbib.railway.internal:3000")


def analyze_leads() -> list:
    print("[LeadAnalyzer] Trigger analisis background di WA bot...")
    try:
        resp = requests.get(f"{WA_API}/analyze-leads/start", timeout=15)
        data = resp.json()
        print(f"[LeadAnalyzer] {data.get('message', data)}")
        return []  # hasil dikirim langsung oleh bot.js ke WA owner
    except Exception as e:
        print(f"[LeadAnalyzer] Gagal trigger: {e}")
        return []


def format_lead_report(leads: list) -> str:
    # Bot.js langsung kirim ke WA owner, tidak perlu format di sini
    return ""
