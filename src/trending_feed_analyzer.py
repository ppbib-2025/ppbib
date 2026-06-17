"""
Trending Feed Content Analyzer — ambil sinyal tren dari platform sosial media
dan analisis topik konten yang sedang viral di niche peternakan itik.

Alur:
  1. Kumpulkan sinyal tren dari analytics internal PPBIB (top performing content)
  2. Enrichment opsional via Google Trends (jika TrendsMCP tersedia di runtime)
  3. Claude filter + analisis: 3 topik video yang harus dibuat SEGERA
  4. Simpan ke data/trending_feed.json
  5. Feed ke video_producer untuk konten reaktif terhadap tren
"""
import os
import json
import re
from datetime import datetime
from anthropic import Anthropic
from src.analytics import get_top_content

client = Anthropic()

TRENDING_FEED_FILE = "data/trending_feed.json"

BRAND_CONTEXT = """PPBIB (Pusat Pengembangan Budidaya Itik dan Bebek) adalah brand edukasi
untuk peternak itik Indonesia. Produk: ebook Rp75.000, kalkulator pakan.
Target: peternak itik 100-2.000 ekor, usia 25-55 tahun, Jawa & Sumatera.
Tone: praktis, seperti mentor berpengalaman, selalu sertakan angka nyata."""


def _get_internal_trending_signals() -> dict:
    """
    Ekstrak sinyal tren dari analytics internal PPBIB.
    Topik dengan ER tertinggi = trending di audiens kita sendiri.
    """
    signals = {}
    for platform in ["tiktok", "instagram", "facebook"]:
        signals[platform] = get_top_content(platform, n=5)
    return signals


def _format_internal_signals(signals: dict) -> str:
    lines = []
    for platform, items in signals.items():
        if items:
            lines.append(f"\n{platform.upper()} — top konten:")
            for item in items[:3]:
                title = (item.get("title") or item.get("caption") or item.get("message") or "")[:80]
                lines.append(f'  - "{title}" (ER: {item["engagement_rate"]}%)')
    return "\n".join(lines) if lines else "Belum ada data performa internal."


def analyze_trending_feed(external_trends: list | None = None) -> dict:
    """
    Analisis tren konten gabungan: sinyal internal + data eksternal opsional.
    Return dict berisi 3 trending_topics siap dipakai video_producer.

    external_trends: list of {keyword, interest/value} dari Google Trends atau sumber lain.
    """
    internal = _get_internal_trending_signals()
    internal_summary = _format_internal_signals(internal)

    ext_lines = []
    if external_trends:
        for t in external_trends[:10]:
            kw = t.get("keyword") or t.get("query") or t.get("topic", "")
            val = t.get("value") or t.get("interest") or t.get("growth", "")
            if kw:
                ext_lines.append(f"  - {kw}: {val}")
    ext_summary = "\n".join(ext_lines) if ext_lines else "Data tren eksternal tidak disertakan."

    today = datetime.now().strftime("%A, %d %B %Y")

    prompt = f"""{BRAND_CONTEXT}

Hari ini: {today}

SINYAL TREN INTERNAL PPBIB (konten performa terbaik):
{internal_summary}

TREN EKSTERNAL (Google Trends / sumber lain):
{ext_summary}

Berdasarkan sinyal di atas, identifikasi 3 topik video yang SEDANG TRENDING dan relevan untuk PPBIB.
Prioritaskan topik dengan potensi viral tinggi untuk audiens peternak itik.

Return HANYA JSON valid, tidak ada teks lain:

{{
  "analyzed_at": "{datetime.now().isoformat()}",
  "trend_summary": "ringkasan 2-3 kalimat: tren apa yang dominan hari ini di niche peternakan itik",
  "recommended_posting_window": "waktu posting optimal hari ini, contoh: 18:00-20:00 WIB",
  "trending_topics": [
    {{
      "rank": 1,
      "topic": "judul topik video yang sedang tren",
      "urgency": "HIGH",
      "trend_signal": "alasan konkret kenapa ini trending (dari data di atas)",
      "hook": "kalimat pembuka 3 detik yang mengeksploitasi momentum tren",
      "script": "narasi 45-60 detik Bahasa Indonesia, natural, sertakan angka nyata (Rp/kg/ekor/%)",
      "caption": "caption TikTok/IG/FB max 150 karakter + emoji",
      "hashtags": ["#itik", "#ternak", "#pakan", "#ppbib", "#trending"],
      "cta": "call to action 1 kalimat"
    }},
    {{
      "rank": 2,
      "topic": "...",
      "urgency": "MEDIUM",
      "trend_signal": "...",
      "hook": "...",
      "script": "...",
      "caption": "...",
      "hashtags": ["#itik", "#ppbib"],
      "cta": "..."
    }},
    {{
      "rank": 3,
      "topic": "...",
      "urgency": "LOW",
      "trend_signal": "...",
      "hook": "...",
      "script": "...",
      "caption": "...",
      "hashtags": ["#itik", "#ppbib"],
      "cta": "..."
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f"Trending feed response bukan JSON: {raw[:200]}")

    feed = json.loads(match.group())
    _save_trending_feed(feed)
    print(f"[TrendingFeed] Analisis selesai. {len(feed.get('trending_topics', []))} topik trending ditemukan.")
    return feed


def _save_trending_feed(feed: dict):
    os.makedirs("data", exist_ok=True)
    existing = []
    if os.path.exists(TRENDING_FEED_FILE):
        with open(TRENDING_FEED_FILE) as f:
            existing = json.load(f)
    existing.append(feed)
    existing = existing[-30:]  # simpan 30 entri terakhir
    with open(TRENDING_FEED_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"[TrendingFeed] Disimpan: {TRENDING_FEED_FILE}")


def get_latest_trending_feed() -> dict | None:
    """Load trending feed terbaru."""
    if not os.path.exists(TRENDING_FEED_FILE):
        return None
    with open(TRENDING_FEED_FILE) as f:
        data = json.load(f)
    return data[-1] if data else None


def get_top_trending_topic(urgency_filter: str | None = None) -> dict | None:
    """
    Ambil topik trending teratas dari feed terbaru.
    urgency_filter: "HIGH", "MEDIUM", atau "LOW" untuk filter prioritas.
    """
    feed = get_latest_trending_feed()
    if not feed:
        return None
    topics = feed.get("trending_topics", [])
    if not topics:
        return None
    if urgency_filter:
        filtered = [t for t in topics if t.get("urgency") == urgency_filter]
        return filtered[0] if filtered else topics[0]
    return topics[0]


def format_trending_feed_wa(feed: dict) -> str:
    """Format trending feed untuk notifikasi WhatsApp."""
    topics = feed.get("trending_topics", [])
    urgency_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
    lines = [
        "📈 *Trending Feed PPBIB — Sinyal Tren Hari Ini*",
        "",
        f"📊 {feed.get('trend_summary', '')}",
        f"⏰ Window posting: *{feed.get('recommended_posting_window', '-')}*",
        "",
        "─" * 30,
        "*🔥 TOPIK VIDEO TRENDING:*",
        "",
    ]
    for t in topics:
        icon = urgency_icon.get(t.get("urgency", "LOW"), "⚪")
        lines += [
            f"{icon} *#{t['rank']} {t['topic']}* ({t.get('urgency', '')})",
            f"📌 {t.get('trend_signal', '')}",
            f"🪄 Hook: _{t.get('hook', '')}_",
            "",
        ]
    lines += [
        "─" * 30,
        "_Produksi video trending HIGH priority dimulai otomatis._",
    ]
    return "\n".join(lines)
