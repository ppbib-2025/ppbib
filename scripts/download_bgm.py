"""
Download royalty-free background music ke assets/music/.
Jalankan sekali di lokal: python scripts/download_bgm.py

Sumber: Pixabay (CC0, bebas royalti, tidak perlu atribusi)
Semua track cocok untuk konten TikTok / Reels / FB.
"""
import os
import time
import requests

MUSIC_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

# Track Pixabay — upbeat acoustic / folk / nature
# Cocok untuk konten peternakan & edukasi
TRACKS = [
    {
        "filename": "upbeat_acoustic_folk.mp3",
        "url": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
        "desc": "Upbeat Acoustic Folk — ceria, cocok untuk tips peternak",
    },
    {
        "filename": "positive_morning.mp3",
        "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8cb6d1f9a9.mp3",
        "desc": "Positive Morning — ringan, motivasi",
    },
    {
        "filename": "happy_farm.mp3",
        "url": "https://cdn.pixabay.com/download/audio/2021/11/25/audio_91b32b13ab.mp3",
        "desc": "Happy Farm — ceria pedesaan",
    },
    {
        "filename": "nature_acoustic.mp3",
        "url": "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946b1b80ef.mp3",
        "desc": "Nature Acoustic — alam, tenang",
    },
    {
        "filename": "inspirational_acoustic.mp3",
        "url": "https://cdn.pixabay.com/download/audio/2022/11/22/audio_febc508520.mp3",
        "desc": "Inspirational Acoustic — motivasi peternak",
    },
]

def download(track: dict) -> bool:
    path = os.path.join(MUSIC_DIR, track["filename"])
    if os.path.exists(path):
        print(f"  ✓ Skip (sudah ada): {track['filename']}")
        return True
    try:
        print(f"  ↓ Download: {track['filename']} — {track['desc']}")
        r = requests.get(track["url"], timeout=30, stream=True,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        kb = os.path.getsize(path) / 1024
        print(f"    ✅ {kb:.0f} KB → {path}")
        return True
    except Exception as e:
        print(f"    ❌ Gagal: {e}")
        if os.path.exists(path):
            os.remove(path)
        return False


if __name__ == "__main__":
    print(f"Download BGM ke: {os.path.abspath(MUSIC_DIR)}\n")
    ok = 0
    for t in TRACKS:
        if download(t):
            ok += 1
        time.sleep(0.5)
    print(f"\nSelesai: {ok}/{len(TRACKS)} track berhasil.")
    print("Commit ke repo: git add assets/music/ && git commit -m 'add: BGM royalty-free'")
