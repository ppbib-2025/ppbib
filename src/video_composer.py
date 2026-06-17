"""
Video Composer — gabungkan semua komponen jadi 1 MP4 siap upload via FFmpeg.

Pipeline (mode AI):
  raw_video.mp4 (visual SiliconFlow Wan 2.2)
  + voiceover.mp3 (edge-tts Ardi)
  + subtitle.srt  (edge-tts SubMaker, timing otomatis sinkron)
  + bgm.mp3       (dari assets/music/, volume 20%, di-loop)
  ──────────────────────────────────────────────────────────
  final_video.mp4 (siap upload TikTok / IG Reels / FB Reels)

Pipeline (mode lokal):
  clip.mp4 (footage dari assets/clips/ — rekaman kandang bebek, dll.)
  + voiceover.mp3 + subtitle.srt + bgm.mp3
  ──────────────────────────────────────────────────────────
  final_video.mp4

Butuh: ffmpeg dengan libass (untuk burn subtitle).
Railway: tambahkan "ffmpeg" di nixpacks.toml atau railpack config.
"""
import os
import glob
import random
import subprocess

OUTPUT_DIR = "data/videos"

# Lokasi clip video lokal (footage bebek, kandang, dll.)
_CLIP_SEARCH_DIRS = [
    "assets/clips",
    "data/clips",
    "clips",
]

# Lokasi pencarian BGM — cek semua folder, yang mana ada mp3-nya dipakai
_MUSIC_SEARCH_DIRS = [
    ".",              # root folder ppbib (taruh langsung di sini)
    "assets/music",
    "data/music",
    "music",
]


def get_local_clip() -> str | None:
    """
    Cari clip video lokal (.mp4 / .mov) di assets/clips/ atau folder lain.
    Return path file yang dipilih secara acak, atau None jika tidak ada.
    """
    files = []
    for d in _CLIP_SEARCH_DIRS:
        if os.path.isdir(d):
            files += glob.glob(os.path.join(d, "*.mp4"))
            files += glob.glob(os.path.join(d, "*.mov"))
            files += glob.glob(os.path.join(d, "*.MP4"))
            files += glob.glob(os.path.join(d, "*.MOV"))
    # Filter file terlalu kecil (< 100KB) agar tidak ambil placeholder
    files = [f for f in files if os.path.getsize(f) > 100 * 1024]
    if not files:
        return None
    chosen = random.choice(files)
    print(f"[Composer] Clip lokal: {os.path.basename(chosen)}")
    return chosen


def has_local_clips() -> bool:
    """Cek apakah ada clip video lokal yang tersedia."""
    return get_local_clip() is not None


def get_random_bgm() -> str | None:
    """
    Cari file BGM (.mp3 / .m4a) di beberapa lokasi.
    Bisa taruh langsung di folder ppbib atau di subfolder manapun.
    Return path file yang dipilih secara acak, atau None jika tidak ada.
    """
    files = []
    for d in _MUSIC_SEARCH_DIRS:
        if os.path.isdir(d):
            files += glob.glob(os.path.join(d, "*.mp3"))
            files += glob.glob(os.path.join(d, "*.m4a"))
    # Exclude file yang terlalu kecil (< 50KB) agar tidak salah ambil file lain
    files = [f for f in files if os.path.getsize(f) > 50 * 1024]
    return random.choice(files) if files else None


def compose_full_video(
    video_path: str,
    audio_path: str,
    srt_path: str,
    output_path: str,
    bgm_path: str | None = None,
    bgm_volume: float = 0.20,
) -> str:
    """
    Gabungkan video + voiceover + subtitle + BGM jadi 1 MP4 final.

    bgm_volume: 0.0–1.0, default 0.20 (BGM 20% supaya voiceover tetap jelas).
    Return: path output MP4.
    """
    os.makedirs(os.path.dirname(output_path) or OUTPUT_DIR, exist_ok=True)
    abs_srt = os.path.abspath(srt_path)

    # ── Subtitle style (TikTok / Reels style) ────────────────────────────────
    sub_style = (
        "FontName=Arial,"
        "FontSize=16,"
        "PrimaryColour=&H00FFFFFF,"   # putih
        "OutlineColour=&H00000000,"   # outline hitam
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=1,"
        "Bold=1,"
        "Alignment=2,"                # bawah tengah
        "MarginV=40"
    )
    video_filter = f"subtitles='{abs_srt}':force_style='{sub_style}'"

    # ── Build FFmpeg command ──────────────────────────────────────────────────
    cmd = ["ffmpeg", "-y"]

    if bgm_path and os.path.exists(bgm_path):
        # Input: video, voiceover, BGM (di-loop otomatis)
        cmd += ["-i", video_path, "-i", audio_path, "-stream_loop", "-1", "-i", bgm_path]
        audio_filter = (
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume={bgm_volume}[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        filter_complex = f"{audio_filter};[0:v]{video_filter}[vout]"
        cmd += [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
        ]
    else:
        # Tanpa BGM
        cmd += ["-i", video_path, "-i", audio_path]
        filter_complex = f"[0:v]{video_filter}[vout];[1:a]volume=1.0[aout]"
        cmd += [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
        ]

    cmd += [
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",    # streaming-friendly
        "-shortest",
        output_path,
    ]

    print(f"[Composer] Render: visual + voiceover + subtitle{' + BGM' if bgm_path else ''}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg gagal:\n{result.stderr[-800:]}")

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[Composer] ✅ Selesai: {output_path} ({size_mb:.1f} MB)")
    return output_path


def ffmpeg_available() -> bool:
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    return result.returncode == 0
