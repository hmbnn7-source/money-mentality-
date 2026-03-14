import os
import random
import subprocess
import requests
import openai
import whisper
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings

class VideoGenerator:
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.pexels_key = os.environ.get('PEXELS_API_KEY')
        self.elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
        self.voice_id = os.environ.get('VOICE_ID', '21m00Tcm4TlvDq8ikWAM')
        
        openai.api_key = self.openai_key
        self.client = openai.OpenAI(api_key=self.openai_key)
        self.whisper_model = whisper.load_model("base")
        self.eleven_client = ElevenLabs(api_key=self.elevenlabs_key)
    
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
            title = script.split('.')[0][:60] + " | Money Mentality"
            return title, script
        except Exception as e:
            print(f"OpenAI error: {e}")
            return f"Mindset Shift: {topic}", f"Did you know that {topic} can change your life? Subscribe for more."
    
    def text_to_speech_elevenlabs(self, text, output_path):
        try:
            response = self.eleven_client.text_to_speech.convert(
                voice_id=self.voice_id,
                output_format="mp3_44100_128",
                text=text,
                model_id="eleven_monolingual_v1",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.5
                )
            )
            with open(output_path, 'wb') as f:
                for chunk in response:
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"ElevenLabs error: {e}")
            return False
    
    def search_pexels_video(self, query=None):
        search_queries = [
            "city skyline night aerial",
            "downtown city lights night",
            "urban cityscape night",
            "skyscrapers night view",
            "city夜景"
        ]
        if not query:
            query = random.choice(search_queries)
        
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": self.pexels_key}
        params = {
            "query": query,
            "per_page": 30,
            "orientation": "portrait",
            "size": "medium"
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            videos = data.get("videos", [])
            
            if videos:
                filtered_videos = []
                for video in videos:
                    url_lower = video.get("url", "").lower()
                    exclude_keywords = ["fireworks", "celebration", "festival", "explosion", "pyrotechnics"]
                    if not any(keyword in url_lower for keyword in exclude_keywords):
                        filtered_videos.append(video)
                
                if not filtered_videos:
                    filtered_videos = videos
                
                video = random.choice(filtered_videos)
                for file in video.get("video_files", []):
                    if file.get("quality") == "hd" and file.get("width", 0) >= 720:
                        print(f"Selected video: {video.get('url', '')}")
                        return file.get("link")
        except Exception as e:
            print(f"Pexels API error: {e}")
        return None
    
    def create_ass_subtitle_file(self, segments, output_ass):
        with open(output_ass, 'w', encoding='utf-8') as f:
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1080\n")
            f.write("PlayResY: 1920\n")
            f.write("ScaledBorderAndShadow: yes\n\n")
            
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write("Style: Default,Arial,70,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,5,20,20,20,1\n\n")
            
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            for i, seg in enumerate(segments):
                start = seg['start']
                end = seg['end']
                text = seg['text'].strip()
                f.write(f"Dialogue: 0,{self.format_time_ass(start)},{self.format_time_ass(end)},Default,,0,0,0,,{text}\n")
    
    def format_time_ass(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds - int(seconds)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    
    def format_time(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    def create_video(self, script, video_url, output_path):
        audio_file = "/tmp/audio.mp3"
        if not self.text_to_speech_elevenlabs(script, audio_file):
            print("ElevenLabs failed, using gTTS fallback")
            from gtts import gTTS
            tts = gTTS(text=script, lang='en', slow=False)
            tts.save(audio_file)
        
        video_file = "/tmp/video.mp4"
        r = requests.get(video_url, stream=True)
        with open(video_file, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        
        audio_duration_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{audio_file}"'
        audio_duration = float(subprocess.check_output(audio_duration_cmd, shell=True).decode().strip())
        
        temp_video = "/tmp/video_trimmed.mp4"
        trim_cmd = f'ffmpeg -i "{video_file}" -t {audio_duration} -c copy "{temp_video}" -y'
        subprocess.run(trim_cmd, shell=True, check=True)
        
        resized_video = "/tmp/video_resized.mp4"
        resize_cmd = f'ffmpeg -i "{temp_video}" -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" -c:a copy "{resized_video}" -y'
        subprocess.run(resize_cmd, shell=True, check=True)
        
        print("Transcribing audio with Whisper...")
        result = self.whisper_model.transcribe(audio_file)
        segments = result['segments']
        
        ass_file = "/tmp/subtitles.ass"
        self.create_ass_subtitle_file(segments, ass_file)
        
        video_with_subs = "/tmp/video_with_subs.mp4"
        subs_cmd = f'ffmpeg -i "{resized_video}" -vf "ass={ass_file}" -c:a copy "{video_with_subs}" -y'
        subprocess.run(subs_cmd, shell=True, check=True)
        
        final_video = "/tmp/video_final.mp4"
        merge_cmd = f'ffmpeg -i "{video_with_subs}" -i "{audio_file}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{final_video}" -y'
        subprocess.run(merge_cmd, shell=True, check=True)
        
        subprocess.run(f'cp "{final_video}" "{output_path}"', shell=True, check=True)
        
        for f in [audio_file, video_file, temp_video, resized_video, video_with_subs, final_video, ass_file]:
            if os.path.exists(f):
                os.remove(f)
        
        return output_path
