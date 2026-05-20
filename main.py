import sys
import os
import asyncio
import random
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip

# ==========================================
# 1. PARSE TOPIC & GENERATE VOICE TEXT
# ==========================================
TOPIC = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() != "" else "How does the brain work"
print(f"[BOT] Target Topic Received: '{TOPIC}'")

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
    video_data = random.choice(response['videos'])
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
# 4. TYPOGRAPHY SETUP (MONTSERRAT BOLD)
# ==========================================
FONT_FILE = "Montserrat-Bold.ttf"
try:
    # Look for common linux system font path first, fallback to direct download if missing
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_path):
        font_path = FONT_FILE
        if not os.path.exists(font_path):
            print("[FONT SEEDER] Downloading crisp typography assets...")
            r = requests.get("https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Bold.ttf", timeout=10)
            with open(font_path, "wb") as f:
                f.write(r.content)
    video_font = ImageFont.truetype(font_path, 65)
    line_h = 90
    print(f"[FONT] System typography loaded cleanly from: {font_path}")
except Exception as e:
    print(f"[FONT WARNING] Typography engine fallback deployed: {e}")
    video_font = ImageFont.load_default()
    line_h = 25

# Helper logic to wrap lines safely across a mobile screen canvas
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

# ==========================================
# 5. STREAMLINED FRAME-STAMPING ENGINE
# ==========================================
print("[COMPOSITOR] Extracting video track arrays...")
audio_track = AudioFileClip(VOICE_FILE)
duration = audio_track.duration

bg_clip = VideoFileClip(VIDEO_FILE).without_audio()
if bg_clip.duration < duration:
    bg_clip = bg_clip.loop(duration=duration)
else:
    bg_clip = bg_clip.subclip(0, duration)

bg_clip = bg_clip.resize(newsize=(1080, 1920))

# This stamps captions directly into the frame pixels, bypassing alpha conflicts entirely!
def add_captions_to_frame(frame):
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    
    lines = wrap_text(SCRIPT_TEXT, video_font, 900)
    total_text_h = len(lines) * line_h
    start_y = (1920 - total_text_h) // 2
    
    for idx, line in enumerate(lines):
        line_w = video_font.getlength(line)
        start_x = (1080 - line_w) // 2
        curr_y = start_y + (idx * line_h)
        
        # Heavy black high-contrast outline backings
        for dx, dy in [(-3,-3), (3,-3), (-3,3), (3,3), (-1,-1), (1,-1), (-1,1), (1,1)]:
            draw.text((start_x + dx, curr_y + dy), line, font=video_font, fill=(0, 0, 0))
            
        # Crisp white face text fronting
        draw.text((start_x, curr_y), line, font=video_font, fill=(255, 255, 255))
        
    return np.array(img)

print("[COMPOSITOR] Commencing inline pixel typography transformations...")
final_video = bg_clip.fl_image(add_captions_to_frame).set_audio(audio_track)

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
