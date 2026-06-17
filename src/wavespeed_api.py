"""
WaveSpeed AI Video Generation API.
Docs: https://wavespeed.ai/docs

Setup:
  Set WAVESPEED_API_KEY di .env (daftar di wavespeed.ai)

Model yang tersedia (termurah → terbaik kualitas):
  wavespeed-ai/wan-2.2/t2v-480p-ultra-fast  → 480p, paling cepat & murah
  wavespeed-ai/wan-2.2/t2v-720p-ultra-fast  → 720p, recommended untuk konten
  wavespeed-ai/wan-2.2/t2v-720p             → 720p standard (lebih lambat)
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("WAVESPEED_API_KEY", "")
BASE_URL = "https://api.wavespeed.ai/api/v3"

# Ganti model ini untuk trade-off harga vs kualitas
DEFAULT_MODEL = "wavespeed-ai/wan-2.2/t2v-720p-ultra-fast"


def _headers() -> dict:
    if not API_KEY:
        raise RuntimeError("WAVESPEED_API_KEY belum di-set di .env")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def submit_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Submit job ke WaveSpeed. Return request_id untuk polling.
    duration: detik video (max 10 untuk most models)
    aspect_ratio: "9:16" untuk TikTok/Reels vertical
    """
    resp = requests.post(
        f"{BASE_URL}/{model}",
        headers=_headers(),
        json={
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    request_id = data.get("id", "")
    if not request_id:
        raise RuntimeError(f"WaveSpeed tidak return request ID: {resp.text[:300]}")
    print(f"[WaveSpeed] Job submitted: {request_id}")
    return request_id


def wait_for_completion(request_id: str, timeout: int = 600, poll_interval: int = 5) -> str:
    """
    Poll sampai video selesai dirender. Return URL video MP4.
    Timeout default 10 menit.
    """
    url     = f"{BASE_URL}/predictions/{request_id}"
    headers = _headers()
    elapsed = 0

    while elapsed < timeout:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data   = resp.json().get("data", {})
        status = data.get("status", "pending")

        if status == "completed":
            outputs = data.get("outputs", [])
            if not outputs:
                raise RuntimeError("Video selesai tapi outputs kosong.")
            video_url = outputs[0]
            print(f"[WaveSpeed] Selesai: {video_url}")
            return video_url

        if status == "failed":
            raise RuntimeError(f"WaveSpeed gagal render: {data.get('error', 'unknown')}")

        print(f"[WaveSpeed] {status}... ({elapsed}s/{timeout}s)")
        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Video tidak selesai dalam {timeout} detik.")


def generate_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Submit + poll sampai selesai. Return URL video MP4.
    Wrapper convenience untuk dipakai di video_producer.
    """
    request_id = submit_video(prompt, duration, aspect_ratio, model)
    return wait_for_completion(request_id)


def download_video(url: str, save_path: str) -> str:
    """Download video MP4 dari URL ke path lokal."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = os.path.getsize(save_path) / 1024 / 1024
    print(f"[WaveSpeed] Tersimpan: {save_path} ({size_mb:.1f} MB)")
    return save_path
