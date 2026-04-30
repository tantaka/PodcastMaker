import json
import os
from datetime import datetime
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import yaml


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class DriveUploader:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.folder_name = config["drive"]["folder_name"]

        service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )
        self.service = build("drive", "v3", credentials=creds)
        self._root_folder_id = None

    def _get_or_create_folder(self, name: str, parent_id: str = None) -> str:
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = self.service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]

        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        folder = self.service.files().create(body=metadata, fields="id").execute()
        return folder["id"]

    def _get_root_folder(self) -> str:
        if self._root_folder_id is None:
            self._root_folder_id = self._get_or_create_folder(self.folder_name)
        return self._root_folder_id

    def upload(self, file_path: Path, topic: dict) -> str:
        root_id = self._get_root_folder()
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_folder_id = self._get_or_create_folder(date_str, root_id)

        filename = f"{topic['id']}_{date_str}.wav"
        media = MediaFileUpload(str(file_path), mimetype="audio/wav", resumable=True)
        file_metadata = {
            "name": filename,
            "parents": [date_folder_id],
        }
        uploaded = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
        ).execute()

        print(f"  アップロード完了: {filename}")
        return uploaded.get("webViewLink", "")
