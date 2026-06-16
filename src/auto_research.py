"""
Auto Research — evaluasi performa konten mingguan dan optimalkan strategi.
Loop: ukur metrik → analisis pola → update strategi → generate konten lebih baik.
Dijalankan otomatis tiap Sabtu 17:00, sebelum content generation Minggu 18:00.
"""
import json
import os
import re
from datetime import datetime, timedelta
from anthropic import Anthropic
from src.analytics import _load

client = Anthropic()

STRATEGY_FILE = "data/strategy_insights.json"
TIKTOK_ANALYTICS_FILE = "data/analytics_tiktok.json"
IG_ANALYTICS_FILE = "data/analytics_instagram.json"
FB_ANALYTICS_FILE = "data/analytics_facebook.json"
CONTENT_QUEUE_FILE = "data/content_queue.json"


def _load_last_week_plan() -> dict | None:
    if not os.path.exists(CONTENT_QUEUE_FILE):
        return None
    with open(CONTENT_QUEUE_FILE) as f:
        queue = json.load(f)
    return queue[-1] if queue else None


def _get_recent_performance(days: int = 7) -> dict:
    """Ambil data performa konten dari N hari terakhir per platform."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    result = {"tiktok": [], "instagram": [], "facebook": []}

    tiktok_history = _load(TIKTOK_ANALYTICS_FILE)
    for vid_id, data in tiktok_history.items():
        recent = [s for s in data.get("snapshots", []) if s["time"] >= cutoff]
        if not recent:
            continue
        latest = recent[-1]
        views = latest.get("view_count", 0)
        likes = latest.get("like_count", 0)
        comments = latest.get("comment_count", 0)
        shares = latest.get("share_count", 0)
        er = round((likes + comments + shares) / max(views, 1) * 100, 2)
        result["tiktok"].append({
            "title": (data.get("title") or data.get("description", ""))[:80],
            "view_count": views,
            "like_count": likes,
            "comment_count": comments,
            "share_count": shares,
            "engagement_rate": er,
        })
    result["tiktok"].sort(key=lambda x: x["engagement_rate"], reverse=True)

    ig_history = _load(IG_ANALYTICS_FILE)
    for pid, data in ig_history.items():
        recent = [s for s in data.get("snapshots", []) if s["time"] >= cutoff]
        if not recent:
            continue
        latest = recent[-1]
        likes = latest.get("like_count", 0)
        comments = latest.get("comments_count", 0)
        impressions = latest.get("impressions", 0)
        er = round((likes + comments) / max(impressions, 1) * 100, 2)
        result["instagram"].append({
            "caption": data.get("caption", "")[:80],
            "media_type": data.get("media_type", "IMAGE"),
            "like_count": likes,
            "comments_count": comments,
            "impressions": impressions,
            "engagement_rate": er,
        })
    result["instagram"].sort(key=lambda x: x["engagement_rate"], reverse=True)

    fb_history = _load(FB_ANALYTICS_FILE)
    for pid, data in fb_history.items():
        recent = [s for s in data.get("snapshots", []) if s["time"] >= cutoff]
        if not recent:
            continue
        latest = recent[-1]
        likes = latest.get("like_count", 0)
        comments = latest.get("comment_count", 0)
        shares = latest.get("share_count", 0)
        impressions = latest.get("impressions", 0)
        er = round((likes + comments + shares) / max(impressions, 1) * 100, 2)
        result["facebook"].append({
            "message": data.get("message", "")[:80],
            "like_count": likes,
            "comment_count": comments,
            "share_count": shares,
            "impressions": impressions,
            "engagement_rate": er,
        })
    result["facebook"].sort(key=lambda x: x["engagement_rate"], reverse=True)

    return result


def load_strategy_insights() -> dict:
    """Load strategi hasil auto research. Return empty dict jika belum ada."""
    if not os.path.exists(STRATEGY_FILE):
        return {}
    with open(STRATEGY_FILE) as f:
        return json.load(f)


def _save_strategy_insights(insights: dict):
    os.makedirs("data", exist_ok=True)
    with open(STRATEGY_FILE, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    print(f"[AutoResearch] Insights disimpan: {STRATEGY_FILE}")


def run_weekly_evaluation() -> dict:
    """
    Loop utama auto research:
    1. Kumpulkan performa konten 7 hari terakhir
    2. Bandingkan dengan rencana konten yang dijalankan
    3. Minta Claude ekstrak pola pemenang
    4. Simpan strategi untuk dipakai generate konten minggu depan
    Return: dict insights yang disimpan.
    """
    print("[AutoResearch] Memulai evaluasi mingguan...")

    performance = _get_recent_performance(days=7)
    last_plan = _load_last_week_plan()
    previous = load_strategy_insights()

    perf_lines = []
    if performance["tiktok"]:
        perf_lines.append("=== TIKTOK (7 hari terakhir) ===")
        for i, v in enumerate(performance["tiktok"][:5], 1):
            perf_lines.append(
                f'{i}. "{v["title"]}"\n'
                f'   Views: {v["view_count"]:,} | Likes: {v["like_count"]:,} | '
                f'Komentar: {v["comment_count"]:,} | Share: {v["share_count"]:,} | ER: {v["engagement_rate"]}%'
            )
    if performance["instagram"]:
        perf_lines.append("\n=== INSTAGRAM (7 hari terakhir) ===")
        for i, p in enumerate(performance["instagram"][:5], 1):
            perf_lines.append(
                f'{i}. [{p["media_type"]}] "{p["caption"]}"\n'
                f'   Likes: {p["like_count"]:,} | Impresi: {p["impressions"]:,} | ER: {p["engagement_rate"]}%'
            )
    if performance["facebook"]:
        perf_lines.append("\n=== FACEBOOK (7 hari terakhir) ===")
        for i, p in enumerate(performance["facebook"][:5], 1):
            perf_lines.append(
                f'{i}. "{p["message"]}"\n'
                f'   Likes: {p["like_count"]:,} | Share: {p["share_count"]:,} | ER: {p["engagement_rate"]}%'
            )
    perf_summary = "\n".join(perf_lines) if perf_lines else "Belum ada data performa minggu ini."

    plan_lines = ["(tidak ada data rencana konten)"]
    if last_plan:
        plan_lines = [f'Tema: "{last_plan.get("week_theme", "")}"']
        for v in last_plan.get("videos", []):
            plan_lines.append(f'- {v["day"]}: "{v["topic"]}" | Hook: "{v["hook"][:60]}"')
    plan_summary = "\n".join(plan_lines)

    prev_strategy = previous.get("strategy_prompt", "(belum ada — ini iterasi pertama)")
    prev_iteration = previous.get("iteration", 0)

    prompt = f"""Kamu adalah research analyst untuk PPBIB — brand edukasi peternak itik Indonesia.
