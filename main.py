import sys
import os
import asyncio
import random
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

# ==========================================
# 1. PARSE TOPIC & GENERATE VOICE TEXT
# ==========================================
TOPIC = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() != "" else "How does the brain work"
print(f"[BOT] Target Topic Received: '{TOPIC}'")

# Simplified dynamic educational scripts based on keyword matching
if "brain" in TOPIC.lower():
    SCRIPT_TEXT = "The human brain contains eighty-six billion neurons. They communicate through electrical impulses traveling up to two hundred and sixty miles per hour. Every single memory, thought, and feeling is just a complex symphony of these microscopic signals flashing across your mind."
    SEARCH_KEYWORD = "brain neurology"
elif "crypto" in TOPIC.lower() or "bitcoin" in TOPIC.lower() or "trade" in TOPIC.lower():
    SCRIPT_TEXT = "Markets move on two emotions: fear and greed. True consistency separates the top one percent from the amateur. If you stick strictly to your execution rules and master your internal psychology, numbers don't lie."
    SEARCH_KEYWORD = "finance trading"
else:
    SCRIPT_TEXT = f"Let's dive into {TOPIC}. Understanding complex subjects requires breaking them down to their core structural principles. Focus, track the underlying data points, and consistency will build the ultimate blueprint for success."
    SEARCH_KEYWORD = "abstract technology"

# ==========================================
# 2. GENERATE AI VOICE (EDGE-TTS)
# ==========================================
VOICE_FILE = "voice.mp3"
async def generate_voice():
    import edge_tts
    # Using a crisp, premium male professional voice
    communicate = edge_tts.Communicate(SCRIPT_TEXT, "en-US-ChristopherNeural")
    await communicate.save(VOICE_FILE)

print("[TTS ENGINE] Commencing speech synthesis...")
asyncio.run(generate_voice())

# ==========================================
# 3. FETCH ORIGINAL BACKGROUND FROM PEXELS
# ==========================================
PEXELS_KEY = os.getenv("PEXELS_API_KEY")
VIDEO_FILE = "background.mp4"

if not PEXELS_KEY:
    print("[ERROR] PEXELS_API_KEY is missing from GitHub Secrets! Cannot fetch video clips.")
    sys.exit(1)

headers = {"Authorization": PEXELS_KEY}
url = f"https://api.pexels.com/videos/search?query={SEARCH_KEYWORD}&per_page=5&orientation=portrait"

print(f"[PEXELS API] Querying stock assets for '{SEARCH_KEYWORD}'...")
try:
    response = requests.get(url, headers=headers, timeout=15).json()
    # Pull a random clip from the top portrait results to keep every single run unique
    video_data = random.choice(response['videos'])
    # Find a clean HD or mobile-friendly file link
    video_files = video_data['video_files']
    download_url = next(f['link'] for f in video_files if f['width'] <= 1080)
    
    print("[DOWNLOADER] Extracting raw binary video track...")
    video_bytes = requests.get(download_url, timeout=20).content
    with open(VIDEO_FILE, "wb") as f:
        f.write(video_bytes)
except Exception as e:
    print(f"[FATAL SETUP ERROR] Failed to fetch or download stock footage: {e}")
    sys.exit(1)

# ==========================================
# 4. ADVANCED VIDEO PROCESSING ENGINE
# ==========================================
print("[COMPOSITOR] Staging audio and visual elements...")
audio_track = AudioFileClip(VOICE_FILE)
duration = audio_track.duration

# Load background, strip original audio, loop or trim to match voice file exactly
bg_clip = VideoFileClip(VIDEO_FILE).without_audio()
if bg_clip.duration < duration:
    bg_clip = bg_clip.loop(duration=duration)
else:
    bg_clip = bg_clip.subclip(0, duration)

# Force background to conform perfectly to 1080x1920 TikTok standards
bg_clip = bg_clip.resize(newsize=(1080, 1920))

# Text layout helper using standard system font mechanics to prevent format crashes
def wrap_text(text, font, max_width):
    words = text.upper().split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.getlength(test_line) <= max_width:
            current_line.append(word)
        else:
            if current_line: lines.append(' '.join(current_line))
            current_line = [word]
    if current_line: lines.append(' '.join(current_line))
    return lines

print("[COMPOSITOR] Generating high-contrast dynamic text layer...")
def make_caption_frame(t):
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default() # Fallback safe system font engine
    
    # Text mapping metrics
    lines = wrap_text(SCRIPT_TEXT, font, 900)
    line_h = 80
    start_y = (1920 - (len(lines) * line_h)) // 2
    
    for idx, line in enumerate(lines):
        line_w = font.getlength(line)
        start_x = (1080 - line_w) // 2
        curr_y = start_y + (idx * line_h)
        
        # Heavy shadow backing lines for high mobile readability
        for dx, dy in [(-2,-2), (2,-2), (-2,2), (2,2)]:
            draw.text((start_x + dx, curr_y + dy), line, font=font, fill=(0, 0, 0, 255))
        # Hard white primary face text
        draw.text((start_x, curr_y), line, font=font, fill=(255, 255, 255, 255))
        
    return np.array(img)

# Combine video background, synthesized voice track, and text subtitles
caption_clip = VideoClip(make_caption_frame, duration=duration).set_ismask(False)
final_video = CompositeVideoClip([bg_clip, caption_clip]).set_audio(audio_track)

print("[COMPOSITOR] Rendering finalized MP4 production master...")
final_video.write_videofile(
    "output.mp4",
    fps=24,
    codec="libx264",
    audio_codec="aac",
    threads=4,
    logger=None
)

print("[SUCCESS] Production sequence ended cleanly.")
