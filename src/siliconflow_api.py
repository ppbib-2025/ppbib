"""
SiliconFlow Video Generation API.
Docs: https://docs.siliconflow.com/en/api-reference/videos/videos_submit

Setup:
  Set SILICONFLOW_API_KEY di .env (daftar di siliconflow.com)

Model text-to-video yang tersedia:
  Wan-AI/Wan2.2-T2V-A14B  → $0.29/video, kualitas terbaik (recommended)
  Wan-AI/Wan2.1-T2V-14B   → $0.29/video, generasi sebelumnya
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("SILICONFLOW_API_KEY", "")
BASE_URL = "https://api.siliconflow.com/v1"

DEFAULT_MODEL = "Wan-AI/Wan2.2-T2V-A14B"


def _headers() -> dict:
    if not API_KEY:
        raise RuntimeError("SILICONFLOW_API_KEY belum di-set di .env")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def submit_video(
    prompt: str,
    duration: int = 5,
    image_size: str = "720x1280",
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Submit job video ke SiliconFlow. Return request_id untuk polling.
    image_size "720x1280" = 720p vertical 9:16 untuk TikTok/Reels.
    duration: 4 atau 5 detik (Wan 2.2 max ~5 detik per generate).
    """
    resp = requests.post(
        f"{BASE_URL}/video/submit",
        headers=_headers(),
        json={
            "model":      model,
            "prompt":     prompt,
            "image_size": image_size,
            "duration":   duration,
        },
        timeout=30,
    )
    resp.raise_for_status()
    body       = resp.json()
    request_id = body.get("requestId") or body.get("request_id", "")
    if not request_id:
        raise RuntimeError(f"SiliconFlow tidak return requestId: {resp.text[:300]}")
    print(f"[SiliconFlow] Job submitted: {request_id}")
    return request_id


def get_status(request_id: str) -> dict:
    """Cek status job. Return dict dengan field status dan results."""
    resp = requests.get(
        f"{BASE_URL}/video/status/{request_id}",
        headers=_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def wait_for_completion(request_id: str, timeout: int = 600, poll_interval: int = 5) -> str:
    """
    Poll sampai video selesai. Return URL video MP4.
    Status SiliconFlow: "InQueue" → "Processing" → "Succeed" / "Failed"
    """
    elapsed = 0
    while elapsed < timeout:
        data   = get_status(request_id)
        status = data.get("status", "")

        if status == "Succeed":
            results   = data.get("results", {})
            video_url = results.get("videos", [{}])[0].get("url", "")
            if not video_url:
                raise RuntimeError("Video Succeed tapi URL kosong.")
            print(f"[SiliconFlow] Selesai: {video_url}")
            return video_url

        if status == "Failed":
            reason = data.get("reason", "unknown")
            raise RuntimeError(f"SiliconFlow gagal render: {reason}")

        print(f"[SiliconFlow] {status}... ({elapsed}s/{timeout}s)")
        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Video tidak selesai dalam {timeout} detik.")


def generate_video(
    prompt: str,
    duration: int = 5,
    image_size: str = "720x1280",
    model: str = DEFAULT_MODEL,
) -> str:
    """Submit + poll sampai selesai. Return URL video MP4."""
    request_id = submit_video(prompt, duration, image_size, model)
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
    print(f"[SiliconFlow] Tersimpan: {save_path} ({size_mb:.1f} MB)")
    return save_path
