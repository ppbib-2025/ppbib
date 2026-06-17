"""
TTS Engine — convert script narasi ke audio MP3 via edge-tts (gratis).
Menggunakan Microsoft Edge Neural TTS, tidak butuh API key.

Voice Indonesia tersedia:
  id-ID-GadisNeural  — suara wanita (default)
  id-ID-ArdiNeural   — suara pria

Install: pip install edge-tts
Butuh ffmpeg untuk compose video + audio.
"""
import asyncio
import os
import edge_tts

AUDIO_DIR    = "data/audio"
DEFAULT_VOICE = "id-ID-GadisNeural"   # ganti ke "id-ID-ArdiNeural" untuk suara pria


async def _synthesize(text: str, output_path: str, voice: str, rate: str, volume: str):
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await communicate.save(output_path)


def generate_tts(
    text: str,
    output_path: str | None = None,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    volume: str = "+0%",
) -> str:
    """
    Convert teks Bahasa Indonesia ke audio MP3.
    rate:   kecepatan bicara, misal "+10%" lebih cepat, "-10%" lebih lambat
    volume: volume output, misal "+20%"
    Return: path file audio yang dihasilkan.
    """
    os.makedirs(AUDIO_DIR, exist_ok=True)
    if output_path is None:
        import time
        output_path = os.path.join(AUDIO_DIR, f"tts_{int(time.time())}.mp3")

    asyncio.run(_synthesize(text, output_path, voice, rate, volume))
    size_kb = os.path.getsize(output_path) / 1024
    print(f"[TTS] Audio selesai: {output_path} ({size_kb:.1f} KB) | voice: {voice}")
    return output_path