Tugasmu: analisis performa konten minggu ini, ekstrak pola yang bisa direplikasi, buat strategi lebih baik untuk minggu depan.

PERFORMA KONTEN MINGGU INI:
{perf_summary}

RENCAN KONTEN YANG DIJALANKAN:
{plan_summary}

STRATEGI SEBELUMNYA (iterasi {prev_iteration}):
{prev_strategy}

Return HANYA JSON valid:

{{
  "iteration": {prev_iteration + 1},
  "week_analyzed": "{datetime.now().strftime('%Y-%m-%d')}",
  "top_performing_patterns": {{
    "hook_styles": ["pola hook yang berhasil, contoh: 'mulai dengan angka kerugian'"],
    "winning_topics": ["topik dengan engagement tertinggi minggu ini"],
    "best_formats": ["format konten terbaik: video step-by-step, carousel perbandingan, dll"],
    "avoid_patterns": ["pola yang underperform minggu ini"]
  }},
  "avg_er_tiktok": 0.0,
  "avg_er_instagram": 0.0,
  "avg_er_facebook": 0.0,
  "strategy_prompt": "Instruksi strategi konten 3-5 kalimat. Spesifik dan actionable: apa yang harus direplikasi, apa yang harus dihindari, format apa yang paling perform berdasarkan data di atas.",
  "wa_summary": "Ringkasan evaluasi 4-5 baris untuk WhatsApp. Singkat, padat, berisi angka ER dan insight utama."
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f"Auto research response bukan JSON: {raw[:200]}")

    insights = json.loads(match.group())
    insights["_raw_top_performers"] = {
        "tiktok": performance["tiktok"][:3],
        "instagram": performance["instagram"][:3],
        "facebook": performance["facebook"][:3],
    }

    _save_strategy_insights(insights)
    print(f"[AutoResearch] Selesai. Iterasi #{insights.get('iteration', '?')}")
    print(f"[AutoResearch] Strategi baru: {insights.get('strategy_prompt', '')[:120]}...")
    return insights
