
import os
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


def get_drive_service():
    private_key = os.environ["GOOGLE_PRIVATE_KEY"].replace(
        "\\n", "\n"
    )

    credentials_info = {
        "type": "service_account",
        "project_id": os.environ["GOOGLE_PROJECT_ID"],
        "private_key_id": os.environ["GOOGLE_PRIVATE_KEY_ID"],
        "private_key": private_key,
        "client_email": os.environ["GOOGLE_CLIENT_EMAIL"],
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    credentials = (
        service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/drive"],
        )
    )

    return build("drive", "v3", credentials=credentials)


def upload_image(image):
    service = get_drive_service()
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

    content = image.read()

    media = MediaIoBaseUpload(
        io.BytesIO(content),
        mimetype=image.mimetype or "application/octet-stream",
        resumable=False,
    )

    uploaded = service.files().create(
        body={
            "name": image.filename or "upload.jpg",
            "parents": [folder_id],
        },
        media_body=media,
        fields="id,name",
    ).execute()

    file_id = uploaded["id"]

    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    return {
        "file_id": file_id,
        "image_url": f"https://drive.google.com/uc?export=view&id={file_id}",
    }