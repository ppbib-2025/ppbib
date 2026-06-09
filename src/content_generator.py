"""
AI Content Generator — buat rencana konten mingguan berdasarkan insight performa.
Menggunakan Claude API. Jalankan otomatis tiap Minggu jam 18:00.
"""
import os
import json
import re
from datetime import datetime
from openai import OpenAI
from src.analytics import get_top_content

client = OpenAI(
    api_key=os.getenv("DINOIKI_API_KEY"),
    base_url="https://ai.dinoiki.com/v1",
)

CONTENT_QUEUE_FILE = "data/content_queue.json"

DAY_MAP = {
    "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
    "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
}

BRAND_CONTEXT = """Kamu adalah content strategist untuk PPBIB (Pusat Pengembangan Budidaya Itik dan Bebek).
PPBIB menjual produk digital (ebook Rp75.000, kalkulator pakan) untuk peternak itik Indonesia.
Target audiens: peternak itik skala 100-2.000 ekor, usia 25-55 tahun, mayoritas Jawa & Sumatera.
Tone: praktis, mudah dipahami, seperti mentor berpengalaman — bukan akademis.
Selalu sertakan angka nyata (Rp, %, kg, ekor) agar konten terasa terpercaya."""


def _top_content_summary() -> str:
    """Ringkasan konten terbaik dari semua platform sebagai konteks AI."""
    lines = []
    for platform in ["tiktok", "instagram", "facebook"]:
        top = get_top_content(platform, n=3)
        if top:
            lines.append(f"{platform.upper()}:")
            for t in top:
                title = (t.get("title") or t.get("caption") or t.get("message") or "").strip()[:80]
                lines.append(f'  - "{title}" (ER: {t["engagement_rate"]}%)')
    return "\n".join(lines) if lines else (
        "Belum ada data performa. Gunakan topik umum: "
        "pakan mandiri, FCR, keuntungan ternak itik."
    )


def generate_weekly_plan() -> dict:
    """
    Generate rencana konten 1 minggu berdasarkan insight performa.
    Return dict lengkap: 7 video scripts, 2 carousel, 2 foto.
    """
    top_summary = _top_content_summary()

    prompt = f"""{BRAND_CONTEXT}

DATA KONTEN TERBAIK PPBIB (engagement rate tertinggi minggu ini):
{top_summary}

Berdasarkan pola konten yang perform di atas, buat rencana konten organik 1 minggu
untuk TikTok, Instagram, dan Facebook.

Return HANYA JSON valid, tidak ada teks lain sebelum atau sesudah JSON:

{{
  "week_theme": "tema utama minggu ini dalam 1 kalimat",
  "insight_note": "analisis singkat: pola apa dari konten terbaik yang kita replikasi minggu ini",
  "videos": [
    {{
      "day": "Senin",
      "topic": "judul topik video",
      "hook": "kalimat pembuka 3 detik yang langsung menarik perhatian",
      "script": "narasi lengkap 45-60 detik, natural seperti bicara ke peternak",
      "caption": "caption TikTok/IG/FB max 150 karakter + emoji",
      "hashtags": ["#itik", "#ternak", "#pakan", "#ppbib", "#budidaya"],
      "cta": "call to action di akhir video max 1 kalimat"
    }}
  ],
  "carousels": [
    {{
      "day": "Rabu",
      "platform": "Instagram",
      "topic": "judul carousel",
      "slides": [
        {{"num": 1, "heading": "judul slide", "body": "isi 2-3 baris singkat"}},
        {{"num": 2, "heading": "...", "body": "..."}},
        {{"num": 3, "heading": "...", "body": "..."}},
        {{"num": 4, "heading": "...", "body": "..."}},
        {{"num": 5, "heading": "Kesimpulan + CTA", "body": "ajakan ambil ebook/kalkulator PPBIB"}}
      ],
      "caption": "caption post",
      "hashtags": ["#itik", "#ppbib"]
    }}
  ],
  "photos": [
    {{
      "day": "Jumat",
      "platform": "Instagram",
      "concept": "deskripsi visual detail: warna, elemen, angka/data yang ditampilkan, ukuran",
      "caption": "caption lengkap dengan angka dan fakta nyata",
      "hashtags": ["#itik", "#infografis", "#ppbib"]
    }}
  ]
}}

Buat: 7 video (Senin-Minggu), 2 carousel (hari berbeda), 2 foto (hari berbeda).
Semua Bahasa Indonesia. Topik: pakan mandiri, FCR, keuntungan ternak, tips budidaya, atau promo produk PPBIB."""

    message = client.chat.completions.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.choices[0].message.content.strip()
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f"Response bukan JSON valid: {raw[:200]}")

    plan = json.loads(match.group())
    plan["generated_at"] = datetime.now().isoformat()
    plan["week_of"] = datetime.now().strftime("%Y-%m-%d")
    _append_queue(plan)
    return plan


