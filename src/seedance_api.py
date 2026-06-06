"""
Seedance 2.0 (Dola Seed) API via fal.ai.
Model ByteDance dengan kemampuan multi-shot storyboard dalam 1 generate.

Setup:
  pip install fal-client
  Set FAL_KEY di .env (daftar di fal.ai)
"""
import os
import fal_client
from dotenv import load_dotenv

load_dotenv()

# fal_client otomatis baca FAL_KEY dari env
MODEL_T2V = "bytedance/seedance-2.0/text-to-video"
MODEL_FAST = "bytedance/seedance-2.0/fast/text-to-video"


def generate_video(
    storyboard_prompt: str,
    duration: str = "10",
    aspect_ratio: str = "9:16",
    resolution: str = "720p",
    generate_audio: bool = True,
    fast_mode: bool = False,
) -> str:
    """
    Generate video multi-shot dari storyboard prompt.

    storyboard_prompt format:
        "Scene 1 description. Cut scene to Scene 2 description. Cut scene to Scene 3."

    Seedance memahami 'Cut scene to' sebagai perpindahan shot baru.
    Maksimal ~6 shots per video, durasi total 4-15 detik.

    Return: URL video MP4.
    """
    if not os.getenv("FAL_KEY"):
        raise RuntimeError("FAL_KEY belum di-set di .env (daftar di fal.ai)")

    model = MODEL_FAST if fast_mode else MODEL_T2V

    result = fal_client.subscribe(
        model,
        arguments={
            "prompt": storyboard_prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "generate_audio": generate_audio,
        },
    )
    url = result.get("video", {}).get("url", "")
    if not url:
        raise RuntimeError(f"Seedance tidak return video URL: {result}")
    print(f"[Seedance] Video selesai: {url}")
    return url


def download_video(url: str, save_path: str) -> str:
    """Download video MP4 dari URL ke path lokal."""
    import requests
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = os.path.getsize(save_path) / 1024 / 1024
    print(f"[Seedance] Tersimpan: {save_path} ({size_mb:.1f} MB)")
    return save_path
