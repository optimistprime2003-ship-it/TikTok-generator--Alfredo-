import sys
import os
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoClip

# ==========================================
# 1. INGEST INPUTS & FORCE ALL CAPS
# ==========================================
if len(sys.argv) > 1 and sys.argv[1].strip() != "":
    raw_text = sys.argv[1].strip()
else:
    raw_text = "Consistency separates the amateur from the professional. Trade your plan, master your mind."

VIDEO_TEXT = raw_text.upper()
print(f"[PROCESSING TEXT]: {VIDEO_TEXT}")

# ==========================================
# 2. DOWNLOAD PREMIUM BOLD FONT
# ==========================================
font_path = "Roboto-Bold.ttf"
font_url = "https://cdnjs.cloudflare.com/ajax/libs/ink/3.1.10/fonts/Roboto/Roboto-Bold.ttf"

if not os.path.exists(font_path):
    print("[ASSET] Downloading high-res typography font...")
    try:
        response = requests.get(font_url, timeout=15)
        with open(font_path, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"[WARNING] Font download failed, using default: {e}")

# ==========================================
# 3. VIDEO SPECIFICATIONS & TIMELINE
# ==========================================
WIDTH, HEIGHT = 1080, 1920
FPS = 24
DURATION = 8

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.getlength(test_line) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def make_frame(t):
    # Deep aesthetic dark background canvas
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(15, 15, 20))
    draw = ImageDraw.Draw(img)
    
    # Load the downloaded premium font at a massive scale
    if os.path.exists(font_path):
        font = ImageFont.truetype(font_path, 85)
    else:
        font = ImageFont.load_default()

    max_text_width = WIDTH - 160
    wrapped_lines = wrap_text(VIDEO_TEXT, font, max_text_width)
    
    line_height = 110
    total_text_height = len(wrapped_lines) * line_height
    start_y = (HEIGHT - total_text_height) // 2
    
    for i, line in enumerate(wrapped_lines):
        line_w = font.getlength(line)
        start_x = (WIDTH - line_w) // 2
        current_y = start_y + (i * line_height)
        
        # Heavy High-Contrast Drop Shadow Outlines
        for dx, dy in [(-4,-4), (4,-4), (-4,4), (4,4), (0,-4), (0,4), (-4,0), (4,0)]:
            draw.text((start_x + dx, current_y + dy), line, font=font, fill=(0, 0, 0))
            
        # Crisp White Main Text Layer
        draw.text((start_x, current_y), line, font=font, fill=(255, 255, 255))
        
    return np.array(img)

# ==========================================
# 4. EXPORT PIPELINE
# ==========================================
print("[COMPOSITOR] Stitching canvas timeline...")
video_clip = VideoClip(make_frame, duration=DURATION)

print("[COMPOSITOR] Compiling uncompressed frames into MP4 container...")
video_clip.write_videofile(
    "output.mp4", 
    fps=FPS, 
    codec="libx264", 
    audio=False
)
print("[SUCCESS] Production run completed clean.")
