from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import json

# 1. النطاق (Scope) اللي محتاجه لرفع فيديوهات يوتيوب
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    creds = None
    # الملف اللي هيحفظ الـ token (هيتولد بعد تنفيذ الكود)
    token_file = 'token.json'

    # 2. شغّل التطبيق باستخدام client_secrets.json
    flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # 3. احفظ الـ token في ملف
    with open(token_file, 'w') as token:
        token.write(creds.to_json())
    print(f"✅ تم إنشاء ملف {token_file} بنجاح!")

if __name__ == '__main__':
    main()