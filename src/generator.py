import os
import random
import requests
from gtts import gTTS
from moviepy.editor import *
import openai
from pexels_api import PexelsAPI

class VideoGenerator:
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.pexels_key = os.environ.get('PEXELS_API_KEY')
        openai.api_key = self.openai_key
        self.pexels = PexelsAPI(self.pexels_key)
    
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
        videos = self.pexels.search_videos({
            "query": query,
            "per_page": 20,
            "orientation": "portrait",
            "size": "medium"
        })
        if videos and len(videos) > 0:
            video = random.choice(videos)
            for file in video.video_files:
                if file.quality == "hd" and file.width >= 720:
                    return file.link
        return None
    
    def create_video(self, script, video_url, output_path):
        # صوت
        audio = gTTS(text=script, lang='en', slow=False)
        audio_file = "/tmp/audio.mp3"
        audio.save(audio_file)
        
        # فيديو
        video_file = "/tmp/video.mp4"
        r = requests.get(video_url, stream=True)
        with open(video_file, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        
        # دمج
        audio_clip = AudioFileClip(audio_file)
        video_clip = VideoFileClip(video_file).without_audio()
        
        if video_clip.duration < audio_clip.duration:
            video_clip = video_clip.loop(duration=audio_clip.duration)
        else:
            video_clip = video_clip.subclip(0, audio_clip.duration)
        
        video_clip = video_clip.resize(height=1920).crop(x_center=video_clip.w/2, width=1080, height=1920)
        
        final = video_clip.set_audio(audio_clip)
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        os.remove(audio_file)
        os.remove(video_file)
        return output_path
