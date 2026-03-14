import os
import random
import subprocess
import requests
from gtts import gTTS
import openai

class VideoGenerator:
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.pexels_key = os.environ.get('PEXELS_API_KEY')
        self.client = openai.OpenAI(api_key=self.openai_key)
    
    def generate_script_and_title(self, topic):
        prompt = f"""
        You are a YouTube Shorts creator. Generate a video title and script about "{topic}" in American English.
        
        Requirements:
        - Title: catchy, under 60 characters.
        - Script: exactly 60 words, motivational tone with a gentle reality check.
        - Structure: Hook (1 sentence),  ️ quick insights (2 sentences), Call to action (1 sentence).
        
        Format your response exactly like this:
        TITLE: [your title here]
        SCRIPT: [your script here]
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.8
            )
            content = response.choices[0].message.content.strip()
            lines = content.split('\n')
            title = lines[0].replace('TITLE:', '').strip()
            script = '\n'.join(lines[1:]).replace('SCRIPT:', '').strip()
            return title, script
        except Exception as e:
            print(f"OpenAI error: {e}")
            return f"Mindset Shift: {topic}", f"Did you know that {topic} can change your life? Subscribe for more."
    
    def search_pexels_video(self, query="dark night sky"):
        """البحث عن فيديو في Pexels باستخدام API مباشر"""
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": self.pexels_key}
        params = {
            "query": query,
            "per_page": 20,
            "orientation": "portrait",
            "size": "medium"
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            videos = data.get("videos", [])
            if videos:
                # اختر فيديو عشوائي
                video = random.choice(videos)
                # ابحث عن ملف بجودة HD
                for file in video.get("video_files", []):
                    if file.get("quality") == "hd" and file.get("width", 0) >= 720:
                        return file.get("link")
        except Exception as e:
            print(f"Pexels API error: {e}")
        return None
    
    def create_video(self, script, video_url, output_path):
        # 1. توليد الصوت
        audio_file = "/tmp/audio.mp3"
        tts = gTTS(text=script, lang='en', slow=False)
        tts.save(audio_file)
        
        # 2. تحميل الفيديو
        video_file = "/tmp/video.mp4"
        r = requests.get(video_url, stream=True)
        with open(video_file, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        
        # 3. الحصول على مدة الصوت
        audio_duration_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{audio_file}"'
        audio_duration = float(subprocess.check_output(audio_duration_cmd, shell=True).decode().strip())
        
        # 4. قص الفيديو ليناسب مدة الصوت
        temp_video = "/tmp/video_trimmed.mp4"
        trim_cmd = f'ffmpeg -i "{video_file}" -t {audio_duration} -c copy "{temp_video}" -y'
        subprocess.run(trim_cmd, shell=True, check=True)
        
        # 5. تغيير الحجم إلى 1080x1920 (عمودي)
        final_video = "/tmp/video_resized.mp4"
        resize_cmd = f'ffmpeg -i "{temp_video}" -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" -c:a copy "{final_video}" -y'
        subprocess.run(resize_cmd, shell=True, check=True)
        
        # 6. دمج الصوت مع الفيديو
        merge_cmd = f'ffmpeg -i "{final_video}" -i "{audio_file}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{output_path}" -y'
        subprocess.run(merge_cmd, shell=True, check=True)
        
        # 7. تنظيف الملفات المؤقتة
        os.remove(audio_file)
        os.remove(video_file)
        os.remove(temp_video)
        os.remove(final_video)
        
        return output_path
