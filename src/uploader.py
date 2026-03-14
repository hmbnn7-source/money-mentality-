import os
import json
import base64
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

class YouTubeUploader:
    def __init__(self):
        # فك تشفير الـ secrets القادمة من GitHub
        client_secrets_json = base64.b64decode(
            os.environ.get('CLIENT_SECRETS_JSON', '')
        ).decode('utf-8')
        token_json = base64.b64decode(
            os.environ.get('TOKEN_JSON', '')
        ).decode('utf-8')
        
        self.client_config = json.loads(client_secrets_json)
        self.token_data = json.loads(token_json)
        
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
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'private'
            }
        }
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
        response = request.execute()
        return response['id']