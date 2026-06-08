"""
Video Producer — pipeline: script → storyboard → Seedance 2.0 → MP4 siap upload.

Alur:
  1. Ambil script hari ini dari content_queue.json
  2. Claude convert script narasi → storyboard 5 shot (Cut scene to...)
  3. Submit ke Seedance 2.0 via fal.ai
  4. Download MP4 ke data/videos/
  5. Kirim notifikasi WA
"""
import os
from datetime import datetime
import os
from anthropic import Anthropic
from src.seedance_api import generate_video, download_video
from src.content_generator import get_todays_content

_api_key = os.getenv("DINOIKI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=_api_key)
VIDEO_DIR = "data/videos"


def script_to_storyboard(script: str, topic: str, hook: str) -> str:
    """
    Convert script narasi Bahasa Indonesia ke storyboard prompt Inggris
    format Seedance: deskripsi per shot dipisah 'Cut scene to'.

    Script = apa yang DIUCAPKAN.
    Storyboard = apa yang TERLIHAT di kamera, shot per shot.
    """
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": f"""Convert this Indonesian duck farming video script into a 5-shot storyboard prompt for Seedance 2.0 AI video generator.

Topic: {topic}
Hook: {hook}
Script: {script}

Rules:
- Write in English only
- Exactly 5 shots separated by "Cut scene to"
- Each shot = what the CAMERA SEES, not what is spoken
- Setting: Indonesian rural duck farm, warm natural lighting
- Shot structure:
  Shot 1 (hook visual): attention-grabbing opening scene
  Shot 2 (problem): show the challenge/pain point
  Shot 3 (solution): show the process/solution
  Shot 4 (result): show positive outcome with numbers/proof
  Shot 5 (CTA): farmer smiling, call-to-action moment
- Keep each shot description under 25 words
- NO narration text, NO subtitles in description

Output only the prompt, no explanation:"""
        }]
    )
    return message.content[0].text.strip()


def produce_video(video_content: dict) -> dict:
    """
    Generate 1 video dari konten dict.
    Return info lengkap video yang sudah jadi.
    """
    topic = video_content["topic"]
    script = video_content["script"]
    hook = video_content["hook"]

    print(f"[VideoProducer] Produksi: {topic}")

    # 1. Convert script → storyboard prompt
    storyboard = script_to_storyboard(script, topic, hook)
    print(f"[VideoProducer] Storyboard:\n{storyboard}")

    # 2. Generate di Seedance 2.0
    video_url = generate_video(
        storyboard_prompt=storyboard,
        duration="10",
        aspect_ratio="9:16",
        resolution="720p",
        generate_audio=True,
    )

    # 3. Download MP4
    date_str = datetime.now().strftime("%Y%m%d")
    safe_topic = topic[:25].replace(" ", "_").replace("/", "-")
    save_path = os.path.join(VIDEO_DIR, f"{date_str}_{safe_topic}.mp4")
    download_video(video_url, save_path)

    return {
        "topic": topic,
        "hook": hook,
        "script": script,
        "caption": video_content.get("caption", ""),
        "hashtags": video_content.get("hashtags", []),
        "cta": video_content.get("cta", ""),
        "storyboard": storyboard,
        "video_url": video_url,
        "video_path": save_path,
    }


def produce_todays_video() -> dict:
    """Ambil konten hari ini dari queue dan generate videonya."""
    content = get_todays_content()
    if not content or "video" not in content:
        print("[VideoProducer] Tidak ada video terjadwal hari ini.")
        return {}
    return produce_video(content["video"])


def format_video_ready_wa(info: dict) -> str:
    """Notifikasi WA: video siap + caption + script lengkap."""
    hashtag_str = " ".join(info.get("hashtags", []))
    storyboard_preview = info.get("storyboard", "")[:200] + "..."
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
        f"*CTA:* {info['cta']}",
        "",
        "─" * 30,
        "*SCRIPT voiceover:*",
        f"\U0001fab4 Hook: {info['hook']}",
        info["script"],
        "",
        "─" * 30,
        "*Storyboard Seedance:*",
        storyboard_preview,
        "",
        "_Upload ke TikTok + IG Reels + FB Reels_",
    ]
    return "\n".join(lines)
