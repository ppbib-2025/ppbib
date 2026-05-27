import os
import json
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")
TOKEN_FILE = "data/tokens/tiktok_token.json"

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


def get_auth_url():
    params = {
        "client_key": CLIENT_KEY,
        "scope": "user.info.basic,video.list,comment.list,comment.list.manage",
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": "ppbib_automation",
    }
    return AUTH_URL + "?" + urlencode(params)


def exchange_code_for_token(code: str) -> dict:
    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    resp = requests.post(TOKEN_URL, data=payload)
    data = resp.json()
    if "data" in data:
        _save_token(data["data"])
    return data


def refresh_token(refresh_tok: str) -> dict:
    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_tok,
    }
    resp = requests.post(TOKEN_URL, data=payload)
    data = resp.json()
    if "data" in data:
        _save_token(data["data"])
    return data


def load_token() -> dict | None:
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def _save_token(token_data: dict):
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
