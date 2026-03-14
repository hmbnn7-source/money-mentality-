import os
import json
import base64
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

class YouTubeUploader:
    def __init__(self):
        # الحصول على الأسرار المشفرة من المتغيرات البيئية
        client_secrets_b64 = os.environ.get('CLIENT_SECRETS_JSON', '')
        token_b64 = os.environ.get('TOKEN_JSON', '')

        if not client_secrets_b64 or not token_b64:
            raise ValueError("Missing CLIENT_SECRETS_JSON or TOKEN_JSON environment variables")

        try:
            # فك تشفير base64 إلى نص JSON
            client_secrets_json_str = base64.b64decode(client_secrets_b64).decode('utf-8')
            token_json_str = base64.b64decode(token_b64).decode('utf-8')

            # تحويل النص إلى كائنات Python
            self.client_config = json.loads(client_secrets_json_str)
            self.token_data = json.loads(token_json_str)
        except Exception as e:
            print("Error decoding secrets. Please check that the secrets contain valid base64-encoded JSON.")
            print(f"Decoding error: {e}")
            raise

        # إنشاء كائن Credentials باستخدام refresh_token
        self.credentials = Credentials(
            token=self.token_data.get('token'),
            refresh_token=self.token_data.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_config['web']['client_id'],
            client_secret=self.client_config['web']['client_secret'],
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )

    def upload(self, video_path, title, description):
        if self.credentials.expired:
            self.credentials.refresh(Request())

        youtube = build('youtube', 'v3', credentials=self.credentials)
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': '22'  # 22 = People & Blogs
            },
            'status': {
                'privacyStatus': 'private'  # يمكن تغييره لاحقاً إلى public
            }
        }
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        response = request.execute()
        return response['id']
