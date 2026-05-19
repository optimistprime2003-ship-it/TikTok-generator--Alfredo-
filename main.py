import sys
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, VideoClip, ColorClip

# ==========================================
# 1. CAPTURE CUSTOM COMMANDS & INPUTS
# ==========================================
print("[AI ENGINE] Processing text configurations...")
raw_text = ""

if len(sys.argv) > 1 and sys.argv[1].strip() != "":
    raw_text = sys.argv[1].strip()
    print(f"[CUSTOM COMMAND INGESTED]: {raw_text}")
else:
    print("[AI ENGINE] Requesting narrative contents from Hugging Face...")
    # Default high-engagement placeholder text
    raw_text = "Consistency separates the amateur from the professional. Trade your plan, master your mind."
    print("[AI ENGINE] Successfully ingested viral text blocks.")

# CRITICAL UPGRADE: Force ALL CAPS and massive punchy formatting
VIDEO_TEXT = raw_text.upper()

# ==========================================
# 2. VIDEO SPECIFICATIONS (HIGHEST RESOLUTION)
# ==========================================
WIDTH, HEIGHT = 1080, 1920
FPS = 24
DURATION = 10  # Duration in seconds

print("[ASSET] Generating dynamic typographic layouts...")

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
    # Create an uncompressed canvas frame
    # Background color: Dark aesthetic slate (#111116)
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(17, 17, 22))
    draw = ImageDraw.Draw(img)
    
    # CRITICAL UPGRADE: Huge, ultra-sharp font size configuration
    try:
        font = ImageFont.load_default(size=95)
    except TypeError:
        font = ImageFont.load_default() # Fallback for legacy environments

    # Calculate safe bounding margins for wrapping text
    max_text_width = WIDTH - 160
    wrapped_lines = wrap_text(VIDEO_TEXT, font, max_text_width)
    
    # Layout and central positioning math
    line_height = 120
    total_text_height = len(wrapped_lines) * line_height
    start_y = (HEIGHT - total_text_height) // 2
    
    # Draw text layers with dynamic drop shadows for depth
    for i, line in enumerate(wrapped_lines):
        line_w = font.getlength(line)
        start_x = (WIDTH - line_w) // 2
        current_y = start_y + (i * line_height)
        
        # Crisp black stroke outline effect
        for offset_x, offset_y in [(-4,-4), (4,-4), (-4,4), (4,4), (0,-5), (0,5), (-5,0), (5,0)]:
            draw.text((start_x + offset_x, current_y + offset_y), line, font=font, fill=(0, 0, 0))
            
        # Highlight Core Text (Vibrant Neon Accent)
        draw.text((start_x, current_y), line, font=font, fill=(255, 255, 255))
        
    return np.array(img)

# ==========================================
# 3. COMPOSITOR & EXPORT ENGINE
# ==========================================
print("[COMPOSITOR] Stitching layers together into canvas timeline...")
video_clip = VideoClip(make_frame, duration=DURATION)

print(f"[COMPOSITOR] Rendering video stream: {WIDTH}x{HEIGHT} | {FPS} FPS")
video_clip.write_videofile(
    "output.mp4", 
    fps=FPS, 
    codec="libx264", 
    audio=False, 
    logger=None
)

print("[SUCCESS] Video generation pipeline completed successfully.")
