import requests
from src.tiktok_auth import load_token

BASE = "https://open.tiktokapis.com/v2"


def _headers():
    token = load_token()
    if not token:
        raise RuntimeError("Token TikTok tidak ditemukan. Login dulu via /tiktok-auth")
    return {"Authorization": f"Bearer {token['access_token']}"}


def get_my_videos() -> list:
    resp = requests.post(
        f"{BASE}/video/list/",
        headers=_headers(),
        json={"max_count": 20},
        params={"fields": "id,title,create_time,comment_count"},
    )
    return resp.json().get("data", {}).get("videos", [])


def get_comments(video_id: str, cursor: int = 0) -> dict:
    resp = requests.get(
        f"{BASE}/video/comment/list/",
        headers=_headers(),
        params={
            "video_id": video_id,
            "max_count": 50,
            "cursor": cursor,
            "fields": "id,text,username,create_time,like_count",
        },
    )
    return resp.json()


def reply_comment(video_id: str, comment_id: str, text: str) -> dict:
    resp = requests.post(
        f"{BASE}/video/comment/reply/",
        headers=_headers(),
        json={"video_id": video_id, "comment_id": comment_id, "text": text},
    )
    return resp.json()
