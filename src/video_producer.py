"""
Video Producer — pipeline: script → visual prompt → WaveSpeed AI (Wan 2.2) → MP4 siap upload.

Alur:
  1. Ambil script dari content_queue.json atau trending_feed.json
  2. Claude convert script narasi → visual prompt untuk Wan 2.2
  3. Submit ke WaveSpeed AI (Wan 2.2 720p Ultra Fast)
  4. Poll sampai selesai, download MP4 ke data/videos/
  5. Kirim notifikasi Telegram
"""
import os
from datetime import datetime
from anthropic import Anthropic
from src.siliconflow_api import generate_video, download_video
from src.tts_engine import generate_tts
from src.video_composer import compose_video_audio, ffmpeg_available
from src.content_generator import get_todays_content
from src.trending_feed_analyzer import get_top_trending_topic

client = Anthropic()
VIDEO_DIR = "data/videos"


def script_to_visual_prompt(script: str, topic: str, hook: str) -> str:
    """
    Convert script narasi Bahasa Indonesia ke visual prompt Inggris untuk Wan 2.2.
    Wan 2.2 menerima deskripsi sinematik lengkap dalam 1 prompt, bukan per-shot.
    """
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Convert this Indonesian duck farming video script into a cinematic visual prompt for Wan 2.2 AI video generator (text-to-video).

Topic: {topic}
Hook: {hook}
Script: {script}

Rules:
- Write in English only, max 150 words
- Describe what the CAMERA SEES, not what is spoken
- Setting: Indonesian rural duck farm, golden hour lighting, lush green surroundings
- Flow: start with hook visual → show problem/process → show result → end with farmer smiling
- Include: camera movement (slow pan, close-up, aerial), mood, color palette
- Style: documentary-style, warm cinematic, authentic UGC feel
- NO text overlays, NO subtitles in description

Output only the visual prompt, no explanation:"""
        }]
    )
    return message.content[0].text.strip()


def produce_video(video_content: dict) -> dict:
    """
    Generate 1 video dari konten dict.
    Return info lengkap video yang sudah jadi.
    """
    topic  = video_content["topic"]
    script = video_content["script"]
    hook   = video_content["hook"]

    print(f"[VideoProducer] Produksi: {topic}")

    # 1. Convert script → visual prompt untuk Wan 2.2
    visual_prompt = script_to_visual_prompt(script, topic, hook)
    print(f"[VideoProducer] Visual prompt:\n{visual_prompt}")

    # 2. Generate via SiliconFlow (Wan 2.2 T2V, 720p vertical 9:16)
    video_url = generate_video(
        prompt=visual_prompt,
        duration=5,
        image_size="720x1280",
    )

    # 3. Download raw video MP4 (visual only)
    date_str   = datetime.now().strftime("%Y%m%d")
    safe_topic = topic[:25].replace(" ", "_").replace("/", "-")
    raw_path   = os.path.join(VIDEO_DIR, f"{date_str}_{safe_topic}_raw.mp4")
    download_video(video_url, raw_path)

    # 4. Generate TTS voiceover dari script narasi
    tts_text  = f"{hook}. {script}"
    audio_dir = "data/audio"
    audio_path = os.path.join(audio_dir, f"{date_str}_{safe_topic}.mp3")
    generate_tts(tts_text, output_path=audio_path)

    # 5. Gabungkan video + voiceover (butuh ffmpeg)
    if ffmpeg_available():
        final_path = os.path.join(VIDEO_DIR, f"{date_str}_{safe_topic}.mp4")
        compose_video_audio(raw_path, audio_path, final_path)
        os.remove(raw_path)   # hapus raw setelah compose
    else:
        print("[VideoProducer] ffmpeg tidak tersedia — video tanpa voiceover.")
        final_path = raw_path

    return {
        "topic":         topic,
        "hook":          hook,
        "script":        script,
        "caption":       video_content.get("caption", ""),
        "hashtags":      video_content.get("hashtags", []),
        "cta":           video_content.get("cta", ""),
        "visual_prompt": visual_prompt,
        "video_url":     video_url,
        "audio_path":    audio_path,
        "video_path":    final_path,
    }


def produce_todays_video() -> dict:
    """Ambil konten hari ini dari queue dan generate videonya."""
    content = get_todays_content()
    if not content or "video" not in content:
        print("[VideoProducer] Tidak ada video terjadwal hari ini.")
        return {}
    return produce_video(content["video"])


def produce_trending_video(urgency_filter: str = "HIGH") -> dict:
    """
    Produksi video berdasarkan topik trending dari trending_feed_analyzer.
    Ambil topik dengan urgency tertinggi (default HIGH) dari feed terbaru.
    """
    topic_data = get_top_trending_topic(urgency_filter=urgency_filter)
    if not topic_data:
        topic_data = get_top_trending_topic()
    if not topic_data:
        print("[VideoProducer] Tidak ada trending topic tersedia.")
        return {}
    print(f"[VideoProducer] Trending video: [{topic_data.get('urgency')}] {topic_data['topic']}")
    return produce_video(topic_data)


def format_video_ready_tg(info: dict) -> str:
    """Notifikasi Telegram: video terjadwal siap upload."""
    hashtag_str    = " ".join(info.get("hashtags", []))
    prompt_preview = info.get("visual_prompt", "")[:200] + "..."
    lines = [
        "✅ *Video Siap Upload!*",
        f"🎬 {info['topic']}",
        f"📁 File: `{info['video_path']}`",
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
        f"🪄 Hook: {info['hook']}",
        info["script"],
        "",
        "─" * 30,
        f"*Visual Prompt Wan 2.2:*",
        prompt_preview,
        "",
        "_Upload ke TikTok + IG Reels + FB Reels_",
    ]
    return "\n".join(lines)


def format_trending_video_tg(info: dict) -> str:
    """Notifikasi Telegram untuk video dari trending feed."""
    hashtag_str    = " ".join(info.get("hashtags", []))
    prompt_preview = info.get("visual_prompt", "")[:200] + "..."
    lines = [
        "📈 *Video Trending Siap Upload!*",
        f"🎬 {info['topic']}",
        f"📁 File: `{info['video_path']}`",
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
        f"🪄 Hook: {info['hook']}",
        info["script"],
        "",
        "─" * 30,
        f"*Visual Prompt Wan 2.2:*",
        prompt_preview,
        "",
        "_⚡ Konten reaktif tren hari ini — upload segera!_",
        "_Upload ke TikTok + IG Reels + FB Reels_",
    ]
    return "\n".join(lines)


# Backward-compat aliases (dipakai main.py lama)
format_video_ready_wa    = format_video_ready_tg
format_trending_video_wa = format_trending_video_tg
