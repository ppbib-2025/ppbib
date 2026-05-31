"""Downloads selected clips and assembles them into the final TikTok video."""

from pathlib import Path

from .drive_client import DriveClient
from .video_processor import concatenate_clips, process_clip


def _find_clip(clip_name: str, category: str, clips_by_category: dict) -> dict | None:
    candidates = clips_by_category.get(category, [])
    name_stripped = clip_name.lower().removesuffix(".mp4")
    for c in candidates:
        if c["name"].lower().removesuffix(".mp4") == name_stripped:
            return c
    # Fallback: search across all categories
    for cat_clips in clips_by_category.values():
        for c in cat_clips:
            if c["name"].lower().removesuffix(".mp4") == name_stripped:
                return c
    return None


def build_video(
    content_plan: dict,
    clips_by_category: dict,
    output_dir: Path,
    drive: DriveClient,
    video_cfg: dict,
) -> Path:
    """
    Download and process each scene clip, then concatenate into the final video.
    Returns path to final_video.mp4.
    """
    output_dir = Path(output_dir)
    tmp_dir = output_dir / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    hook_text = content_plan.get("hook_text", "")
    processed: list[Path] = []

    for i, scene in enumerate(content_plan["scenes"]):
        clip_name = scene.get("clip_name") or scene.get("clip", "")
        category = scene.get("category", "")
        duration = float(scene.get("duration_seconds", 5))
        scene_type = scene.get("scene_type", "")

        text_overlay = scene.get("text_overlay")
        if scene_type == "hook" and not text_overlay:
            text_overlay = hook_text or None
        elif scene_type == "cta" and not text_overlay:
            text_overlay = "Follow untuk tips budidaya ikan!"

        clip_info = _find_clip(clip_name, category, clips_by_category)
        if not clip_info:
            print(f"  [!] Clip not found: '{clip_name}' (category={category}) — skipping scene {i+1}")
            continue

        # Download
        raw_path = tmp_dir / f"raw_{i:02d}_{clip_info['name']}"
        print(f"  [{i+1}/{len(content_plan['scenes'])}] {scene_type}: {clip_info['name']}")
        drive.download_clip(clip_info["id"], raw_path)

        # Process
        processed_path = tmp_dir / f"scene_{i:02d}.mp4"
        process_clip(raw_path, processed_path, video_cfg, duration=duration, text=text_overlay)
        processed.append(processed_path)

        raw_path.unlink()

    if not processed:
        raise RuntimeError("No scenes could be processed. Check clip names in the content plan.")

    final_path = output_dir / "final_video.mp4"
    print(f"  Assembling {len(processed)} scenes into final video...")
    concatenate_clips(processed, final_path)

    for p in processed:
        if p.exists():
            p.unlink()
    if tmp_dir.exists():
        tmp_dir.rmdir()

    return final_path
