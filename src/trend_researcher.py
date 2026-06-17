"""
Trend Researcher — filter dan skor topik trending untuk niche budidaya ikan air tawar premium.
Data trend ditulis oleh rutin Claude Code harian ke data/trend_insights.json.
"""
import json
import os
from datetime import datetime

TREND_INSIGHTS_FILE = "data/trend_insights.json"

# Sinyal intent premium / investasi
PREMIUM_INTENT_KEYWORDS = [
    "investasi", "roi", "modal", "keuntungan", "profit", "bisnis", "komersial",
    "skala besar", "hatchery", "ras", "bioflok", "teknologi modern",
    "kelayakan", "feasibility", "ekspor", "supplier", "kontrak", "kemitraan",
    "harga pasar", "margin", "omzet", "pendapatan", "passive income",
    "kolam komersial", "farm", "budidaya modern", "sertifikasi", "grosir",
    "distributor", "hotel", "restoran", "pasar ekspor",
]

# Sinyal audiens pemula / budget kecil — filter keluar
EXCLUDE_KEYWORDS = [
    "pemula", "murah", "hemat", "cara membuat sendiri", "gratis", "modal kecil",
    "tanpa modal", "sederhana", "rumahan", "ternak sampingan", "tutorial dasar",
]

# Keyword inti niche
NICHE_KEYWORDS = [
    "budidaya ikan", "lele", "nila", "gurame", "patin", "mas", "bawal",
    "kolam terpal", "kolam beton", "sistem ras", "bioflok", "hatchery",
    "pakan ikan", "benih ikan", "pembenihan", "pembesaran ikan",
    "akuakultur", "aquaculture", "ikan air tawar",
]


def load_trend_insights() -> dict:
    """Load insights trend yang ditulis oleh rutin harian."""
    if not os.path.exists(TREND_INSIGHTS_FILE):
        return {}
    with open(TREND_INSIGHTS_FILE) as f:
        return json.load(f)


def save_trend_insights(data: dict):
    """Simpan trend insights (dipanggil oleh rutin Claude Code)."""
    os.makedirs("data", exist_ok=True)
    data["saved_at"] = datetime.now().isoformat()
    with open(TREND_INSIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[TrendResearch] Insights disimpan: {TREND_INSIGHTS_FILE}")


def score_topic_premium_intent(topic: str) -> int:
    """
    Hitung skor premium intent sebuah topik (0-100).
    Skor tinggi = lebih relevan untuk target menengah ke atas.
    """
    topic_lower = topic.lower()
    score = 0
    for kw in PREMIUM_INTENT_KEYWORDS:
        if kw in topic_lower:
            score += 20
    for kw in NICHE_KEYWORDS:
        if kw in topic_lower:
            score += 10
    for kw in EXCLUDE_KEYWORDS:
        if kw in topic_lower:
            score -= 30
    return max(0, min(100, score))


def filter_premium_topics(topics: list) -> list:
    """
    Filter dan urutkan daftar topik berdasarkan relevansi untuk target premium.
    Return list dict: {topic, score, relevant}.
    """
    scored = []
    for topic in topics:
        score = score_topic_premium_intent(topic)
        scored.append({"topic": topic, "score": score, "relevant": score >= 10})
    return sorted(scored, key=lambda x: x["score"], reverse=True)


def get_trend_context_for_content() -> str:
    """
    Return string context trend untuk dimasukkan ke prompt content generator.
    Prioritaskan topik dengan skor premium intent tinggi.
    """
    insights = load_trend_insights()
    if not insights:
        return (
            "Belum ada data trend terkini. Gunakan topik evergreen budidaya ikan air tawar premium: "
            "ROI kolam komersial, perbandingan sistem RAS vs konvensional, "
            "modal dan proyeksi keuntungan skala 1 hektar."
        )

    lines = [f"DATA TREND TERKINI ({insights.get('date', insights.get('saved_at', 'terbaru'))[:10]}):\n"]

    premium_topics = insights.get("premium_topics", [])
    if premium_topics:
        lines.append("Topik premium (intent investasi/bisnis tinggi):")
        for t in premium_topics[:5]:
            label = t if isinstance(t, str) else t.get("topic", "")
            score = "" if isinstance(t, str) else f" (skor: {t.get('score', '')})"
            lines.append(f"  ✓ {label}{score}")

    rising_topics = insights.get("rising_topics", [])
    if rising_topics:
        lines.append("\nTopik sedang naik (momentum bagus untuk konten):")
        for t in rising_topics[:3]:
            lines.append(f"  ↑ {t}")

    youtube_trending = insights.get("youtube_trending", [])
    if youtube_trending:
        lines.append("\nTrending YouTube budidaya ikan:")
        for t in youtube_trending[:3]:
            lines.append(f"  ▶ {t}")

    lines.append(
        "\nGunakan topik di atas sebagai angle konten. "
        "Selalu bingkai dari sudut pandang investor/pebisnis: ROI, modal, proyeksi keuntungan."
    )
    return "\n".join(lines)
