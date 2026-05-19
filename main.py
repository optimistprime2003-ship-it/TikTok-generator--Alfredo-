import os
import re
import json
import requests
import threading
import numpy as np
from http.server import SimpleHTTPRequestHandler, HTTPServer
from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient
from gtts import gTTS
from moviepy import VideoClip, AudioFileClip, CompositeAudioClip

# ==========================================
# 1. IMMEDIATE RENDER HEALTH KEEPALIVE
# ==========================================
def serve_keep_alive():
    target_port = int(os.getenv("PORT", 10000))
    class HealthCheckListener(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Processing Finished</h1><p>Video target compiled.</p></body></html>")
            
    http_service = HTTPServer(('', target_port), HealthCheckListener)
    print(f"[RENDER KEEPALIVE] Health endpoint active on port {target_port}.")
    http_service.serve_forever()

# Start server instantly to prevent Render port-binding timeouts during rendering
keepalive_worker = threading.Thread(target=serve_keep_alive, daemon=True)
keepalive_worker.start()

# ==========================================
# 2. CONFIGURATION & FONTS
# ==========================================
HF_TOKEN = os.getenv("HF_TOKEN")

FONT_PATH = "Roboto-Bold.ttf"
if not os.path.exists(FONT_PATH):
    print("[ASSET] Downloading typography font...")
    font_url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    try:
        r = requests.get(font_url, timeout=15)
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"[ASSET] Font download skipped: {e}")
        FONT_PATH = None

# ==========================================
# 3. CHAT-COMPLETION AI SCRIPT ENGINE
# ==========================================
print("[AI ENGINE] Requesting narrative contents from Hugging Face...")
script_data = []

if HF_TOKEN:
    try:
        client = InferenceClient(api_key=HF_TOKEN)
        
        # Using chat completions endpoint to fix provider compatibility issues
        response_obj = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            messages=[{
                "role": "user",
                "content": (
                    "Generate a highly viral TikTok video script about deep psychological facts. "
                    "Provide exactly 9 to 12 segments to ensure the duration exceeds 60 seconds. "
                    "Output your answer STRICTLY as a raw JSON array of objects with no markdown backticks or conversational intros. "
                    "Each object must contain keys 'text' (the spoken words) and 'scene' (short descriptive keyword)."
                )
            }],
            max_tokens=2048,
            temperature=0.75
        )
        
        response = response_obj.choices[0].message.content.strip()
        
        # Sanitize markdown response variations
        if "```json" in response:
            match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if match: response = match.group(1).strip()
        elif "```" in response:
            match = re.search(r"```\s*(.*?)\s*```", response, re.DOTALL)
            if match: response = match.group(1).strip()

        script_data = json.loads(response)
        print(f"[AI ENGINE] Successfully ingested {len(script_data)} viral text blocks.")
    except Exception as e:
        print(f"[AI ENGINE] Parsing pipeline failed: {e}. Engaging manual backup block.")
        script_data = []

# High-retention data fallback backup
if not script_data:
    script_data = [
        {"text": "Deep in the dark voids of the universe, time doesn't behave the way you think it does.", "scene": "nebula"},
        {"text": "If you sit near a stellar black hole, a single hour would stretch out into decades back home on Earth.", "scene": "horizon"},
        {"text": "Your human mind experiences a parallel illusion when confronting an immediate threat.", "scene": "synapse"},
        {"text": "This defensive reflex violently distorts your working perception, transforming seconds into an eternity.", "scene": "cosmic burst"},
        {"text": "Starlight traveling across our night sky requires over one hundred thousand years to traverse our galaxy.", "scene": "starlight"},
        {"text": "Yet, from the perspective of the photon itself, time does not exist; its voyage is completely instantaneous.", "scene": "photon"},
        {"text": "Our modern reality is constructed out of ancient phantom reflections and delayed historical signals.", "scene": "deep galaxy"},
        {"text": "Every time you gaze upward into the night canopy, you are looking directly into the graveyard of dead stars.", "scene": "constellation"}
    ]

# ==========================================
# 4. AUDIO SYNTHESIS & TIMING
# ==========================================
audio_clips = []
current_time = 0.0
temp_audio_files = []

print("[AUDIO ENGINE] Commencing speech synthesis segments...")
for idx, item in enumerate(script_data):
    clean_text = item["text"]
    tts = gTTS(text=clean_text, lang='en', tld='com')
    audio_path = f"segment_{idx}.mp3"
    tts.save(audio_path)
    temp_audio_files.append(audio_path)
    
    chunk = AudioFileClip(audio_path)
    duration = chunk.duration
    
    item["start"] = current_time
    item["end"] = current_time + duration
    
    audio_clips.append(chunk.with_start(current_time))
    current_time += duration

# Safe monetization check padding
if current_time < 61.0:
    print(f"[MONETIZATION] Adjusting duration ({current_time:.2f}s) to exceed 60s standard threshold...")
    outro_text = "If these cosmic revelations shook your reality, click the follow button now and join us for more mind bending secrets."
    tts_outro = gTTS(text=outro_text, lang='en', tld='com')
    outro_path = "segment_outro.mp3"
    tts_outro.save(outro_path)
    temp_audio_files.append(outro_path)
    
    outro_chunk = AudioFileClip(outro_path)
    outro_dur = outro_chunk.duration
    
    script_data.append({
        "text": outro_text,
        "scene": "outro",
        "start": current_time,
        "end": current_time + outro_dur
    })
    
    audio_clips.append(outro_chunk.with_start(current_time))
    current_time += outro_dur

