"""
Video Composer — gabungkan video (visual) + audio (TTS) via FFmpeg.
Butuh ffmpeg terinstall di server (Railway support ffmpeg via nixpacks).
"""
import os
import subprocess

COMPOSED_DIR = "data/videos/composed"


def compose_video_audio(
    video_path: str,
    audio_path: str,
    output_path: str | None = None,
) -> str:
    """
    Gabungkan video MP4 (visual) + audio MP3 (TTS voiceover).
    Audio di-loop jika video lebih panjang, atau dipotong jika audio lebih panjang.
    Return: path file output MP4 final.
    """
    os.makedirs(COMPOSED_DIR, exist_ok=True)
    if output_path is None:
        base = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(COMPOSED_DIR, f"{base}_final.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",          # potong di mana yang lebih pendek habis dulu
        "-map", "0:v:0",
        "-map", "1:a:0",
        output_path,
    ]

    print(f"[Composer] Menggabungkan video + audio...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg gagal:\n{result.stderr[-500:]}")

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[Composer] Selesai: {output_path} ({size_mb:.1f} MB)")
    return output_path


def ffmpeg_available() -> bool:
    """Cek apakah ffmpeg terinstall di sistem."""
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    return result.returncode == 0
