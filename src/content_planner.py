"""AI-powered content planner using Claude to select clips and write captions."""

import json
import re
from anthropic import Anthropic

client = Anthropic()

SYSTEM_PROMPT = """Kamu adalah content planner TikTok yang ahli di niche budidaya ikan (aquaculture).

Target audiens: petani ikan, pemula budidaya, penggemar agribisnis.
Gaya konten: edukatif, engaging, sedikit santai — seperti petani yang berbagi pengalaman nyata.
Bahasa: Indonesia yang natural, sesekali pakai istilah teknis (tapi tetap mudah dipahami).

Kamu tahu apa yang viral di TikTok: hook kuat di 3 detik pertama, visual yang memukau, CTA yang jelas."""


def plan_daily_content(
    available_clips: dict[str, list[dict]],
    config: dict,
    target_date: str,
    used_clips: list[str] | None = None,
) -> dict:
    """
    Ask Claude to plan today's content: pick clips, assign scenes, write caption & hashtags.

    Returns a structured content plan dict.
    """
    clips_summary = {
        cat: [c["name"] for c in clips]
        for cat, clips in available_clips.items()
        if clips
    }

    templates_info = {
        k: {"title": v["title"], "structure": v["structure"], "topic_hints": v["topic_hints"]}
        for k, v in config["templates"].items()
    }

    scene_types_info = {
        k: {"description": v["description"], "preferred_categories": v["preferred_categories"]}
        for k, v in config["scene_types"].items()
    }

    previously_used = used_clips or []

    prompt = f"""Tanggal hari ini: {target_date}

Klip tersedia di Google Drive (dikelompokkan per kategori):
{json.dumps(clips_summary, indent=2, ensure_ascii=False)}

Klip yang sudah dipakai sebelumnya (hindari mengulang):
{json.dumps(previously_used, ensure_ascii=False)}

Template konten yang tersedia:
{json.dumps(templates_info, indent=2, ensure_ascii=False)}

Tipe scene yang tersedia:
{json.dumps(scene_types_info, indent=2, ensure_ascii=False)}

Tugas kamu:
1. Pilih template yang paling cocok untuk hari ini
2. Susun urutan scene sesuai template
3. Pilih klip terbaik untuk tiap scene (pilih klip yang BELUM pernah dipakai jika memungkinkan)
4. Tulis hook text yang bikin orang langsung nonton (max 7 kata)
5. Tulis caption TikTok yang engaging (max 150 kata, gunakan emoji)
6. Tentukan hashtag (10-15 hashtag)

Format jawaban HANYA JSON berikut (tanpa teks lain):
{{
  "template": "nama_template",
  "title": "judul internal konten hari ini",
  "hook_text": "teks hook maks 7 kata",
  "scenes": [
    {{
      "scene_type": "hook",
      "clip_name": "nama_klip.mp4",
      "category": "kategori_klip",
      "duration_seconds": 4,
      "text_overlay": "teks di video atau null"
    }}
  ],
  "caption": "caption TikTok lengkap dengan emoji",
  "hashtags": ["#tag1", "#tag2"]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)
