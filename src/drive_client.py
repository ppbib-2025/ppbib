"""Google Drive client for listing and downloading footage clips."""

import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DriveClient:
    def __init__(self, credentials_path: str, token_path: str, config: dict):
        self.config = config
        self.service = self._authenticate(credentials_path, token_path)

    def _authenticate(self, credentials_path: str, token_path: str):
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        return build("drive", "v3", credentials=creds)

    def _list_videos_in_folder(self, folder_id: str) -> list[dict]:
        query = f"'{folder_id}' in parents and mimeType='video/mp4' and trashed=false"
        result = self.service.files().list(
            q=query,
            fields="files(id, name, size, createdTime)",
            orderBy="name",
        ).execute()
        return result.get("files", [])

    def list_all_clips(self) -> dict[str, list[dict]]:
        """Return clips grouped by category as defined in scenes_config.json."""
        drive_cfg = self.config["drive"]
        exclude_prefixes = tuple(drive_cfg.get("exclude_prefixes", []))
        clips: dict[str, list[dict]] = {}

        for cat_key, cat_cfg in drive_cfg["categories"].items():
            folder_id = cat_cfg.get("folder_id")
            name_prefix = cat_cfg.get("name_prefix")

            if folder_id:
                clips[cat_key] = self._list_videos_in_folder(folder_id)
            elif name_prefix:
                # Filter from footage root folder by name prefix
                footage_id = drive_cfg["footage_folder_id"]
                all_footage = self._list_videos_in_folder(footage_id)
                clips[cat_key] = [
                    f for f in all_footage
                    if f["name"].lower().startswith(name_prefix.lower())
                ]

        # Add uncategorized original footage (not in subfolders, not reference downloads)
        footage_id = drive_cfg["footage_folder_id"]
        all_footage = self._list_videos_in_folder(footage_id)
        categorized_names = {
            f["name"]
            for cat_list in clips.values()
            for f in cat_list
        }
        clips["footage_misc"] = [
            f for f in all_footage
            if f["name"] not in categorized_names
            and not f["name"].startswith(exclude_prefixes)
        ]

        return clips

    def download_clip(self, file_id: str, destination: Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        request = self.service.files().get_media(fileId=file_id)
        with open(destination, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return destination
