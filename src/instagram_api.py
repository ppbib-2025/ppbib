"""
Instagram Graph API — ambil postingan organik + insights performa.
Membutuhkan Instagram Business/Creator Account yang terhubung ke Facebook Page.
"""
import requests
from src.instagram_auth import load_token

BASE = "https://graph.facebook.com/v19.0"


def _access_token() -> str:
    token = load_token()
    if not token:
        raise RuntimeError("Token Instagram belum ada. Jalankan: python setup_instagram_token.py")
    return token["access_token"]


def get_ig_account() -> tuple[str, str]:
    """Return (ig_user_id, page_access_token) dari Facebook Page yang terhubung."""
    token = _access_token()
    pages_resp = requests.get(
        f"{BASE}/me/accounts",
        params={"access_token": token, "fields": "id,name,access_token"}
    )
    pages = pages_resp.json().get("data", [])
    if not pages:
        raise RuntimeError("Tidak ada Facebook Page ditemukan di akun ini.")

    page = pages[0]
    page_token = page["access_token"]
    page_id = page["id"]

    ig_resp = requests.get(
        f"{BASE}/{page_id}",
        params={"fields": "instagram_business_account", "access_token": page_token}
    )
    ig_id = ig_resp.json().get("instagram_business_account", {}).get("id")
    if not ig_id:
        raise RuntimeError(
            "Tidak ada Instagram Business Account terhubung ke Page ini. "
            "Pastikan akun IG sudah diubah ke Business/Creator dan terhubung ke Page."
        )
    return ig_id, page_token


def get_media_list(limit: int = 20) -> list:
    """Ambil daftar postingan IG terbaru beserta metrik dasar."""
    ig_id, page_token = get_ig_account()
    resp = requests.get(
        f"{BASE}/{ig_id}/media",
        params={
            "fields": "id,caption,media_type,timestamp,like_count,comments_count,thumbnail_url,media_url",
            "limit": limit,
            "access_token": page_token,
        }
    )
    posts = resp.json().get("data", [])
    # Simpan page_token di tiap post untuk get_media_insights
    for p in posts:
        p["_page_token"] = page_token
    return posts


def get_media_insights(media_id: str, page_token: str, media_type: str = "IMAGE") -> dict:
    """
    Ambil insights satu postingan.
    Metrics berbeda per tipe:
      IMAGE/CAROUSEL_ALBUM: impressions, reach, engagement, saved
      VIDEO/REELS: + video_views
    """
    base_metrics = ["impressions", "reach", "engagement", "saved"]
    if media_type in ("VIDEO", "REELS"):
        base_metrics.append("video_views")

    resp = requests.get(
        f"{BASE}/{media_id}/insights",
        params={
            "metric": ",".join(base_metrics),
            "access_token": page_token,
        }
    )
    data = resp.json().get("data", [])
    if not data:
        return {}
    return {item["name"]: item["values"][0]["value"] for item in data}


def get_account_insights() -> dict:
    """Insights mingguan level akun: reach, impressions, profile_views."""
    ig_id, page_token = get_ig_account()
    resp = requests.get(
        f"{BASE}/{ig_id}/insights",
        params={
            "metric": "impressions,reach,profile_views",
            "period": "week",
            "access_token": page_token,
        }
    )
    data = resp.json().get("data", [])
    return {item["name"]: item["values"][-1]["value"] for item in data}
