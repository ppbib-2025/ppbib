"""
TTS Engine — convert script ke audio MP3 + subtitle SRT via edge-tts (gratis).
Menggunakan Microsoft Edge Neural TTS, tidak butuh API key.

Voice Indonesia:
  id-ID-ArdiNeural   — suara pria (default)
  id-ID-GadisNeural  — suara wanita
"""
import asyncio
import os
import edge_tts

AUDIO_DIR     = "data/audio"
DEFAULT_VOICE = "id-ID-ArdiNeural"


async def _synthesize_with_subtitle(
    text: str,
    audio_path: str,
    srt_path: str,
    voice: str,
    rate: str,
    volume: str,
):
    """Generate audio MP3 + file SRT secara bersamaan dari 1 stream."""
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    submaker    = edge_tts.SubMaker()

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    with open(srt_path, "w", encoding="utf-8") as srt_file:
        srt_file.write(submaker.get_srt())


def generate_tts(
    text: str,
    output_path: str | None = None,
    srt_path: str | None = None,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    volume: str = "+0%",
) -> tuple[str, str]:
    """
    Convert teks ke audio MP3 + file subtitle SRT.
    Return: (audio_path, srt_path)
    """
    os.makedirs(AUDIO_DIR, exist_ok=True)

    if output_path is None:
        import time
        ts = int(time.time())
        output_path = os.path.join(AUDIO_DIR, f"tts_{ts}.mp3")

    if srt_path is None:
        srt_path = output_path.replace(".mp3", ".srt")

    asyncio.run(_synthesize_with_subtitle(text, output_path, srt_path, voice, rate, volume))

    audio_kb = os.path.getsize(output_path) / 1024
    print(f"[TTS] Audio : {output_path} ({audio_kb:.1f} KB) | voice: {voice}")
    print(f"[TTS] SRT   : {srt_path}")
    return output_path, srt_path
