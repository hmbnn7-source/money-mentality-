#!/usr/bin/env python3
import os
import sys
import random
import datetime
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.generator import VideoGenerator
from src.uploader import YouTubeUploader

# مواضيع مالية متنوعة
TOPICS = [
    "Why most people stay broke",
    "The 1% rule",
    "Money mindset shift",
    "Stop being poor",
    "Wealthy habits",
    "Financial freedom secrets",
    "Why you're not rich yet",
    "The psychology of money",
    "Rich dad poor dad",
    "Money mistakes to avoid",
    "How to think like a millionaire",
    "Passive income truth",
    "Why saving money isn't enough",
    "Financial education first",
    "Dark side of money"
]

def main():
    selected_topics = random.sample(TOPICS, 5)
    generator = VideoGenerator()
    uploader = YouTubeUploader()
    
    for i, topic in enumerate(selected_topics):
        print(f"\n🎬 [{i+1}/5] {topic}")
        try:
            # توليد العنوان والنص
            title, script = generator.generate_script_and_title(topic)
            print(f"📝 Title: {title}")
            
            # البحث عن فيديو
            video_url = generator.search_pexels_video("dark night sky")
            if not video_url:
                video_url = generator.search_pexels_video("night")
            
            # إنشاء الفيديو
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = f"/tmp/video_{timestamp}_{i}.mp4"
            generator.create_video(script, video_url, video_path)
            
            # رفع
            description = f"{script}\n\nSubscribe for daily mindset shifts! 💰"
            video_id = uploader.upload(video_path, title, description)
            print(f"📤 Uploaded: https://youtu.be/{video_id}")
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    print("\n🎉 All done!")

if __name__ == "__main__":
    main()