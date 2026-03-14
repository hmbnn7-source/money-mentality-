import os
import random
import subprocess
import requests
from gtts import gTTS
import openai
from pexels_api import API  # ✅ التصحيح: استيراد API بدلاً من PexelsAPI

class VideoGenerator:
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.pexels_key = os.environ.get('PEXELS_API_KEY')
        openai.api_key = self.openai_key
        # ✅ إنشاء كائن API بالمفتاح
        self.pexels = API(self.pexels_key)
    
    def generate_script_and_title(self, topic):
        prompt = f"""
        You are a YouTube Shorts creator. Generate a video title and script about "{topic}" in American English.
        
        Requirements:
        - Title: catchy, under 60 characters.
        - Script: exactly 60 words, motivational tone with a gentle reality check.
        - Structure: Hook (1 sentence), 2 insights (2 sentences), Call to action (1 sentence).
        
        Format your response exactly like this:
        TITLE: [your title here]
        SCRIPT: [your script here]
        """
        try:
            response = openai.ChatCompletion.create(
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
        # ✅ استخدام الدالة الصحيحة من المكتبة
        self.pexels.search_videos(query, page=1, results_per_page=20)
        videos_data = self.pexels.get_entries()  # هذه ترجع قائمة بكائنات الفيديو
        
        if videos_data and len(videos_data) > 0:
            video = random.choice(videos_data)
            # البحث عن ملف بجودة HD
            for file in video.video_files:
                if file.quality == "hd" and file.width >= 720:
                    return file.link
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
