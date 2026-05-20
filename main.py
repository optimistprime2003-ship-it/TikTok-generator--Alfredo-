import sys
import os
import asyncio
import random
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip

# ==========================================
# 1. PARSE TOPIC & GENERATE DYNAMIC SCRIPT
# ==========================================
TOPIC = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() != "" else "How does ovulation work"
print(f"[BOT] Target Prompt Received: '{TOPIC}'")

def get_ai_script_and_keywords(prompt_topic):
    # Specialized, high-quality educational fallback templates
    if "ovulat" in prompt_topic.lower() or "girl" in prompt_topic.lower() or "cycle" in prompt_topic.lower():
        fallback_script = "Ovulation is a central part of the female reproductive cycle. It occurs when a mature egg is released from the ovary, moving down the fallopian tube where it becomes available for fertilization. Driven by changing hormone levels, this process typically happens once a month."
        fallback_keyword = "medical biology"
    elif "brain" in prompt_topic.lower():
        fallback_script = "The human brain contains eighty-six billion neurons. They communicate through electrical impulses traveling up to two hundred and sixty miles per hour. Every single memory, thought, and feeling is just a complex symphony of these microscopic signals flashing across your mind."
        fallback_keyword = "brain neurology"
    else:
        fallback_script = f"Let's explore the core principles of {prompt_topic}. Understanding complex subjects requires breaking them down into fundamental data points. Through structural analysis and consistency, you can master the mechanics behind how it works."
        fallback_keyword = "abstract technology"
    
    url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
    system_prompt = (
        "Respond EXACTLY in this format, replacing the bracketed text:\n"
        "KEYWORDS: [1-2 simple, lowercase video search terms, e.g. 'science' or 'nature']\n"
        "SCRIPT: [A fascinating 3-sentence educational answer, around 40 words max. No emojis, no markdown.]\n\n"
        f"User Question: {prompt_topic}"
    )
    
    print("[AI ENGINE] Querying open-source model for custom script...")
    try:
        response = requests.post(url, json={"inputs": system_prompt, "parameters": {"max_new_tokens": 150}}, timeout=12)
        if response.status_code == 200:
            gen_text = response.json()[0].get("generated_text", "") if isinstance(response.json(), list) else response.json().get("generated_text", "")
            gen_text = gen_text.replace(system_prompt, "")
            
            # Flexible parsing that handles various casing styles safely
            clean_text = gen_text.upper()
            if "KEYWORDS:" in clean_text and "SCRIPT:" in clean_text:
                parts = gen_text.split("SCRIPT:") if "SCRIPT:" in gen_text else gen_text.split("script:")
                kw_part = parts[0].replace("KEYWORDS:", "").replace("keywords:", "").replace("[", "").replace("]", "").strip()
                sc_part = parts[1].replace("[", "").replace("]", "").strip()
                
                # Double-check that the AI didn't return an empty or microscopic response
                if len(sc_part.split()) > 10 and len(kw_part) > 2:
                    return sc_part, kw_part
        print(f"[AI ENGINE INFO] Status {response.status_code}. Deploying specialized template.")
    except Exception as e:
        print(f"[AI ENGINE WARNING] Request timed out ({e}). Using safety backup.")
        
    return fallback_script, fallback_keyword

# Execute script generation
SCRIPT_TEXT, SEARCH_KEYWORD = get_ai_script_and_keywords(TOPIC)
print(f"[BOT AI] Final Script Text: \"{SCRIPT_TEXT}\"")
print(f"[BOT AI] Selected Visual Keyword: '{SEARCH_KEYWORD}'")

# ==========================================
# 2. GENERATE AI VOICE (EDGE-TTS)
# ==========================================
VOICE_FILE = "voice.mp3"
async def generate_voice():
    import edge_tts
    # Clean professional tone suitable for educational content
    communicate = edge_tts.Communicate(SCRIPT_TEXT, "en-US-ChristopherNeural")
    await communicate.save(VOICE_FILE)

print("[TTS ENGINE] Commencing speech synthesis...")
asyncio.run(generate_voice())

# ==========================================
# 3. FETCH MATCHING BACKGROUND FROM PEXELS
# ==========================================
PEXELS_KEY = os.getenv("PEXELS_API_KEY")
VIDEO_FILE = "background.mp4"

if not PEXELS_KEY:
    print("[ERROR] PEXELS_API_KEY is missing from GitHub Secrets!")
    sys.exit(1)

headers = {"Authorization": PEXELS_KEY}
url = f"https://api.pexels.com/videos/search?query={SEARCH_KEYWORD}&per_page=5&orientation=portrait"

print(f"[PEXELS API] Searching stock library for '{SEARCH_KEYWORD}'...")
try:
    response = requests.get(url, headers=headers, timeout=15).json()
    video_data = random.choice(response['videos'])
    download_url = next(f['link'] for f in video_data['video_files'] if f['width'] <= 1080)
    
    with open(VIDEO_FILE, "wb") as f:
        f.write(requests.get(download_url, timeout=20).content)
except Exception as e:
    print(f"[PEXELS FALLBACK] No direct asset match found. Pulling generic safe medical/nature asset...")
    alt_url = "https://api.pexels.com/videos/search?query=science&per_page=1&orientation=portrait"
    response = requests.get(alt_url, headers=headers, timeout=15).json()
    download_url = response['videos'][0]['video_files'][0]['link']
    with open(VIDEO_FILE, "wb") as f:
        f.write(requests.get(download_url).content)

# ==========================================
# 4. TYPOGRAPHY ASSET CONFIGURATION
# ==========================================
FONT_FILE = "Montserrat-Bold.ttf"
try:
    if not os.path.exists(FONT_FILE):
        r = requests.get("https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Bold.ttf", timeout=10)
        with open(FONT_FILE, "wb") as f:
            f.write(r.content)
    video_font = ImageFont.truetype(FONT_FILE, 65)
    line_h = 90
except Exception as e:
    print(f"[FONT WARNING] Core asset issue ({e}). Using native fallback.")
    video_font = ImageFont.load_default()
    line_h = 25

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
# 5. FRAME STAMPING COMPOSITOR
# ==========================================
audio_track = AudioFileClip(VOICE_FILE)
duration = max(audio_track.duration, 3.0)  # Enforce minimum duration threshold

bg_clip = VideoFileClip(VIDEO_FILE).without_audio()
if bg_clip.duration < duration:
    bg_clip = bg_clip.loop(duration=duration)
else:
    bg_clip = bg_clip.subclip(0, duration)

bg_clip = bg_clip.resize(newsize=(1080, 1920))

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
        
        for dx, dy in [(-3,-3), (3,-3), (-3,3), (3,3), (-1,-1), (1,-1), (-1,1), (1,1)]:
            draw.text((start_x + dx, curr_y + dy), line, font=video_font, fill=(0, 0, 0))
            
        draw.text((start_x, curr_y), line, font=video_font, fill=(255, 255, 255))
        
    return np.array(img)

print("[COMPOSITOR] Merging audio and visual frames...")
final_video = bg_clip.fl_image(add_captions_to_frame).set_audio(audio_track)

output_filename = "output.mp4"
final_video.write_videofile(
    output_filename,
    fps=24,
    codec="libx264",
    audio_codec="aac",
    threads=4,
    logger=None
)

# Print verification statistics directly into the GitHub log
if os.path.exists(output_filename):
    size_mb = os.path.getsize(output_filename) / (1024 * 1024)
    print(f"[SUCCESS] Master production output verified. File size: {size_mb:.2f} MB")
else:
    print("[ERROR] Render process finished but target output file was not found.")
