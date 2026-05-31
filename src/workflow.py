"""
Main agentic workflow: daily TikTok content generation from Google Drive footage.

Usage:
    python -m src.workflow                   # generate today's content
    python -m src.workflow --date 2026-06-01 # specific date
    python -m src.workflow --dry-run         # AI planning only, skip download/video
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OUTPUT_BASE = Path("output")
CONFIG_PATH = Path("scenes_config.json")
USED_CLIPS_PATH = Path("output/used_clips.json")


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_used_clips() -> list[str]:
    if USED_CLIPS_PATH.exists():
        with open(USED_CLIPS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_used_clips(used: list[str], new_clips: list[str]) -> None:
    combined = list(dict.fromkeys(used + new_clips))  # deduplicate, preserve order
    USED_CLIPS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USED_CLIPS_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)


def _save_caption(plan: dict, output_dir: Path) -> Path:
    path = output_dir / "caption.txt"
    hashtags = " ".join(plan.get("hashtags", []))
    content = f"{plan['caption']}\n\n{hashtags}"
    path.write_text(content, encoding="utf-8")
    return path


def _save_plan(plan: dict, output_dir: Path) -> Path:
    path = output_dir / "content_plan.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    return path


def _check_ffmpeg() -> bool:
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def run(target_date: str | None = None, dry_run: bool = False) -> None:
    today = target_date or str(date.today())
    output_dir = OUTPUT_BASE / today
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"  TikTok Content Workflow — {today}")
    print(f"{'='*50}\n")

    # Validate environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("[ERROR] ANTHROPIC_API_KEY not set. Copy .env.example → .env and fill in your key.")

    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

    if not Path(creds_path).exists():
        sys.exit(f"[ERROR] Google credentials not found at '{creds_path}'.\n"
                 "Download OAuth2 credentials from Google Cloud Console → APIs & Services → Credentials.")

    config = _load_config()

    # ── Step 1: Connect to Google Drive ──────────────────────────────────────
    print("[1/4] Connecting to Google Drive...")
    from .drive_client import DriveClient
    drive = DriveClient(creds_path, token_path, config)
    print("      Connected.\n")

    # ── Step 2: List available clips ──────────────────────────────────────────
    print("[2/4] Fetching available clips from Drive...")
    clips = drive.list_all_clips()
    total = sum(len(v) for v in clips.values())
    for cat, cat_clips in clips.items():
        if cat_clips:
            print(f"      {cat}: {len(cat_clips)} clips — {', '.join(c['name'] for c in cat_clips[:3])}{'...' if len(cat_clips) > 3 else ''}")
    print(f"      Total: {total} clips\n")

    # ── Step 3: AI content planning ───────────────────────────────────────────
    print("[3/4] Planning content with Claude AI...")
    from .content_planner import plan_daily_content
    used_clips = _load_used_clips()
    plan = plan_daily_content(clips, config, today, used_clips)

    print(f"      Template  : {plan.get('template', '—')}")
    print(f"      Title     : {plan.get('title', '—')}")
    print(f"      Hook      : {plan.get('hook_text', '—')}")
    print(f"      Scenes    : {len(plan.get('scenes', []))}")

    plan_file = _save_plan(plan, output_dir)
    caption_file = _save_caption(plan, output_dir)
    print(f"      Plan saved: {plan_file}")
    print(f"      Caption   : {caption_file}\n")

    if dry_run:
        print("─── DRY RUN — Caption Preview ───")
        print(caption_file.read_text(encoding="utf-8"))
        print("─────────────────────────────────")
        print("\n[DRY RUN] Skipping video download and processing.")
        return

    if not _check_ffmpeg():
        sys.exit("[ERROR] ffmpeg not found. Install with: sudo apt install ffmpeg  (or brew install ffmpeg)")

    # ── Step 4: Download clips & build video ──────────────────────────────────
    print("[4/4] Building video...")
    from .scene_builder import build_video
    video_path = build_video(plan, clips, output_dir, drive, config["video"])

    # Track used clips
    used_names = [s.get("clip_name", s.get("clip", "")) for s in plan.get("scenes", [])]
    _save_used_clips(used_clips, used_names)

    # ── Done ──────────────────────────────────────────────────────────────────
    size_mb = video_path.stat().st_size / 1_048_576
    print(f"\n{'='*50}")
    print(f"  Done! Output → {output_dir.absolute()}")
    print(f"{'='*50}")
    print(f"  Video   : {video_path.name} ({size_mb:.1f} MB)")
    print(f"  Caption : {caption_file.name}")
    print(f"  Plan    : {plan_file.name}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate daily TikTok content from Google Drive footage"
    )
    parser.add_argument("--date", help="Target date (YYYY-MM-DD), defaults to today")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="AI planning and caption only — skip video download/processing",
    )
    args = parser.parse_args()
    run(target_date=args.date, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
