"""
Instagram API auth — dua jalur:
  A. Facebook Login (Graph API, graph.facebook.com): butuh INSTAGRAM_APP_ID/
     INSTAGRAM_APP_SECRET/INSTAGRAM_REDIRECT_URI + IG terhubung ke FB Page.
  B. Instagram Login (graph.instagram.com): token dibuat dari dashboard
     Meta (Kasus penggunaan → Instagram API → Buat token), lalu disimpan
     ke TOKEN_FILE dengan login_type="instagram_login". Jalur ini yang aktif.
"""
import os
import json
import requests
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("INSTAGRAM_APP_ID")
APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")
REDIRECT_URI = os.getenv("INSTAGRAM_REDIRECT_URI")
TOKEN_FILE = "data/tokens/instagram_token.json"
GRAPH_VERSION = "v23.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
IG_LOGIN_BASE = f"https://graph.instagram.com/{GRAPH_VERSION}"

SCOPES = [
    "instagram_basic",
    "instagram_manage_insights",
    "pages_read_engagement",
    "pages_show_list",
]


def get_auth_url() -> str:
    if not all((APP_ID, APP_SECRET, REDIRECT_URI)):
        missing = [n for n, v in {
            "INSTAGRAM_APP_ID": APP_ID,
            "INSTAGRAM_APP_SECRET": APP_SECRET,
            "INSTAGRAM_REDIRECT_URI": REDIRECT_URI,
        }.items() if not v]
        raise RuntimeError(
            f"Env belum lengkap, kurang: {', '.join(missing)}. "
            "Isi di .env lalu coba lagi."
        )
    params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": ",".join(SCOPES),
        "response_type": "code",
        "state": "ppbib_ig_auth",
    }
    return f"https://www.facebook.com/{GRAPH_VERSION}/dialog/oauth?" + urlencode(params)


def exchange_code_for_token(code: str) -> dict:
    # Short-lived token
    resp = requests.get(f"{GRAPH_BASE}/oauth/access_token", params={
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    })
    short = resp.json()
    if "access_token" not in short:
        return short

    # Tukar ke long-lived token (60 hari)
    long_resp = requests.get(f"{GRAPH_BASE}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short["access_token"],
    })
    long_data = long_resp.json()
    if "access_token" in long_data:
        long_data["saved_at"] = datetime.now().isoformat()
        _save_token(long_data)
    return long_data


def _save_token(token_data: dict):
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def load_token() -> dict | None:
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def refresh_long_lived_token() -> dict:
    """Perpanjang long-lived token (~60 hari). Jalankan via cron tiap ~30 hari."""
    token = load_token()
    if not token:
        raise RuntimeError("Belum ada token. Buat dulu dari dashboard Meta.")
    if token.get("login_type") == "instagram_login":
        resp = requests.get(f"{IG_LOGIN_BASE}/refresh_access_token", params={
            "grant_type": "ig_refresh_token",
            "access_token": token["access_token"],
        })
        data = resp.json()
        if "access_token" in data:
            token["access_token"] = data["access_token"]
            token["saved_at"] = datetime.now().isoformat()
            _save_token(token)
        return data
    resp = requests.get(f"{GRAPH_BASE}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": token["access_token"],
    })
    data = resp.json()
    if "access_token" in data:
        data["saved_at"] = datetime.now().isoformat()
        _save_token(data)
    return data
