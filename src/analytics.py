"""
Analytics modul — snapshot harian + laporan harian & mingguan.
Platform: TikTok, Instagram, Facebook.
Laporan dikirim via WhatsApp dan disimpan di data/reports/.
"""
import json
import os
from datetime import datetime

TIKTOK_ANALYTICS_FILE = "data/analytics_tiktok.json"
IG_ANALYTICS_FILE = "data/analytics_instagram.json"
FB_ANALYTICS_FILE = "data/analytics_facebook.json"
REPORT_DIR = "data/reports"


# ── Helpers ─────────────────────────────────────────────────────────────────

def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _save(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_report(filename: str, content: str):
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Analytics] Laporan disimpan: {path}")


def _label(text: str, limit: int = 42) -> str:
    text = (text or "(tanpa teks)").strip().replace("\n", " ")
    return text[:limit] + "..." if len(text) > limit else text


def _er_tiktok(v: dict) -> float:
    views = v.get("view_count") or 1
    eng = v.get("like_count", 0) + v.get("comment_count", 0) + v.get("share_count", 0)
    return round(eng / views * 100, 2)


def _er_ig(like_count: int, comments_count: int, impressions: int) -> float:
    imp = impressions or 1
    return round((like_count + comments_count) / imp * 100, 2)


def _er_fb(like_count: int, comment_count: int, share_count: int, impressions: int) -> float:
    imp = impressions or 1
    return round((like_count + comment_count + share_count) / imp * 100, 2)


# ── Collect Metrics ──────────────────────────────────────────────────────────

def collect_tiktok_metrics() -> list:
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


def collect_instagram_metrics() -> list:
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
            "video_views": insights.get("video_views", insights.get("views", 0)),
            "views": insights.get("views", 0),
            "likes": insights.get("likes", 0),
            "shares": insights.get("shares", 0),
        })
    _save(IG_ANALYTICS_FILE, history)
    print(f"[Analytics] Instagram: {len(posts)} post disimpan.")
    return posts


def collect_facebook_metrics() -> list:
    try:
        from src.facebook_api import get_posts, get_post_insights
    except Exception as e:
        print(f"[Analytics] Skip Facebook: {e}")
        return []
    posts = get_posts(limit=20)
    history = _load(FB_ANALYTICS_FILE)
    now = datetime.now().isoformat()
    for p in posts:
        pid = p["id"]
        page_token = p.pop("_page_token", "")
        insights = get_post_insights(pid, page_token)
        if pid not in history:
            history[pid] = {
                "message": p.get("message", ""),
                "created_time": p.get("created_time"),
                "snapshots": [],
            }
        history[pid]["snapshots"].append({
            "time": now,
            "like_count": p.get("like_count", 0),
            "comment_count": p.get("comment_count", 0),
            "share_count": p.get("share_count", 0),
            "impressions": insights.get("post_impressions", 0),
            "reach": insights.get("post_impressions_unique", 0),
            "engaged_users": insights.get("post_engaged_users", 0),
        })
    _save(FB_ANALYTICS_FILE, history)
    print(f"[Analytics] Facebook: {len(posts)} post disimpan.")
    return posts


# ── Section Builders ─────────────────────────────────────────────────────────

def _tiktok_section(videos: list, mode: str = "daily") -> list[str]:
    if not videos:
        return ["(tidak ada data TikTok)"]
    total_views = sum(v.get("view_count", 0) for v in videos)
    total_likes = sum(v.get("like_count", 0) for v in videos)
    total_comments = sum(v.get("comment_count", 0) for v in videos)
    total_shares = sum(v.get("share_count", 0) for v in videos)
    avg_er = round(sum(_er_tiktok(v) for v in videos) / len(videos), 2)
    best = max(videos, key=lambda v: v.get("view_count", 0))
    best_title = _label(best.get("title") or best.get("video_description"))

    lines = [
        f"\U0001f441 {total_views:,} views  ❤️ {total_likes:,} likes",
        f"\U0001f4ac {total_comments:,} komentar  \U0001f4e4 {total_shares:,} share",
        f"\U0001f4c8 Rata-rata ER: {avg_er}%",
        f"\U0001f3c6 Terbaik: \"{best_title}\"",
        f"   \U0001f441 {best.get('view_count',0):,} views | ER {_er_tiktok(best)}%",
    ]
    if mode == "weekly":
        sorted_views = sorted(videos, key=lambda v: v.get("view_count", 0), reverse=True)
        sorted_er = sorted(videos, key=_er_tiktok, reverse=True)
        lines += ["", "*\U0001f3c6 Top 5 Views:*"]
        for i, v in enumerate(sorted_views[:5], 1):
            t = _label(v.get("title") or v.get("video_description"))
            lines.append(f"{i}. {t}\n   \U0001f441{v.get('view_count',0):,} | ❤{v.get('like_count',0):,} | ER:{_er_tiktok(v)}%")
        lines += ["", "*\U0001f525 Top 3 ER:*"]
        for i, v in enumerate(sorted_er[:3], 1):
            t = _label(v.get("title") or v.get("video_description"))
            lines.append(f"{i}. {t}\n   ER:{_er_tiktok(v)}%  \U0001f441{v.get('view_count',0):,}")
    return lines


