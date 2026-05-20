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
TOPIC = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() != "" else "How does the brain work"
print(f"[BOT] Target Prompt Received: '{TOPIC}'")

def get_ai_script_and_keywords(prompt_topic):
    # Reliable safety fallback defaults if the open API is congested
    fallback_script = f"Let's dive into {prompt_topic}. Understanding complex subjects requires breaking them down into their core foundational principles. By analyzing the underlying patterns and remaining consistent, anyone can master the internal mechanics of this topic."
    fallback_keyword = "abstract technology"
    
    # Utilizing a high-performance open-source LLM via Hugging Face serverless infrastructure
    url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
    
    system_prompt = (
        "Respond EXACTLY in this format, replacing the bracketed text:\n"
        "KEYWORDS: [1-2 simple, lowercase general search terms for a background video, e.g. 'space' or 'ocean']\n"
        "SCRIPT: [A fascinating 3-sentence educational answer to the user's question, around 40-50 words max. No emojis, no markdown, no introductions.]\n\n"
        f"User Question: {prompt_topic}"
    )
    
    print("[AI ENGINE] Querying open-source model for custom script...")
    try:
        response = requests.post(url, json={"inputs": system_prompt, "parameters": {"max_new_tokens": 150}}, timeout=12)
        if response.status_code == 200:
            raw_result = response.json()
            gen_text = raw_result[0].get("generated_text", "") if isinstance(raw_result, list) else raw_result.get("generated_text", "")
            
            if system_prompt in gen_text:
                gen_text = gen_text.replace(system_prompt, "")
                
            if "KEYWORDS:" in gen_text and "SCRIPT:" in gen_text:
                parts = gen_text.split("SCRIPT:")
                kw = parts[0].replace("KEYWORDS:", "").replace("[", "").replace("]", "").strip()
                sc = parts[1].replace("[", "").replace("]", "").strip()
                if kw and sc:
                    return sc, kw
        print(f"[AI ENGINE INFO] Server status {response.status_code}. Using tailored template system.")
    except Exception as e:
        print(f"[AI ENGINE WARNING] Request pool busy ({e}). Deploying adaptive fallback.")
        
    return fallback_script, fallback_keyword

# Run the live generation
SCRIPT_TEXT, SEARCH_KEYWORD = get_ai_script_and_keywords(TOPIC)
print(f"[BOT AI] Final Script Voiceover: \"{SCRIPT_TEXT}\"")
print(f"[BOT AI] Pexels Visual Keyword: '{SEARCH_KEYWORD}'")

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
# 3. FETCH MATCHING BACKGROUND FROM PEXELS
# ==========================================
PEXELS_KEY = os.getenv("PEXELS_API_KEY")
VIDEO_FILE = "background.mp4"

if not PEXELS_KEY:
    print("[ERROR] PEXELS_API_KEY is missing from GitHub Secrets!")
    sys.exit(1)

headers = {"Authorization": PEXELS_KEY}
url = f"https://api.pexels.com/videos/search?query={SEARCH_KEYWORD}&per_page=5&orientation=portrait"

print(f"[PEXELS API] Downloading stock assets matching '{SEARCH_KEYWORD}'...")
try:
    response = requests.get(url, headers=headers, timeout=15).json()
    video_data = random.choice(response['videos'])
    video_files = video_data['video_files']
    download_url = next(f['link'] for f in video_files if f['width'] <= 1080)
    
    video_bytes = requests.get(download_url, timeout=20).content
    with open(VIDEO_FILE, "wb") as f:
        f.write(video_bytes)
except Exception as e:
    print(f"[PEXELS FALLBACK] Media fetch failed for '{SEARCH_KEYWORD}'. Pulling generic city asset...")
    alt_url = "https://api.pexels.com/videos/search?query=city&per_page=1&orientation=portrait"
    response = requests.get(alt_url, headers=headers, timeout=15).json()
    download_url = response['videos'][0]['video_files'][0]['link']
    with open(VIDEO_FILE, "wb") as f:
        f.write(requests.get(download_url).content)

# ==========================================
# 4. TYPOGRAPHY & ASSET LOADING
# ==========================================
FONT_FILE = "Montserrat-Bold.ttf"
try:
    if not os.path.exists(FONT_FILE):
        print("[FONT SEEDER] Downloading high-grade bold typography assets...")
        r = requests.get("https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Bold.ttf", timeout=10)
        with open(FONT_FILE, "wb") as f:
            f.write(r.content)
    video_font = ImageFont.truetype(FONT_FILE, 65)
    line_h = 90
except Exception as e:
    print(f"[FONT WARNING] Core layout fallback deployed: {e}")
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
# 5. INLINE FRAME STAMPING COMPOSITOR
# ==========================================
print("[COMPOSITOR] Staging master tracking elements...")
audio_track = AudioFileClip(VOICE_FILE)
duration = audio_track.duration

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
        
        # Symmetrical high-contrast black shadow backing block
        for dx, dy in [(-3,-3), (3,-3), (-3,3), (3,3), (-1,-1), (1,-1), (-1,1), (1,1)]:
            draw.text((start_x + dx, curr_y + dy), line, font=video_font, fill=(0, 0, 0))
            
        # Hard white center layer typography
        draw.text((start_x, curr_y), line, font=video_font, fill=(255, 255, 255))
        
    return np.array(img)

print("[COMPOSITOR] Transforming raw pixels via frame-stamping matrix...")
final_video = bg_clip.fl_image(add_captions_to_frame).set_audio(audio_track)

print("[COMPOSITOR] Compiling broadcast production master output...")
final_video.write_videofile(
    "output.mp4",
    fps=24,
    codec="libx264",
    audio_codec="aac",
    threads=4,
    logger=None
)

print("[SUCCESS] Pipeline process ended smoothly.")
