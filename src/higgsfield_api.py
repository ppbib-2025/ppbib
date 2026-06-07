"""
Higgsfield AI Video Generation API.
Daftar & dapatkan API key di: https://higgsfield.ai
Docs: https://docs.higgsfield.ai
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("HIGGSFIELD_API_KEY")
BASE = "https://api.higgsfield.ai/v1"


def _headers() -> dict:
    if not API_KEY:
        raise RuntimeError("HIGGSFIELD_API_KEY belum di-set di .env")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def generate_video(
    prompt: str,
    duration: int = 8,
    aspect_ratio: str = "9:16",
    style: str = "cinematic",
) -> str:
    """
    Submit video generation job ke Higgsfield.
    aspect_ratio: "9:16" untuk TikTok/Reels, "1:1" untuk feed IG
    style: "cinematic", "documentary", "ugc", "lifestyle"
    Return: job_id
    """
    resp = requests.post(
        f"{BASE}/generate",
        headers=_headers(),
        json={
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "style": style,
        },
        timeout=30,
    )
    data = resp.json()
    if "job_id" not in data:
        raise RuntimeError(f"Gagal submit Higgsfield job: {data}")
    print(f"[Higgsfield] Job submitted: {data['job_id']}")
    return data["job_id"]


def get_status(job_id: str) -> dict:
    """Cek status job generation."""
    resp = requests.get(
        f"{BASE}/status/{job_id}",
        headers=_headers(),
        timeout=15,
    )
    return resp.json()


def wait_for_completion(job_id: str, timeout: int = 600, poll_interval: int = 15) -> str:
    """
    Poll sampai video selesai dirender. Return video URL.
    Timeout default 10 menit (Higgsfield biasanya 3-8 menit).
    """
    elapsed = 0
    while elapsed < timeout:
        status = get_status(job_id)
        state = status.get("status", "pending")

        if state == "completed":
            url = status.get("video_url") or status.get("output_url", "")
            if not url:
                raise RuntimeError("Video selesai tapi URL kosong.")
            print(f"[Higgsfield] Selesai: {url}")
            return url

        if state == "failed":
            raise RuntimeError(f"Higgsfield gagal render: {status.get('error', 'unknown')}")

        print(f"[Higgsfield] {state}... ({elapsed}s/{timeout}s)")
        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Video tidak selesai dalam {timeout} detik.")


def download_video(url: str, save_path: str) -> str:
    """Download video MP4 ke path lokal."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = os.path.getsize(save_path) / 1024 / 1024
    print(f"[Higgsfield] Video tersimpan: {save_path} ({size_mb:.1f} MB)")
    return save_path
