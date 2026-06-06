"""
Instagram Graph API auth via Facebook OAuth.
Setup: buat Facebook App di developers.facebook.com, aktifkan Instagram Graph API,
lalu set env vars INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET, INSTAGRAM_REDIRECT_URI.
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
GRAPH_BASE = "https://graph.facebook.com/v19.0"

SCOPES = [
    "instagram_basic",
    "instagram_manage_insights",
    "pages_read_engagement",
    "pages_show_list",
]


def get_auth_url() -> str:
    params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": ",".join(SCOPES),
        "response_type": "code",
        "state": "ppbib_ig_auth",
    }
    return "https://www.facebook.com/v19.0/dialog/oauth?" + urlencode(params)


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
