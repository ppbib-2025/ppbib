"""
Video Producer — pipeline: script → visual prompt → Higgsfield → video siap upload.
Dijalankan tiap hari setelah konten reminder (jam 08:00).
"""
import os
from datetime import datetime
from anthropic import Anthropic
from src.higgsfield_api import generate_video, wait_for_completion, download_video
from src.content_generator import get_todays_content

client = Anthropic()
VIDEO_DIR = "data/videos"

# Gaya visual default untuk konten PPBIB (bisa dioverride per konten)
DEFAULT_STYLE = "documentary"
DEFAULT_DURATION = 8  # detik, cukup untuk B-roll TikTok


def script_to_visual_prompt(script: str, topic: str, hook: str) -> str:
    """
    Konversi script narasi Bahasa Indonesia ke prompt visual Inggris
    yang optimal untuk Higgsfield video generation.
    Script = apa yang diucapkan. Prompt = apa yang terlihat di kamera.
    """
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": (
                f"Convert this Indonesian duck farming video script into a visual prompt "
                f"for Higgsfield AI video generator. Write in English, max 80 words.\n\n"
                f"Topic: {topic}\n"
                f"Hook: {hook}\n"
                f"Script: {script[:300]}\n\n"
                "Focus on: Indonesian rural setting, duck farm scenes, "
                "farmers working, ducks eating/walking, golden hour lighting. "
                "Describe what the CAMERA SEES, not what is spoken. "
                "Start with the main visual scene."
            ),
        }]
    )
    return message.content[0].text.strip()


def produce_video(video_content: dict) -> dict:
    """
    Generate 1 video dari konten dict (dari content_queue.json).
    Return dict info video yang sudah jadi.
    """
    topic = video_content["topic"]
    script = video_content["script"]
    hook = video_content["hook"]

    print(f"[VideoProducer] Mulai produksi: {topic}")

    # 1. Convert script → visual prompt
    visual_prompt = script_to_visual_prompt(script, topic, hook)
    print(f"[VideoProducer] Prompt: {visual_prompt}")

    # 2. Submit ke Higgsfield
    job_id = generate_video(
        prompt=visual_prompt,
        duration=DEFAULT_DURATION,
        aspect_ratio="9:16",
        style=DEFAULT_STYLE,
    )

    # 3. Tunggu render selesai
    video_url = wait_for_completion(job_id, timeout=600)

    # 4. Download MP4
    date_str = datetime.now().strftime("%Y%m%d")
    safe_topic = topic[:25].replace(" ", "_").replace("/", "-")
    filename = f"{date_str}_{safe_topic}.mp4"
    save_path = os.path.join(VIDEO_DIR, filename)
    download_video(video_url, save_path)

    return {
        "topic": topic,
        "hook": hook,
        "script": script,
        "caption": video_content.get("caption", ""),
        "hashtags": video_content.get("hashtags", []),
        "cta": video_content.get("cta", ""),
        "visual_prompt": visual_prompt,
        "video_path": save_path,
        "job_id": job_id,
    }


def produce_todays_video() -> dict:
    """
    Ambil konten hari ini dari queue, generate videonya.
    Dipanggil dari scheduler harian jam 08:00.
    """
    content = get_todays_content()
    if not content or "video" not in content:
        print("[VideoProducer] Tidak ada video terjadwal hari ini.")
        return {}
    return produce_video(content["video"])


def format_video_ready_wa(info: dict) -> str:
    """Pesan WA notifikasi video siap upload."""
    hashtag_str = " ".join(info.get("hashtags", []))
    lines = [
        "✅ *Video Siap Upload!*",
        f"\U0001f3ac {info['topic']}",
        f"\U0001f4c1 File: {info['video_path']}",
        "",
        "─" * 30,
        "*CAPTION (copy-paste):*",
        info["caption"],
        "",
        hashtag_str,
        "",
        f"*CTA:* {info['cta']}",
        "",
        "─" * 30,
        "*SCRIPT voiceover:*",
        f"\U0001fab4 Hook: {info['hook']}",
        info["script"],
        "",
        "_Upload ke TikTok + IG Reels + FB Reels_",
    ]
    return "\n".join(lines)
