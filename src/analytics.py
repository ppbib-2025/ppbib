"""
Analytics modul — snapshot harian + laporan mingguan TikTok & Instagram.
Data disimpan di data/analytics_tiktok.json dan data/analytics_instagram.json.
Laporan teks disimpan di data/reports/.
"""
import json
import os
from datetime import datetime

TIKTOK_ANALYTICS_FILE = "data/analytics_tiktok.json"
IG_ANALYTICS_FILE = "data/analytics_instagram.json"
REPORT_DIR = "data/reports"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _save(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _er_tiktok(v: dict) -> float:
    """Engagement rate TikTok = (like+comment+share) / view * 100."""
    views = v.get("view_count") or 1
    eng = v.get("like_count", 0) + v.get("comment_count", 0) + v.get("share_count", 0)
    return round(eng / views * 100, 2)


def _er_ig(like_count: int, comments_count: int, impressions: int) -> float:
    """Engagement rate IG = (like+comment) / impressions * 100."""
    imp = impressions or 1
    return round((like_count + comments_count) / imp * 100, 2)


def _label(text: str, limit: int = 45) -> str:
    text = (text or "(tanpa judul)").strip().replace("\n", " ")
    return text[:limit] + "..." if len(text) > limit else text


# ── TikTok ───────────────────────────────────────────────────────────────────

def collect_tiktok_metrics() -> list:
    """Snapshot metrics TikTok sekarang dan simpan ke history."""
    from src.tiktok_api import get_my_videos
    videos = get_my_videos(max_count=20)
    history = _load(TIKTOK_ANALYTICS_FILE)
    now = datetime.now().isoformat()

    for v in videos:
        vid_id = v["id"]
        if vid_id not in history:
            history[vid_id] = {
                "title": v.get("title", ""),
                "description": v.get("video_description", ""),
                "create_time": v.get("create_time"),
                "snapshots": [],
            }
        history[vid_id]["snapshots"].append({
            "time": now,
            "view_count": v.get("view_count", 0),
            "like_count": v.get("like_count", 0),
            "comment_count": v.get("comment_count", 0),
            "share_count": v.get("share_count", 0),
        })

    _save(TIKTOK_ANALYTICS_FILE, history)
    print(f"[Analytics] TikTok: {len(videos)} video disimpan.")
    return videos


# ── Instagram ─────────────────────────────────────────────────────────────────

def collect_instagram_metrics() -> list:
    """Snapshot metrics Instagram sekarang dan simpan ke history."""
    try:
        from src.instagram_api import get_media_list, get_media_insights
    except Exception as e:
        print(f"[Analytics] Skip Instagram: {e}")
        return []

    posts = get_media_list(limit=20)
    history = _load(IG_ANALYTICS_FILE)
    now = datetime.now().isoformat()

    for p in posts:
        pid = p["id"]
        page_token = p.pop("_page_token", "")
        media_type = p.get("media_type", "IMAGE")
        insights = get_media_insights(pid, page_token, media_type)

        if pid not in history:
            history[pid] = {
                "caption": p.get("caption", ""),
                "media_type": media_type,
                "timestamp": p.get("timestamp"),
                "snapshots": [],
            }
        history[pid]["snapshots"].append({
            "time": now,
            "like_count": p.get("like_count", 0),
            "comments_count": p.get("comments_count", 0),
            "impressions": insights.get("impressions", 0),
            "reach": insights.get("reach", 0),
            "saved": insights.get("saved", 0),
            "video_views": insights.get("video_views", 0),
        })

    _save(IG_ANALYTICS_FILE, history)
    print(f"[Analytics] Instagram: {len(posts)} post disimpan.")
    return posts


# ── Laporan ───────────────────────────────────────────────────────────────────

def _tiktok_section(videos: list) -> list[str]:
    if not videos:
        return ["  (tidak ada data TikTok)"]

    sorted_views = sorted(videos, key=lambda v: v.get("view_count", 0), reverse=True)
    sorted_er = sorted(videos, key=_er_tiktok, reverse=True)

    total_views = sum(v.get("view_count", 0) for v in videos)
    total_likes = sum(v.get("like_count", 0) for v in videos)
    total_comments = sum(v.get("comment_count", 0) for v in videos)
    total_shares = sum(v.get("share_count", 0) for v in videos)
    avg_er = round(sum(_er_tiktok(v) for v in videos) / len(videos), 2)

    lines = [
        f"  Total video   : {len(videos)}",
        f"  Total views   : {total_views:,}",
        f"  Total likes   : {total_likes:,}",
        f"  Total komentar: {total_comments:,}",
        f"  Total share   : {total_shares:,}",
        f"  Rata-rata ER  : {avg_er}%",
        "",
        "  TOP 5 VIEWS:",
    ]
    for i, v in enumerate(sorted_views[:5], 1):
        title = _label(v.get("title") or v.get("video_description"))
        lines.append(
            f"  {i}. {title}\n"
            f"     👁{v.get('view_count',0):,}  "
            f"❤{v.get('like_count',0):,}  "
            f"💬{v.get('comment_count',0):,}  "
            f"📤{v.get('share_count',0):,}  "
            f"ER:{_er_tiktok(v)}%"
        )

    lines += ["", "  TOP 3 ENGAGEMENT RATE:"]
    for i, v in enumerate(sorted_er[:3], 1):
        title = _label(v.get("title") or v.get("video_description"))
        lines.append(f"  {i}. {title}  →  ER:{_er_tiktok(v)}%  👁{v.get('view_count',0):,}")

    return lines


def _ig_section(posts: list) -> list[str]:
    if not posts:
        return ["  (tidak ada data Instagram, atau token belum di-setup)"]

    def er(p):
        return _er_ig(
            p.get("like_count", 0),
            p.get("comments_count", 0),
            p.get("_imp", 0),  # injected saat build laporan
        )

    total_likes = sum(p.get("like_count", 0) for p in posts)
    total_comments = sum(p.get("comments_count", 0) for p in posts)

    sorted_likes = sorted(posts, key=lambda p: p.get("like_count", 0), reverse=True)

    lines = [
        f"  Total post     : {len(posts)}",
        f"  Total likes    : {total_likes:,}",
        f"  Total komentar : {total_comments:,}",
        "",
        "  TOP 5 LIKES:",
    ]
    for i, p in enumerate(sorted_likes[:5], 1):
        caption = _label(p.get("caption", ""))
        media_type = p.get("media_type", "IMAGE")
        icon = {"IMAGE": "🖼", "VIDEO": "🎬", "CAROUSEL_ALBUM": "📑", "REELS": "🎬"}.get(media_type, "📄")
        lines.append(
            f"  {i}. {icon} {caption}\n"
            f"     ❤{p.get('like_count',0):,}  "
            f"💬{p.get('comments_count',0):,}"
        )
    return lines


def generate_report() -> str:
    """Buat laporan performa mingguan TikTok + Instagram. Return string laporan."""
    from src.tiktok_api import get_my_videos

    videos = get_my_videos(max_count=20)

    try:
        from src.instagram_api import get_media_list
        posts = get_media_list(limit=20)
        # hapus _page_token sebelum dipakai di laporan
        for p in posts:
            p.pop("_page_token", None)
    except Exception:
        posts = []

    now_str = datetime.now().strftime("%d %b %Y %H:%M")
    sep = "═" * 54
    thin = "─" * 54

    lines = [
        sep,
        "  LAPORAN PERFORMA KONTEN ORGANIK PPBIB",
        f"  {now_str}",
        sep,
        "",
        "[ TIKTOK ]",
        thin,
        *_tiktok_section(videos),
        "",
        "[ INSTAGRAM ]",
        thin,
        *_ig_section(posts),
        "",
        sep,
    ]

    report = "\n".join(lines)

    os.makedirs(REPORT_DIR, exist_ok=True)
    fname = os.path.join(REPORT_DIR, f"report_{datetime.now().strftime('%Y%m%d')}.txt")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[Analytics] Laporan disimpan: {fname}")

    return report


def get_top_content(platform: str = "tiktok", n: int = 3) -> list[dict]:
    """
    Return n konten terbaik berdasarkan engagement rate.
    Dipakai AI content generator untuk belajar pola konten yang perform.
    """
    if platform == "tiktok":
        history = _load(TIKTOK_ANALYTICS_FILE)
        results = []
        for vid_id, data in history.items():
            if not data["snapshots"]:
                continue
            latest = data["snapshots"][-1]
            er = _er_tiktok(latest)
            results.append({
                "id": vid_id,
                "title": data.get("title") or data.get("description", ""),
                "view_count": latest.get("view_count", 0),
                "engagement_rate": er,
            })
        return sorted(results, key=lambda x: x["engagement_rate"], reverse=True)[:n]

    elif platform == "instagram":
        history = _load(IG_ANALYTICS_FILE)
        results = []
        for pid, data in history.items():
            if not data["snapshots"]:
                continue
            latest = data["snapshots"][-1]
            er = _er_ig(
                latest.get("like_count", 0),
                latest.get("comments_count", 0),
                latest.get("impressions", 0),
            )
            results.append({
                "id": pid,
                "caption": data.get("caption", ""),
                "media_type": data.get("media_type", "IMAGE"),
                "impressions": latest.get("impressions", 0),
                "engagement_rate": er,
            })
        return sorted(results, key=lambda x: x["engagement_rate"], reverse=True)[:n]

    return []