def _ig_section(posts: list, mode: str = "daily") -> list[str]:
    if not posts:
        return ["(token Instagram belum di-setup)"]
    total_likes = sum(p.get("like_count", 0) for p in posts)
    total_comments = sum(p.get("comments_count", 0) for p in posts)
    best = max(posts, key=lambda p: p.get("like_count", 0))
    best_caption = _label(best.get("caption", ""))
    icon = {"VIDEO": "\U0001f3ac", "REELS": "\U0001f3ac", "CAROUSEL_ALBUM": "\U0001f4d1"}.get(
        best.get("media_type", ""), "\U0001f5bc"
    )
    lines = [
        f"❤️ {total_likes:,} likes  \U0001f4ac {total_comments:,} komentar",
        f"\U0001f3c6 Terbaik: {icon} \"{best_caption}\"",
        f"   ❤ {best.get('like_count',0):,} likes",
    ]
    if mode == "weekly":
        sorted_ig = sorted(posts, key=lambda p: p.get("like_count", 0), reverse=True)
        lines += ["", "*\U0001f3c6 Top 5 Likes:*"]
        for i, p in enumerate(sorted_ig[:5], 1):
            ic = {"VIDEO": "\U0001f3ac", "REELS": "\U0001f3ac", "CAROUSEL_ALBUM": "\U0001f4d1"}.get(
                p.get("media_type", ""), "\U0001f5bc"
            )
            cap = _label(p.get("caption", ""))
            lines.append(f"{i}. {ic} {cap}\n   ❤{p.get('like_count',0):,} | \U0001f4ac{p.get('comments_count',0):,}")
    return lines


def _fb_section(posts: list, mode: str = "daily") -> list[str]:
    if not posts:
        return ["(token Facebook belum di-setup atau tidak ada post)"] 
    total_likes = sum(p.get("like_count", 0) for p in posts)
    total_comments = sum(p.get("comment_count", 0) for p in posts)
    total_shares = sum(p.get("share_count", 0) for p in posts)
    best = max(posts, key=lambda p: p.get("like_count", 0))
    best_msg = _label(best.get("message", ""))
    lines = [
        f"❤️ {total_likes:,} likes  \U0001f4ac {total_comments:,} komentar  \U0001f501 {total_shares:,} share",
        f"\U0001f3c6 Terbaik: \"{best_msg}\"",
        f"   ❤ {best.get('like_count',0):,} | \U0001f4ac {best.get('comment_count',0):,} | \U0001f501 {best.get('share_count',0):,}",
    ]
    if mode == "weekly":
        sorted_fb = sorted(posts, key=lambda p: p.get("like_count", 0), reverse=True)
        lines += ["", "*\U0001f3c6 Top 5 Likes:*"]
        for i, p in enumerate(sorted_fb[:5], 1):
            msg = _label(p.get("message", ""))
            lines.append(
                f"{i}. {msg}\n"
                f"   ❤{p.get('like_count',0):,} | "
                f"\U0001f4ac{p.get('comment_count',0):,} | "
                f"\U0001f501{p.get('share_count',0):,}"
            )
    return lines


# ── Laporan Harian ───────────────────────────────────────────────────────────

