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
# 1. INITIALIZATION & CONFIGURATION
# ==========================================
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("[SYSTEM WARNING] HF_TOKEN environment variable is missing. Utilizing safe script fallback.")

# Download typography font to handle standalone Linux headless environments
FONT_PATH = "Roboto-Bold.ttf"
if not os.path.exists(FONT_PATH):
    print("[ASSET] Downloading premium typography font...")
    font_url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    try:
        r = requests.get(font_url, timeout=15)
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)
        print("[ASSET] Font saved locally.")
    except Exception as e:
        print(f"[ASSET CLEAR] Font download skipped: {e}. Reverting to default canvas settings.")
        FONT_PATH = None

# ==========================================
# 2. AI SCRIPT GENERATION ENGINE
# ==========================================
print("[AI ENGINE] Requesting narrative contents from Hugging Face...")
script_data = []

if HF_TOKEN:
    try:
        client = InferenceClient(api_key=HF_TOKEN)
        prompt = (
            "Generate a highly viral TikTok video script about deep psychological facts or scary space facts. "
            "Provide exactly 9 to 12 segments to ensure the voiceover duration comfortably exceeds 60 seconds. "
            "Output your answer STRICTLY as a single JSON array of objects with no preamble text or markdown backticks outside. "
            "Each object must contain keys 'text' (the spoken words) and 'scene' (short descriptive mood keyword)."
        )
        response = client.text_generation(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            prompt=prompt,
            max_new_tokens=2048,
            temperature=0.75
        ).strip()
        
        # Clean potential conversational formatting blocks safely without line breaking
        if "```json" in response:
            match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if match:
                response = match.group(1).strip()
        elif "```" in response:
            match = re.search(r"```\s*(.*?)\s*```", response, re.DOTALL)
            if match:
                response = match.group(1).strip()

        script_data = json.loads(response)
        print(f"[AI ENGINE] Successfully ingested {len(script_data)} narrative visual segments.")
    except Exception as e:
        print(f"[AI ENGINE] Parsing pipeline failed: {e}. Engaging manual backup block.")
        script_data = []

# Fail-safe backup data guaranteeing script completeness under any network condition
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
# 3. VOICE SYNTHESIS & TIMING CALIBRATION
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
    
    positioned_chunk = chunk.with_start(current_time)
    audio_clips.append(positioned_chunk)
    current_time += duration

# Strategic monetization check: Append high-retention outro if clip falls below 60 seconds
if current_time < 61.0:
    print(f"[MONETIZATION] Duration ({current_time:.2f}s) is short of the threshold. Crafting retention outro segment...")
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
print(f"[AUDIO ENGINE] Balanced timeline finalized. Composite Video Length: {total_video_duration:.2f} seconds.")

# ==========================================
# 4. PROCEDURAL GRAPHICS AND RENDERING ENGINE
# ==========================================
def make_frame(t):
    # Standard TikTok 9:16 vertical resolution orientation
    W, H = 1080, 1920
    
    # Locate active text block for the timestamp
    active_segment = None
    for item in script_data:
        if item["start"] <= t <= item["end"]:
            active_segment = item
            break
    if not active_segment and script_data:
        active_segment = script_data[-1]

    # Generate a shifting dark cosmic dust base matrix
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
    
    # Render starry layer
    np.random.seed(101)
    for _ in range(75):
        star_x = np.random.randint(0, W)
        star_y = np.random.randint(0, H)
        diameter = np.random.randint(1, 4)
        brightness = int(140 + 115 * np.sin(t * 2.5 + star_x))
        draw_context.ellipse([star_x, star_y, star_x + diameter, star_y + diameter], fill=(brightness, brightness, brightness))
        
    # Render typography subtitles
    if active_segment:
        raw_words = active_segment["text"].split()
        text_font = None
        try:
            if FONT_PATH:
                text_font = ImageFont.truetype(FONT_PATH, 52)
        except:
            pass
        if not text_font:
            text_font = ImageFont.load_default()
            
        # Word wrapping engine
        max_line_width = 860
        processed_lines = []
        working_line = []
        
        for word in raw_words:
            test_string = " ".join(working_line + [word])
            try:
                boundaries = text_font.getbbox(test_string)
                rendered_width = boundaries[2] - boundaries[0]
            except:
                rendered_width = len(test_string) * 28
                
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
            
        # Spatial text composition calculations
        spacing_offset = 22
        accumulated_text_height = 0
        layout_manifest = []
        
        for line in processed_lines:
            try:
                boundaries = text_font.getbbox(line)
                line_h = boundaries[3] - boundaries[1]
            except:
                line_h = 55
            layout_manifest.append((line, line_h))
            accumulated_text_height += line_h + spacing_offset
            
        if accumulated_text_height > 0:
            accumulated_text_height -= spacing_offset
            
        # Center-align vertical drawing sequence
        draw_y = (H / 2) - (accumulated_text_height / 2)
        for line, line_h in layout_manifest:
            try:
                boundaries = text_font.getbbox(line)
                line_w = boundaries[2] - boundaries[0]
            except:
                line_w = len(line) * 28
            draw_x = (W / 2) - (line_w / 2)
            
            # High-contrast background drop outline shadows
            for offset_x in [-3, 0, 3]:
                for offset_y in [-3, 0, 3]:
                    draw_context.text((draw_x + offset_x, draw_y + offset_y), line, font=text_font, fill=(0, 0, 0))
                    
            # High-visibility viral yellow text fill
            draw_context.text((draw_x, draw_y), line, font=text_font, fill=(255, 235, 15))
            draw_y += line_h + spacing_offset

    return np.array(frame_image)

# ==========================================
# 5. VIDEO RENDER ASSEMBLER
# ==========================================
print("[COMPOSITOR] Structuring virtual frame generators...")
raw_video_track = VideoClip(make_frame, duration=total_video_duration)
final_video_output = raw_video_track.with_audio(final_audio_track)

target_filename = "tiktok_viral_video.mp4"
print(f"[COMPOSITOR] Rendering video layers into high definition output target: '{target_filename}'...")

final_video_output.write_videofile(
    target_filename,
    fps=24,
    codec="libx264",
    audio_codec="aac"
)

print("[COMPOSITOR] Video file generated successfully.")

# Resource housecleaning procedures to free filesystem handles
print("[CLEANER] Running structural pipeline asset housecleaning...")
final_audio_track.close()
raw_video_track.close()
for temp_file in temp_audio_files:
    try:
        os.remove(temp_file)
    except:
        pass
print("[CLEANER] Housecleaning completed.")

# ==========================================
# 6. RENDER SERVICE HEALTH KEEPALIVE DAEMON
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

# Launch background server loop
keepalive_worker = threading.Thread(target=serve_keep_alive, daemon=True)
keepalive_worker.start()

# Keep main processing thread pinned alive to prevent platform container cycles
print("[SYSTEM] Video processing loop complete. Keeping server process active for platform access.")
threading.Event().wait()
