import os
import random
import subprocess
import requests
import openai
import whisper
from elevenlabs import generate, set_api_key

class VideoGenerator:
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.pexels_key = os.environ.get('PEXELS_API_KEY')
        self.elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
        self.voice_id = os.environ.get('VOICE_ID', '21m00Tcm4TlvDq8ikWAM')  # صوت افتراضي
        
        openai.api_key = self.openai_key
        set_api_key(self.elevenlabs_key)
        self.client = openai.OpenAI(api_key=self.openai_key)
        self.whisper_model = whisper.load_model("base")  # تحميل نموذج whisper
    
    def generate_script_and_title(self, topic):
        prompt = f"""
        You are writing a viral YouTube Shorts voiceover script.
        Topic: {topic}
        Rules:
        - Exactly 60 words
        - Short sentences for voice over
        - Strong hook in the first line
        - Create curiosity
        - Fast pacing
        - End with a twist
        - No formatting
        - No quotes
        - Only plain text
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.8
            )
            script = response.choices[0].message.content.strip()
            # توليد عنوان بسيط من أول كلمات النص
            title = script.split('.')[0][:60] + " | Money Mentality"
            return title, script
        except Exception as e:
            print(f"OpenAI error: {e}")
            return f"Mindset Shift: {topic}", f"Did you know that {topic} can change your life? Subscribe for more."
    
    def text_to_speech_elevenlabs(self, text, output_path):
        """تحويل النص إلى صوت باستخدام ElevenLabs"""
        try:
            audio = generate(
                text=text,
                voice=self.voice_id,
                model="eleven_monolingual_v1"
            )
            with open(output_path, 'wb') as f:
                f.write(audio)
            return True
        except Exception as e:
            print(f"ElevenLabs error: {e}")
            return False
    
    def search_pexels_video(self, query="city at night"):
        """البحث عن فيديو في Pexels"""
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
                video = random.choice(videos)
                for file in video.get("video_files", []):
                    if file.get("quality") == "hd" and file.get("width", 0) >= 720:
                        return file.get("link")
        except Exception as e:
            print(f"Pexels API error: {e}")
        return None
    
    def create_subtitle_file(self, segments, output_srt):
        """إنشاء ملف ترجمة SRT من مقاطع Whisper"""
        with open(output_srt, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments):
                start = seg['start']
                end = seg['end']
                text = seg['text'].strip()
                f.write(f"{i+1}\n")
                f.write(f"{self.format_time(start)} --> {self.format_time(end)}\n")
                f.write(f"{text}\n\n")
    
    def format_time(self, seconds):
        """تحويل الثواني إلى تنسيق SRT (hh:mm:ss,ms)"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    def create_video(self, script, video_url, output_path):
        # 1. توليد الصوت باستخدام ElevenLabs
        audio_file = "/tmp/audio.mp3"
        if not self.text_to_speech_elevenlabs(script, audio_file):
            print("ElevenLabs failed, using gTTS fallback")
            from gtts import gTTS
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
        resized_video = "/tmp/video_resized.mp4"
        resize_cmd = f'ffmpeg -i "{temp_video}" -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" -c:a copy "{resized_video}" -y'
        subprocess.run(resize_cmd, shell=True, check=True)
        
        # 6. استخراج الترجمة من الصوت باستخدام Whisper
        print("Transcribing audio with Whisper...")
        result = self.whisper_model.transcribe(audio_file)
        segments = result['segments']
        
        # 7. إنشاء ملف ترجمة SRT
        srt_file = "/tmp/subtitles.srt"
        self.create_subtitle_file(segments, srt_file)
        
        # 8. دمج الترجمة مع الفيديو (حرقها)
        video_with_subs = "/tmp/video_with_subs.mp4"
        subs_cmd = f'ffmpeg -i "{resized_video}" -vf "subtitles={srt_file}" -c:a copy "{video_with_subs}" -y'
        subprocess.run(subs_cmd, shell=True, check=True)
        
        # 9. دمج الصوت مع الفيديو (بعد إضافة الترجمة)
        final_video = "/tmp/video_final.mp4"
        merge_cmd = f'ffmpeg -i "{video_with_subs}" -i "{audio_file}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{final_video}" -y'
        subprocess.run(merge_cmd, shell=True, check=True)
        
        # 10. نسخ الناتج النهائي إلى المسار المطلوب
        subprocess.run(f'cp "{final_video}" "{output_path}"', shell=True, check=True)
        
        # 11. تنظيف الملفات المؤقتة
        for f in [audio_file, video_file, temp_video, resized_video, video_with_subs, final_video, srt_file]:
            if os.path.exists(f):
                os.remove(f)
        
        return output_path
