"""
Google Drive Client — upload & download file untuk PPBIB bot.

Autentikasi via Service Account (cocok untuk bot otomatis tanpa login manual).

Env vars:
  GDRIVE_SERVICE_ACCOUNT_JSON  — isi file JSON service account (minified, 1 baris)
  GDRIVE_CLIPS_FOLDER_ID       — ID folder Drive tempat clip sumber disimpan
  GDRIVE_OUTPUT_FOLDER_ID      — ID folder Drive tempat output video diupload
                                  (opsional, default sama dengan CLIPS_FOLDER_ID)

Cara setup (sekali saja):
  1. Buka https://console.cloud.google.com → buat project baru
  2. Enable "Google Drive API"
  3. IAM → Service Accounts → buat service account → download JSON key
  4. Buka Google Drive → klik kanan folder clips → Share → masukkan email service account
  5. Salin isi file JSON (jadi 1 baris): cat key.json | python -c "import sys,json; print(json.dumps(json.load(sys.stdin)))"
  6. Set sebagai env var GDRIVE_SERVICE_ACCOUNT_JSON di Railway
"""
import io
import json
import os

CLIPS_FOLDER_ID  = os.getenv("GDRIVE_CLIPS_FOLDER_ID", "")
OUTPUT_FOLDER_ID = os.getenv("GDRIVE_OUTPUT_FOLDER_ID", "") or CLIPS_FOLDER_ID
_SA_JSON         = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON", "")

_VIDEO_MIME = "video/mp4"
_CHUNK_SIZE = 5 * 1024 * 1024   # 5MB resumable upload chunks


def is_gdrive_configured() -> bool:
    return bool(_SA_JSON and (CLIPS_FOLDER_ID or OUTPUT_FOLDER_ID))


def _service():
    """Build Google Drive API service dengan service account credentials."""
    if not _SA_JSON:
        raise RuntimeError(
            "GDRIVE_SERVICE_ACCOUNT_JSON belum diset. "
            "Lihat docstring src/gdrive_client.py untuk cara setup."
        )
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_info(
        json.loads(_SA_JSON),
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


# ── Download clip sumber ──────────────────────────────────────────────────────

def list_clips_in_folder(folder_id: str | None = None) -> list[dict]:
    """
    Daftar semua file video (mp4/mov) di folder Drive.
    Return list of {id, name, size}.
    """
    fid = folder_id or CLIPS_FOLDER_ID
    if not fid:
        return []
    svc = _service()
    results = svc.files().list(
        q=f"'{fid}' in parents and trashed=false and "
          f"(mimeType='video/mp4' or mimeType='video/quicktime' or mimeType='video/x-msvideo')",
        fields="files(id,name,size)",
        pageSize=100,
    ).execute()
    return results.get("files", [])


def download_clip(file_id: str, dest_path: str) -> str:
    """Download 1 file video dari Drive ke dest_path."""
    from googleapiclient.http import MediaIoBaseDownload
    svc = _service()
    req = svc.files().get_media(fileId=file_id)
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, req, chunksize=_CHUNK_SIZE)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest_path


def sync_clips_from_drive(dest_dir: str = "assets/clips") -> int:
    """
    Download semua clip dari GDRIVE_CLIPS_FOLDER_ID ke dest_dir.
    Skip file yang sudah ada dengan ukuran sama.
    Return jumlah file yang didownload.
    """
    if not CLIPS_FOLDER_ID:
        print("[GDrive] GDRIVE_CLIPS_FOLDER_ID belum diset — skip sync clip.")
        return 0

    os.makedirs(dest_dir, exist_ok=True)
    clips = list_clips_in_folder(CLIPS_FOLDER_ID)
    if not clips:
        print(f"[GDrive] Tidak ada clip di folder {CLIPS_FOLDER_ID}.")
        return 0

    print(f"[GDrive] {len(clips)} clip ditemukan di Drive.")
    downloaded = 0
    for clip in clips:
        dest = os.path.join(dest_dir, clip["name"])
        remote_size = int(clip.get("size", 0))
        if os.path.exists(dest) and os.path.getsize(dest) == remote_size:
            print(f"  ✓ Skip (sudah ada): {clip['name']}")
            continue
        print(f"  ↓ Download: {clip['name']} ({remote_size / 1024 / 1024:.1f} MB)")
        try:
            download_clip(clip["id"], dest)
            downloaded += 1
            print(f"    ✅ {clip['name']}")
        except Exception as e:
            print(f"    ❌ Gagal: {e}")

    print(f"[GDrive] Sync selesai: {downloaded}/{len(clips)} didownload.")
    return downloaded


# ── Upload output video ───────────────────────────────────────────────────────

def upload_video(local_path: str, folder_id: str | None = None) -> str:
    """
    Upload file video MP4 ke Google Drive.
    Return URL yang bisa dibuka siapa saja (Anyone with link → Viewer).
    """
    from googleapiclient.http import MediaFileUpload
    fid = folder_id or OUTPUT_FOLDER_ID
    if not fid:
        raise RuntimeError("GDRIVE_OUTPUT_FOLDER_ID belum diset.")

    svc  = _service()
    name = os.path.basename(local_path)
    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"[GDrive] Upload: {name} ({size_mb:.1f} MB)...")

    meta  = {"name": name, "parents": [fid]}
    media = MediaFileUpload(local_path, mimetype=_VIDEO_MIME,
                            chunksize=_CHUNK_SIZE, resumable=True)
    file  = svc.files().create(body=meta, media_body=media,
                               fields="id").execute()
    file_id = file["id"]

    # Buka akses publik (anyone with link, view-only)
    svc.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    url = f"https://drive.google.com/file/d/{file_id}/view"
    print(f"[GDrive] ✅ Upload selesai: {url}")
    return url
