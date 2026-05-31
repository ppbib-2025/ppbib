"""Video processing utilities: crop to TikTok 9:16, trim, add text overlay."""

import json
import shutil
import subprocess
from pathlib import Path


def _ffprobe(video_path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    stream = next((s for s in data["streams"] if s["codec_type"] == "video"), {})
    return {
        "width": int(stream.get("width", 1920)),
        "height": int(stream.get("height", 1080)),
        "duration": float(stream.get("duration", 0)),
    }


def _build_text_filter(text: str, cfg: dict) -> str:
    safe = text.replace("'", "’").replace(":", "\\:").replace("\\", "\\\\")
    w, h = cfg["width"], cfg["height"]
    font_size = max(50, w // 18)
    return (
        f"drawtext=text='{safe}'"
        f":fontsize={font_size}"
        f":fontcolor=white"
        f":x=(w-text_w)/2"
        f":y=h*0.12"
        f":box=1:boxcolor=black@0.55:boxborderw=14"
        f":shadowcolor=black@0.8:shadowx=3:shadowy=3"
    )


def process_clip(
    input_path: Path,
    output_path: Path,
    cfg: dict,
    duration: float | None = None,
    text: str | None = None,
) -> Path:
    """
    Crop input clip to TikTok 9:16 format, optionally trim and add text overlay.
    Uses ffmpeg via subprocess.
    """
    info = _ffprobe(input_path)
    w, h = cfg["width"], cfg["height"]
    target_ratio = w / h  # 9:16 ≈ 0.5625

    src_w, src_h = info["width"], info["height"]
    src_ratio = src_w / src_h if src_h > 0 else 1.0

    # Smart crop: preserve center, maintain aspect ratio
    if src_ratio > target_ratio:
        # Wider than 9:16 → crop left/right
        crop_w = int(src_h * target_ratio)
        crop_h = src_h
        crop_x = (src_w - crop_w) // 2
        crop_y = 0
    else:
        # Taller than 9:16 → crop top/bottom (keep upper area for action content)
        crop_w = src_w
        crop_h = int(src_w / target_ratio)
        crop_x = 0
        crop_y = (src_h - crop_h) // 4  # slightly above center

    filters = [
        f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}",
        f"scale={w}:{h}:flags=lanczos",
    ]

    if text:
        filters.append(_build_text_filter(text, cfg))

    cmd = ["ffmpeg", "-y", "-i", str(input_path)]

    if duration:
        clip_duration = info["duration"]
        # Trim from a point that avoids black frames at start
        start = min(0.5, clip_duration * 0.05)
        actual_duration = min(duration, clip_duration - start)
        cmd += ["-ss", str(start), "-t", str(actual_duration)]

    cmd += [
        "-vf", ",".join(filters),
        "-r", str(cfg["fps"]),
        "-c:v", "libx264",
        "-preset", cfg["preset"],
        "-crf", str(cfg["crf"]),
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path),
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def concatenate_clips(clip_paths: list[Path], output_path: Path) -> Path:
    """Concatenate processed clips using ffmpeg concat demuxer."""
    if len(clip_paths) == 1:
        shutil.copy(clip_paths[0], output_path)
        return output_path

    concat_file = output_path.parent / "_concat_list.txt"
    with open(concat_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p.absolute()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    concat_file.unlink()
    return output_path