def _append_queue(plan: dict):
    existing = []
    if os.path.exists(CONTENT_QUEUE_FILE):
        with open(CONTENT_QUEUE_FILE) as f:
            existing = json.load(f)
    existing.append(plan)
    os.makedirs("data", exist_ok=True)
    with open(CONTENT_QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"[Content] Rencana konten disimpan: {CONTENT_QUEUE_FILE}")


def format_plan_for_whatsapp(plan: dict) -> str:
    """Ringkasan rencana konten untuk WA. Detail lengkap ada di JSON."""
    lines = [
        "\U0001f3ac *RENCANA KONTEN PPBIB MINGGU INI*",
        f"\U0001f4c5 Pekan {plan.get('week_of', '')}",
        f"\U0001f3af Tema: *{plan.get('week_theme', '')}*",
        f"\U0001f4a1 {plan.get('insight_note', '')}",
        "─" * 30, "",
        "*\U0001f4f9 VIDEO HARIAN:*",
    ]
    for v in plan.get("videos", []):
        lines += [
            f"*{v['day']}* — {v['topic']}",
            f"\U0001fab4 _{v['hook']}_",
            f"\U0001f4e2 {v['cta']}",
            "",
        ]

    lines.append("*\U0001f4cb CAROUSEL:*")
    for c in plan.get("carousels", []):
        lines.append(f"  • {c['day']}: {c['topic']} ({len(c['slides'])} slide)")

    lines += ["", "*\U0001f5bc FOTO/INFOGRAFIS:*"]
    for p in plan.get("photos", []):
        lines.append(f"  • {p['day']}: {p['concept'][:70]}...")

    lines += [
        "", "─" * 30,
        "\U0001f4c1 Script lengkap: data/content_queue.json",
        "_Dibuat otomatis oleh sistem PPBIB_",
    ]
    return "\n".join(lines)


def get_todays_content() -> dict | None:
    """
    Return konten untuk hari ini dari rencana terakhir.
    Dikirim via WA setiap pagi sebagai reminder posting.
    """
    if not os.path.exists(CONTENT_QUEUE_FILE):
        return None
    with open(CONTENT_QUEUE_FILE) as f:
        queue = json.load(f)
    if not queue:
        return None

    plan = queue[-1]
    today_id = DAY_MAP.get(datetime.now().strftime("%A"), "")

    result: dict = {"day": today_id, "date": datetime.now().strftime("%d %b %Y")}
    for v in plan.get("videos", []):
        if v["day"] == today_id:
            result["video"] = v
    for c in plan.get("carousels", []):
        if c["day"] == today_id:
            result["carousel"] = c
    for p in plan.get("photos", []):
        if p["day"] == today_id:
            result["photo"] = p
    return result if len(result) > 2 else None


def format_today_for_whatsapp(content: dict) -> str:
    """Format konten hari ini jadi pesan WA reminder pagi."""
    lines = [
        f"☀️ *Konten Hari Ini — PPBIB*",
        f"\U0001f4c5 {content['date']} ({content['day']})",
        "─" * 30, "",
    ]
    if v := content.get("video"):
        lines += [
            "*\U0001f3ac VIDEO*",
            f"\U0001f4cc Topik: {v['topic']}",
            f"\U0001fab4 Hook: _{v['hook']}_",
            "",
            f"*Script:*",
            v["script"],
            "",
            f"*Caption:* {v['caption']}",
            f"*Hashtag:* {' '.join(v['hashtags'])}",
            f"*CTA:* {v['cta']}",
            "",
        ]
    if c := content.get("carousel"):
        lines += [
            f"*\U0001f4cb CAROUSEL ({c['platform']})*",
            f"Topik: {c['topic']}",
        ]
        for s in c.get("slides", []):
            lines.append(f"  Slide {s['num']}: {s['heading']}")
        lines += [f"Caption: {c['caption']}", ""]
    if p := content.get("photo"):
        lines += [
            f"*\U0001f5bc FOTO/INFOGRAFIS ({p['platform']})*",
            f"Visual: {p['concept']}",
            f"Caption: {p['caption']}",
            "",
        ]
    lines.append("_Selamat berkreasi! \U0001f4aa_")
    return "\n".join(lines)