final_audio_track = CompositeAudioClip(audio_clips)
total_video_duration = current_time

# ==========================================
# 5. LOW-MEMORY GRAPHICS RENDERING
# ==========================================
def make_frame(t):
    # Downscaled to 720x1280 to save massive memory allocation under 512MB RAM
    W, H = 720, 1280
    
    active_segment = None
    for item in script_data:
        if item["start"] <= t <= item["end"]:
            active_segment = item
            break
    if not active_segment and script_data:
        active_segment = script_data[-1]

    # Generate backgrounds using standard memory constraints
    y_coords = np.linspace(0, 1, H).reshape(H, 1)
    x_coords = np.linspace(0, 1, W).reshape(1, W)
    
    channel_r = np.clip((12 + 8 * np.sin(t * 0.4 + y_coords * 2.5)), 0, 255)
    channel_g = np.clip((8 + 6 * np.cos(t * 0.3 + x_coords * 2.0)), 0, 255)
    channel_b = np.clip((24 + 12 * np.sin(t * 0.5)), 0, 255)
    
    canvas_matrix = np.zeros((H, W, 3), dtype=np.uint8)
    canvas_matrix[:, :, 0] = channel_r.astype(np.uint8)
    canvas_matrix[:, :, 1] = channel_g.astype(np.uint8)
    canvas_matrix[:, :, 2] = channel_b.astype(np.uint8)
    
    frame_image = Image.fromarray(canvas_matrix)
    draw_context = ImageDraw.Draw(frame_image)
    
    # Render static starry fields
    np.random.seed(101)
    for _ in range(45):
        star_x = np.random.randint(0, W)
        star_y = np.random.randint(0, H)
        diameter = np.random.randint(1, 3)
        brightness = int(140 + 115 * np.sin(t * 2.5 + star_x))
        draw_context.ellipse([star_x, star_y, star_x + diameter, star_y + diameter], fill=(brightness, brightness, brightness))
        
    # Process text wrap boundaries
    if active_segment:
        raw_words = active_segment["text"].split()
        text_font = None
        try:
            if FONT_PATH:
                text_font = ImageFont.truetype(FONT_PATH, 38) # Adjusted for 720p scaling
        except:
            pass
        if not text_font:
            text_font = ImageFont.load_default()
            
        max_line_width = 600
        processed_lines = []
        working_line = []
        
        for word in raw_words:
            test_string = " ".join(working_line + [word])
            try:
                boundaries = text_font.getbbox(test_string)
                rendered_width = boundaries[2] - boundaries[0]
            except:
                rendered_width = len(test_string) * 16
                
            if rendered_width <= max_line_width:
                working_line.append(word)
            else:
                if working_line:
                    processed_lines.append(" ".join(working_line))
                    working_line = [word]
                else:
                    processed_lines.append(word)
        if working_line:
            processed_lines.append(" ".join(working_line))
            
        spacing_offset = 15
        accumulated_text_height = 0
        layout_manifest = []
        
        for line in processed_lines:
            try:
                boundaries = text_font.getbbox(line)
                line_h = boundaries[3] - boundaries[1]
            except:
                line_h = 35
            layout_manifest.append((line, line_h))
            accumulated_text_height += line_h + spacing_offset
            
        if accumulated_text_height > 0:
            accumulated_text_height -= spacing_offset
            
        draw_y = (H / 2) - (accumulated_text_height / 2)
        for line, line_h in layout_manifest:
            try:
                boundaries = text_font.getbbox(line)
                line_w = boundaries[2] - boundaries[0]
            except:
                line_w = len(line) * 16
            draw_x = (W / 2) - (line_w / 2)
            
            # Subtle text drop outlines
            for offset_x in [-2, 2]:
                for offset_y in [-2, 2]:
                    draw_context.text((draw_x + offset_x, draw_y + offset_y), line, font=text_font, fill=(0, 0, 0))
                    
            draw_context.text((draw_x, draw_y), line, font=text_font, fill=(255, 235, 15))
            draw_y += line_h + spacing_offset

    return np.array(frame_image)

# ==========================================
# 6. EXECUTOR ASSEMBLY
# ==========================================
print("[COMPOSITOR] Stitching layers together...")
raw_video_track = VideoClip(make_frame, duration=total_video_duration)
final_video_output = raw_video_track.with_audio(final_audio_track)

target_filename = "tiktok_viral_video.mp4"
final_video_output.write_videofile(
    target_filename,
    fps=20, # Reduced slightly from 24 to optimize rendering speed and RAM usage
    codec="libx264",
    audio_codec="aac"
)

print("[COMPOSITOR] Clean up temporary storage tracks...")
final_audio_track.close()
raw_video_track.close()
for temp_file in temp_audio_files:
    try: os.remove(temp_file)
    except: pass

print("[SYSTEM] Output completed. Keeping web instance alive for system validation.")
threading.Event().wait()
