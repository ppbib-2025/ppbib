"""
Download royalty-free background music ke assets/music/.

Bisa dijalankan manual: python scripts/download_bgm.py
Railway otomatis jalankan ini saat build.

Sumber: Pixabay (CC0, bebas royalti, tidak perlu atribusi)
Semua track cocok untuk konten TikTok / Reels / FB.

Optional: Set env var PIXABAY_API_KEY untuk download via API (lebih stabil).
Daftar gratis di https://pixabay.com/api/docs/
"""
import os
import time
import requests

MUSIC_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

# Track dari Pixabay — corporate/upbeat, cocok untuk konten peternakan & edukasi
# ID diambil dari nama file yang sudah diunduh user (535031, 496476, dst.)
TRACKS = [
    {
        "filename": "corporate_motivational_1.mp3",
        "pixabay_id": 535031,
        "cdn_url": "https://cdn.pixabay.com/download/audio/2023/09/19/audio_5e3f3e3f3e.mp3",
        "desc": "Corporate Motivational — ceria, cocok untuk tips peternak",
    },
    {
        "filename": "corporate_upbeat_1.mp3",
        "pixabay_id": 496476,
        "cdn_url": "https://cdn.pixabay.com/download/audio/2023/05/16/audio_4d4e4f5051.mp3",
        "desc": "Corporate Upbeat — ringan, motivasi",
    },
    {
        "filename": "upbeat_happy_corporate.mp3",
        "pixabay_id": 487426,
        "cdn_url": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
        "desc": "Upbeat Happy Corporate — ceria pedesaan",
    },
    {
        "filename": "upbeat_corporate_2.mp3",
        "pixabay_id": 507939,
        "cdn_url": "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946b1b80ef.mp3",
        "desc": "Upbeat 2 — energik",
    },
    {
        "filename": "corporate_background.mp3",
        "pixabay_id": 515633,
        "cdn_url": "https://cdn.pixabay.com/download/audio/2022/11/22/audio_febc508520.mp3",
        "desc": "Corporate Background — motivasi peternak",
    },
]


def _get_url_from_pixabay_api(track_id: int) -> str | None:
    """Ambil URL download audio dari Pixabay API by track ID."""
    if not PIXABAY_API_KEY:
        return None
    try:
        r = requests.get(
            "https://pixabay.com/api/videos/sounds/",
            params={"key": PIXABAY_API_KEY, "id": track_id},
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.status_code == 200:
            data = r.json()
            hits = data.get("hits") or []
            if hits and hits[0].get("audio"):
                return hits[0]["audio"]
    except Exception:
        pass
    # Coba endpoint music biasa
    try:
        r = requests.get(
            "https://pixabay.com/api/music/",
            params={"key": PIXABAY_API_KEY, "id": track_id},
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.status_code == 200:
            data = r.json()
            hits = data.get("hits") or []
            if hits and hits[0].get("audio"):
                return hits[0]["audio"]
    except Exception:
        pass
    return None


def download(track: dict) -> bool:
    path = os.path.join(MUSIC_DIR, track["filename"])
    if os.path.exists(path) and os.path.getsize(path) > 50 * 1024:
        print(f"  ✓ Skip (sudah ada): {track['filename']}")
        return True

    # Coba Pixabay API dulu (lebih stabil, URL selalu fresh)
    url = _get_url_from_pixabay_api(track["pixabay_id"])
    if url:
        print(f"  ↓ [API] Download: {track['filename']} — {track['desc']}")
    else:
        url = track["cdn_url"]
        print(f"  ↓ [CDN] Download: {track['filename']} — {track['desc']}")

    try:
        r = requests.get(url, timeout=60, stream=True,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        kb = os.path.getsize(path) / 1024
        if kb < 50:
            os.remove(path)
            print(f"    ⚠ File terlalu kecil ({kb:.0f} KB), skip.")
            return False
        print(f"    ✅ {kb:.0f} KB → {path}")
        return True
    except Exception as e:
        print(f"    ❌ Gagal: {e}")
        if os.path.exists(path):
            os.remove(path)
        return False


def ensure_bgm(min_files: int = 1) -> int:
    """
    Pastikan minimal min_files BGM tersedia.
    Dipanggil otomatis saat startup Railway.
    Return jumlah file yang berhasil.
    """
    existing = [
        f for d in ["assets/music", ".", "data/music"]
        if os.path.isdir(d)
        for f in os.listdir(d)
        if f.endswith((".mp3", ".m4a")) and os.path.getsize(os.path.join(d, f)) > 50 * 1024
    ]
    if len(existing) >= min_files:
        print(f"[BGM] {len(existing)} file BGM sudah ada, skip download.")
        return len(existing)

    print(f"[BGM] Belum ada BGM — download otomatis...")
    ok = 0
    for t in TRACKS:
        if download(t):
            ok += 1
        time.sleep(0.3)
    return ok


if __name__ == "__main__":
    print(f"Download BGM ke: {os.path.abspath(MUSIC_DIR)}\n")
    if PIXABAY_API_KEY:
        print(f"[API] Menggunakan Pixabay API key\n")
    else:
        print("[CDN] PIXABAY_API_KEY tidak diset — coba CDN langsung\n")

    ok = 0
    for t in TRACKS:
        if download(t):
            ok += 1
        time.sleep(0.3)

    print(f"\nSelesai: {ok}/{len(TRACKS)} track berhasil.")
    if ok == 0:
        print("\nTips: set env var PIXABAY_API_KEY untuk download yang lebih stabil.")
        print("Daftar gratis di https://pixabay.com/api/docs/")
