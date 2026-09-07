"""
Facebook Page organik analytics via Graph API.
Menggunakan token yang sama dengan Instagram (INSTAGRAM_APP_ID/SECRET).
Tidak perlu auth tambahan jika Instagram sudah di-setup.
"""
import requests
from src.instagram_auth import load_token

BASE = "https://graph.facebook.com/v23.0"


def _access_token() -> str:
    token = load_token()
    if not token:
        raise RuntimeError(
            "Token Facebook/Instagram belum ada. "
            "Jalankan: python setup_instagram_token.py"
        )
    return token["access_token"]


def get_page_account() -> tuple[str, str]:
    """Return (page_id, page_access_token)."""
    token = _access_token()
    resp = requests.get(
        f"{BASE}/me/accounts",
        params={"access_token": token, "fields": "id,name,access_token"},
    )
    pages = resp.json().get("data", [])
    if not pages:
        raise RuntimeError("Tidak ada Facebook Page ditemukan di akun ini.")
    page = pages[0]
    return page["id"], page["access_token"]


def get_posts(limit: int = 20) -> list:
    """Ambil postingan Facebook Page terbaru beserta metrik dasar."""
    page_id, page_token = get_page_account()
    resp = requests.get(
        f"{BASE}/{page_id}/posts",
        params={
            "fields": "id,message,created_time,likes.summary(true),comments.summary(true),shares",
            "limit": limit,
            "access_token": page_token,
        },
    )
    posts = resp.json().get("data", [])
    for p in posts:
        p["_page_token"] = page_token
        p["like_count"] = p.get("likes", {}).get("summary", {}).get("total_count", 0)
        p["comment_count"] = p.get("comments", {}).get("summary", {}).get("total_count", 0)
        p["share_count"] = p.get("shares", {}).get("count", 0)
    return posts


def get_post_insights(post_id: str, page_token: str) -> dict:
    """Impressions, reach, dan engaged_users satu post."""
    resp = requests.get(
        f"{BASE}/{post_id}/insights",
        params={
            "metric": "post_impressions,post_impressions_unique,post_engaged_users",
            "access_token": page_token,
        },
    )
    data = resp.json().get("data", [])
    if not data:
        return {}
    return {item["name"]: item["values"][0]["value"] for item in data}
