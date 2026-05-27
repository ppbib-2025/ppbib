import os
import json
import hashlib
import base64
import secrets
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")
TOKEN_FILE = "data/tokens/tiktok_token.json"
VERIFIER_FILE = "data/tokens/code_verifier.txt"

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


def _generate_pkce():
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


def get_auth_url():
    code_verifier, code_challenge = _generate_pkce()
    os.makedirs(os.path.dirname(VERIFIER_FILE), exist_ok=True)
    with open(VERIFIER_FILE, "w") as f:
        f.write(code_verifier)

    params = {
        "client_key": CLIENT_KEY,
        "scope": "user.info.basic,video.list,comment.list,comment.list.manage",
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": "ppbib_automation",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return AUTH_URL + "?" + urlencode(params)


def exchange_code_for_token(code: str) -> dict:
    code_verifier = ""
    if os.path.exists(VERIFIER_FILE):
        with open(VERIFIER_FILE) as f:
            code_verifier = f.read().strip()

    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
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
