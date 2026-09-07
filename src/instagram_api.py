"""
Instagram API — ambil postingan organik + insights performa.

Dua jalur (dipilih otomatis dari data/tokens/instagram_token.json):
  B. Instagram Login (aktif): graph.instagram.com, token dari dashboard Meta.
  A. Facebook Login (cadangan): graph.facebook.com, butuh IG terhubung ke FB Page.
"""
import requests
from src.instagram_auth import load_token, IG_LOGIN_BASE

BASE = "https://graph.facebook.com/v23.0"

# Metrik insights yang valid di Instagram Login API (per media).
_IG_MEDIA_METRICS = "views,reach,likes,comments,shares,saved"


def _token() -> dict:
    token = load_token()
    if not token:
        raise RuntimeError(
            "Token Instagram belum ada. Buat dari dashboard Meta "
            "(Kasus penggunaan → Instagram API → Buat token)."
        )
    return token


def _is_ig_login(token: dict) -> bool:
    return token.get("login_type") == "instagram_login"


def _access_token() -> str:
    return _token()["access_token"]


def get_ig_login_user() -> dict:
    """Profil akun IG untuk jalur Instagram Login."""
    resp = requests.get(
        f"{IG_LOGIN_BASE}/me",
        params={
            "fields": "id,username,account_type,media_count",
            "access_token": _access_token(),
        },
    )
    return resp.json()


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
    token = _token()
    if _is_ig_login(token):
        tok = token["access_token"]
        ig_id = token.get("ig_user_id") or get_ig_login_user().get("id")
        resp = requests.get(
            f"{IG_LOGIN_BASE}/{ig_id}/media",
            params={
                "fields": "id,caption,media_type,timestamp,like_count,comments_count",
                "limit": limit,
                "access_token": tok,
            },
        )
        posts = resp.json().get("data", [])
        for p in posts:
            p["_page_token"] = ""  # tidak dipakai di jalur Instagram Login
        return posts

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


def _parse_insights(data: list) -> dict:
    if not data:
        return {}
    return {item["name"]: item["values"][0]["value"] for item in data}


def get_media_insights(media_id: str, page_token: str = "", media_type: str = "IMAGE") -> dict:
    """
    Ambil insights satu postingan.
    Jalur Instagram Login: views, reach, likes, comments, shares, saved.
    Jalur Facebook Login: impressions, reach, engagement, saved (+video_views).
    """
    token = _token()
    if _is_ig_login(token):
        resp = requests.get(
            f"{IG_LOGIN_BASE}/{media_id}/insights",
            params={
                "metric": _IG_MEDIA_METRICS,
                "access_token": token["access_token"],
            },
        )
        return _parse_insights(resp.json().get("data", []))

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
    return _parse_insights(resp.json().get("data", []))


def get_account_insights() -> dict:
    """Insights mingguan level akun: reach, impressions, profile_views."""
    token = _token()
    if _is_ig_login(token):
        resp = requests.get(
            f"{IG_LOGIN_BASE}/{token.get('ig_user_id') or get_ig_login_user().get('id')}/insights",
            params={
                "metric": "views,reach",
                "period": "day",
                "access_token": token["access_token"],
            },
        )
        data = resp.json().get("data", [])
        return {item["name"]: item["values"][-1]["value"] for item in data}

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
