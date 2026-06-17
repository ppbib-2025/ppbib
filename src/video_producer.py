"""
Video Producer — pipeline lengkap: script → MP4 siap upload.

Mode AI (SILICONFLOW_API_KEY diset):
  1. Claude convert script → visual prompt (Wan 2.2 style)
  2. SiliconFlow Wan 2.2 generate visual → raw_video.mp4
  3. edge-tts (ArdiNeural) generate voiceover.mp3 + subtitle.srt
  4. FFmpeg compose: visual + voiceover + subtitle burn + BGM → final.mp4

Mode Lokal (taruh clip di assets/clips/):
  1. Pilih clip acak dari assets/clips/
  2. edge-tts (ArdiNeural) generate voiceover.mp3 + subtitle.srt
  3. FFmpeg compose: clip + voiceover + subtitle burn + BGM → final.mp4
  Tidak butuh SiliconFlow API key — $0 biaya video generation.
"""
import os
from datetime import datetime
from anthropic import Anthropic
from src.tts_engine import generate_tts
from src.video_composer import (
    compose_full_video,
    get_local_clip,
    get_random_bgm,
    ffmpeg_available,
    has_local_clips,
)
from src.content_generator import get_todays_content
from src.trending_feed_analyzer import get_top_trending_topic

VIDEO_DIR = "data/videos"

_USE_AI = bool(os.getenv("SILICONFLOW_API_KEY"))


def _ai_available() -> bool:
    return _USE_AI


def script_to_visual_prompt(script: str, topic: str, hook: str) -> str:
    """Convert script narasi Indonesia ke visual prompt Inggris untuk Wan 2.2."""
    client = Anthropic()
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


def _get_raw_video_ai(topic: str, script: str, hook: str, raw_path: str) -> str:
    """Generate visual via SiliconFlow, download ke raw_path. Return video_url."""
    from src.siliconflow_api import generate_video, download_video
    visual_prompt = script_to_visual_prompt(script, topic, hook)
    print(f"[VideoProducer] Visual prompt:\n{visual_prompt}")
    video_url = generate_video(prompt=visual_prompt, duration=5, image_size="720x1280")
    download_video(video_url, raw_path)
    return video_url, visual_prompt


def _get_raw_video_local(raw_path: str) -> str:
    """Pilih clip lokal acak. Return path clip (symlink/copy ke raw_path)."""
    import shutil
    clip = get_local_clip()
    if not clip:
        raise RuntimeError(
            "Tidak ada clip di assets/clips/. "
            "Taruh file .mp4 atau .mov di sana, atau set SILICONFLOW_API_KEY untuk mode AI."
        )
    shutil.copy2(clip, raw_path)
    return clip


def produce_video(video_content: dict) -> dict:
    """
    Generate 1 video dari konten dict.
    Otomatis pilih mode AI atau lokal berdasarkan ketersediaan API key & clip.
    Return info lengkap video yang sudah jadi.
    """
    topic  = video_content["topic"]
    script = video_content["script"]
    hook   = video_content["hook"]

    date_str   = datetime.now().strftime("%Y%m%d")
    safe_topic = topic[:25].replace(" ", "_").replace("/", "-")
    raw_path   = os.path.join(VIDEO_DIR, f"{date_str}_{safe_topic}_raw.mp4")
    final_path = os.path.join(VIDEO_DIR, f"{date_str}_{safe_topic}.mp4")

    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs("data/audio", exist_ok=True)

    print(f"[VideoProducer] Produksi: {topic}")

    # ── Pilih sumber visual ───────────────────────────────────────────────────
    video_url     = None
    visual_prompt = None
    clip_source   = None

    if _ai_available():
        print("[VideoProducer] Mode: AI (SiliconFlow Wan 2.2)")
        video_url, visual_prompt = _get_raw_video_ai(topic, script, hook, raw_path)
    elif has_local_clips():
        print("[VideoProducer] Mode: Clip lokal (assets/clips/)")
        clip_source = _get_raw_video_local(raw_path)
    else:
        raise RuntimeError(
            "Tidak ada sumber visual. "
            "Set SILICONFLOW_API_KEY atau taruh clip MP4 di assets/clips/."
        )

    # ── TTS voiceover + subtitle SRT ─────────────────────────────────────────
    tts_text   = f"{hook}. {script}"
    audio_path = os.path.join("data/audio", f"{date_str}_{safe_topic}.mp3")
    srt_path   = os.path.join("data/audio", f"{date_str}_{safe_topic}.srt")
    generate_tts(tts_text, output_path=audio_path, srt_path=srt_path)

    # ── Compose: visual + voiceover + subtitle + BGM → final.mp4 ─────────────
    if ffmpeg_available():
        bgm_path = get_random_bgm()
        if bgm_path:
            print(f"[VideoProducer] BGM: {os.path.basename(bgm_path)}")
        compose_full_video(
            video_path=raw_path,
            audio_path=audio_path,
            srt_path=srt_path,
            output_path=final_path,
            bgm_path=bgm_path,
        )
        if os.path.exists(raw_path) and raw_path != final_path:
            os.remove(raw_path)
    else:
        print("[VideoProducer] ffmpeg tidak tersedia — simpan raw video.")
        final_path = raw_path

    return {
        "topic":         topic,
        "hook":          hook,
        "script":        script,
        "caption":       video_content.get("caption", ""),
        "hashtags":      video_content.get("hashtags", []),
        "cta":           video_content.get("cta", ""),
        "visual_prompt": visual_prompt or f"[clip lokal: {os.path.basename(clip_source or '')}]",
        "video_url":     video_url or "",
        "audio_path":    audio_path,
        "video_path":    final_path,
        "mode":          "ai" if _ai_available() else "local_clip",
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
    hashtag_str = " ".join(info.get("hashtags", []))
    mode_label  = "🎬 AI Wan 2.2" if info.get("mode") == "ai" else "📹 Clip lokal"
    lines = [
        f"✅ *Video Siap Upload!* {mode_label}",
        f"🎬 {info['topic']}",
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
        "_Upload ke TikTok + IG Reels + FB Reels_",
    ]
    return "\n".join(lines)


def format_trending_video_tg(info: dict) -> str:
    """Notifikasi Telegram untuk video dari trending feed."""
    hashtag_str = " ".join(info.get("hashtags", []))
    mode_label  = "🎬 AI Wan 2.2" if info.get("mode") == "ai" else "📹 Clip lokal"
    lines = [
        f"📈 *Video Trending Siap Upload!* {mode_label}",
        f"🎬 {info['topic']}",
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
        "_⚡ Konten reaktif tren hari ini — upload segera!_",
        "_Upload ke TikTok + IG Reels + FB Reels_",
    ]
    return "\n".join(lines)


# Backward-compat aliases
format_video_ready_wa    = format_video_ready_tg
format_trending_video_wa = format_trending_video_tg
