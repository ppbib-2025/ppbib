"""
AI Content Generator — buat rencana konten mingguan berdasarkan insight performa.
Menggunakan Claude API. Jalankan otomatis tiap Minggu jam 18:00.
"""
import os
import json
import re
from datetime import datetime
from anthropic import Anthropic
from src.analytics import get_top_content
from src.auto_research import load_strategy_insights
from src.trend_researcher import get_trend_context_for_content

client = Anthropic()

CONTENT_QUEUE_FILE = "data/content_queue.json"

DAY_MAP = {
    "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
    "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
}

BRAND_CONTEXT = """Kamu adalah content strategist untuk PPBIB (Pusat Pengembangan Budidaya Ikan Bisnis).
PPBIB menjual produk konsultasi, laporan kelayakan usaha, dan program kemitraan budidaya ikan air tawar komersial.
Target audiens: investor dan pengusaha menengah ke atas, usia 30-55 tahun, memiliki modal Rp 50 juta ke atas,
cari passive income atau diversifikasi bisnis ke sektor agribisnis ikan air tawar (lele, nila, gurame, patin, mas).
Mereka BUKAN peternak kecil — mereka adalah pebisnis yang mengevaluasi peluang investasi.
Tone: profesional, data-driven, seperti konsultan bisnis berpengalaman — bukan tutorial pemula.
Selalu sertakan angka nyata (ROI %, proyeksi Rp/bulan, modal awal, payback period, yield per m²)
agar konten terasa kredibel dan layak dipertimbangkan sebagai keputusan bisnis."""


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
        "Belum ada data performa. Gunakan topik premium: "
        "ROI budidaya ikan komersial, perbandingan sistem RAS vs konvensional, "
        "proyeksi keuntungan kolam 1 hektar, modal masuk budidaya ikan nila/gurame."
    )


def generate_weekly_plan() -> dict:
    """
    Generate rencana konten 1 minggu berdasarkan insight performa + data trend premium.
    Return dict lengkap: 7 video scripts, 2 carousel, 2 foto.
    """
    top_summary = _top_content_summary()
    strategy = load_strategy_insights()
    strategy_prompt = strategy.get("strategy_prompt", "")
    strategy_iteration = strategy.get("iteration", 0)
    trend_context = get_trend_context_for_content()

    strategy_block = (
        f"STRATEGI AUTO RESEARCH (iterasi #{strategy_iteration}):\n{strategy_prompt}"
        if strategy_prompt
        else "STRATEGI AUTO RESEARCH: Belum ada data. Gunakan pendekatan premium default."
    )

    prompt = f"""{BRAND_CONTEXT}

DATA KONTEN TERBAIK (engagement rate tertinggi):
{top_summary}

{strategy_block}

{trend_context}

Berdasarkan data di atas, buat rencana konten organik 1 minggu untuk TikTok, Instagram, dan Facebook.
Semua konten harus menyasar audiens premium — pebisnis dan investor, BUKAN pemula.

KEWAJIBAN FORMAT KONTEN:
- Setiap konten HARUS mengandung minimal satu dari: angka ROI, proyeksi pendapatan, perbandingan modal,
  atau data pasar yang bisa dijadikan dasar keputusan bisnis
- Hook video: mulai dengan angka atau klaim mengejutkan yang relevan bagi investor
  (contoh: "Farm ikan nila 2.000 m² bisa hasilkan Rp 18 juta/bulan bersih — ini hitungannya")
- CTA: arahkan ke konsultasi, feasibility study, atau kemitraan PPBIB — bukan ebook murah
- Hindari kata: pemula, mudah, murah, hemat, rumahan, sampingan
- Gunakan kata: investasi, ROI, skala komersial, proyeksi, margin, yield, kemitraan

TOPIK PRIORITAS (pilih yang relevan dengan trend di atas):
- Proyeksi ROI budidaya lele/nila/gurame skala komersial 2026
- Perbandingan sistem RAS vs bioflok vs konvensional: mana yang lebih bankable?
- Modal masuk farm ikan 1 hektar: rincian dan payback period
- Harga jual ikan ke hotel/restoran/supermarket premium vs pasar tradisional
- Due diligence sebelum investasi di bisnis budidaya ikan
- Tren ekspor ikan air tawar Indonesia: peluang dan regulasi
- Kemitraan budidaya ikan: model bagi hasil yang menguntungkan

Return HANYA JSON valid, tidak ada teks lain sebelum atau sesudah JSON:

{{
  "week_theme": "tema utama minggu ini dalam 1 kalimat (angle investasi/bisnis)",
  "insight_note": "analisis singkat: pola konten terbaik yang kita replikasi + angle premium yang digunakan",
  "strategy_iteration": {strategy_iteration},
  "target_segment": "investor/pengusaha menengah ke atas, modal Rp 50jt+, cari passive income agribisnis",
  "videos": [
    {{
      "day": "Senin",
      "topic": "judul topik video (angle bisnis/investasi)",
      "hook": "kalimat pembuka 3 detik — mulai dengan angka atau fakta mengejutkan untuk investor",
      "script": "narasi 45-60 detik, tone konsultan bisnis berpengalaman, sertakan angka nyata",
      "caption": "caption max 150 karakter + emoji, tone profesional",
      "hashtags": ["#budidayaikan", "#investasiagribisnis", "#ppbib", "#bisnisakuakultur"],
      "cta": "ajakan konsultasi / feasibility study / kemitraan PPBIB"
    }}
  ],
  "carousels": [
    {{
      "day": "Rabu",
      "platform": "Instagram",
      "topic": "judul carousel (angle analisis bisnis/perbandingan)",
      "slides": [
        {{"num": 1, "heading": "judul utama dengan angka", "body": "hook data mengejutkan"}},
        {{"num": 2, "heading": "...", "body": "..."}},
        {{"num": 3, "heading": "...", "body": "..."}},
        {{"num": 4, "heading": "...", "body": "..."}},
        {{"num": 5, "heading": "Tertarik?", "body": "CTA ke konsultasi/kemitraan PPBIB"}}
      ],
      "caption": "caption post dengan angka kunci",
      "hashtags": ["#investasiikan", "#ppbib", "#akuakultur"]
    }}
  ],
  "photos": [
    {{
      "day": "Jumat",
      "platform": "Instagram",
      "concept": "deskripsi visual: infografis/data visual, warna profesional, tabel/angka proyeksi keuangan",
      "caption": "caption dengan proyeksi angka nyata dan CTA bisnis",
      "hashtags": ["#investasiagribisnis", "#budidayaikankomersial", "#ppbib"]
    }}
  ]
}}

Buat: 7 video (Senin-Minggu), 2 carousel, 2 foto. Semua Bahasa Indonesia."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
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
    """Ringkasan rencana konten untuk WA."""
    iteration = plan.get("strategy_iteration", 0)
    iter_note = f" _(strategi iterasi #{iteration})_" if iteration else ""
    lines = [
        "\U0001f3ac *RENCANA KONTEN PPBIB MINGGU INI*",
        f"\U0001f4c5 Pekan {plan.get('week_of', '')}{iter_note}",
        f"\U0001f3af Tema: *{plan.get('week_theme', '')}*",
        f"\U0001f4a1 {plan.get('insight_note', '')}",
        f"\U0001f3af Segmen: _{plan.get('target_segment', 'investor/pengusaha menengah ke atas')}_",
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