def generate_daily_report() -> str:
    from src.tiktok_api import get_my_videos
    videos = get_my_videos(max_count=20)

    try:
        from src.instagram_api import get_media_list
        ig_posts = get_media_list(limit=10)
        for p in ig_posts:
            p.pop("_page_token", None)
    except Exception:
        ig_posts = []

    try:
        from src.facebook_api import get_posts
        fb_posts = get_posts(limit=10)
        for p in fb_posts:
            p.pop("_page_token", None)
    except Exception:
        fb_posts = []

    now_str = datetime.now().strftime("%d %b %Y")
    sep = "─" * 30
    lines = [f"\U0001f4ca *Ringkasan Harian PPBIB*", f"\U0001f4c5 {now_str}", sep, ""]

    lines += ["\U0001f3ac *TikTok*", *_tiktok_section(videos, mode="daily"), ""]
    lines += ["\U0001f4f7 *Instagram*", *_ig_section(ig_posts, mode="daily"), ""]
    lines += ["\U0001f4d8 *Facebook*", *_fb_section(fb_posts, mode="daily"), ""]

    report = "\n".join(lines)
    _save_report(f"daily_{datetime.now().strftime('%Y%m%d')}.txt", report)
    return report


# ── Laporan Mingguan ─────────────────────────────────────────────────────────

def generate_weekly_report() -> str:
    from src.tiktok_api import get_my_videos
    videos = get_my_videos(max_count=20)

    try:
        from src.instagram_api import get_media_list
        ig_posts = get_media_list(limit=20)
        for p in ig_posts:
            p.pop("_page_token", None)
    except Exception:
        ig_posts = []

    try:
        from src.facebook_api import get_posts
        fb_posts = get_posts(limit=20)
        for p in fb_posts:
            p.pop("_page_token", None)
    except Exception:
        fb_posts = []

    now_str = datetime.now().strftime("%d %b %Y")
    sep = "═" * 30
    thin = "─" * 30
    lines = [f"\U0001f4ca *LAPORAN MINGGUAN PPBIB*", f"\U0001f4c5 Pekan {now_str}", sep, ""]

    lines += ["\U0001f3ac *TIKTOK*", thin, *_tiktok_section(videos, mode="weekly"), ""]
    lines += [thin, "\U0001f4f7 *INSTAGRAM*", thin, *_ig_section(ig_posts, mode="weekly"), ""]
    lines += [thin, "\U0001f4d8 *FACEBOOK*", thin, *_fb_section(fb_posts, mode="weekly"), ""]
    lines += [sep, "_Laporan otomatis dari sistem PPBIB_"]

    report = "\n".join(lines)
    _save_report(f"weekly_{datetime.now().strftime('%Y%m%d')}.txt", report)
    return report


# ── Top Content (untuk AI content generator) ─────────────────────────────────

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
            results.append({
                "id": vid_id,
                "title": data.get("title") or data.get("description", ""),
                "view_count": latest.get("view_count", 0),
                "engagement_rate": _er_tiktok(latest),
            })
        return sorted(results, key=lambda x: x["engagement_rate"], reverse=True)[:n]

    elif platform == "instagram":
        history = _load(IG_ANALYTICS_FILE)
        results = []
        for pid, data in history.items():
            if not data["snapshots"]:
                continue
            latest = data["snapshots"][-1]
            results.append({
                "id": pid,
                "caption": data.get("caption", ""),
                "media_type": data.get("media_type", "IMAGE"),
                "impressions": latest.get("impressions", 0),
                "engagement_rate": _er_ig(
                    latest.get("like_count", 0),
                    latest.get("comments_count", 0),
                    latest.get("impressions", 0),
                ),
            })
        return sorted(results, key=lambda x: x["engagement_rate"], reverse=True)[:n]

    elif platform == "facebook":
        history = _load(FB_ANALYTICS_FILE)
        results = []
        for pid, data in history.items():
            if not data["snapshots"]:
                continue
            latest = data["snapshots"][-1]
            results.append({
                "id": pid,
                "message": data.get("message", ""),
                "impressions": latest.get("impressions", 0),
                "engagement_rate": _er_fb(
                    latest.get("like_count", 0),
                    latest.get("comment_count", 0),
                    latest.get("share_count", 0),
                    latest.get("impressions", 0),
                ),
            })
        return sorted(results, key=lambda x: x["engagement_rate"], reverse=True)[:n]

    return []
