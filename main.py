import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoClip

# ==========================================
# 1. SETUP TEXT
# ==========================================
raw_text = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].strip() != "" else "CONSISTENCY IS KEY."
VIDEO_TEXT = raw_text.upper()

# ==========================================
# 2. VIDEO SPECS
# ==========================================
WIDTH, HEIGHT = 1080, 1920
FPS = 24
DURATION = 5

def make_frame(t):
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(15, 15, 20))
    draw = ImageDraw.Draw(img)
    
    # Use load_default() which is always available and crash-proof
    font = ImageFont.load_default()
    
    # Draw simple, high-contrast text
    draw.text((100, 900), VIDEO_TEXT, fill=(255, 255, 255))
    return np.array(img)

# ==========================================
# 3. RENDER
# ==========================================
clip = VideoClip(make_frame, duration=DURATION)
clip.write_videofile("output.mp4", fps=FPS, codec="libx264", audio=False)
