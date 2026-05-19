import os
import json
import re
import requests
import numpy as np
from huggingface_hub import InferenceClient
from gtts import gTTS
from moviepy.editor import VideoClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont

# Initialize the free Hugging Face inference client
# Looks for HF_TOKEN in your environment variables
hf_token = os.environ.get("HF_TOKEN")
client = InferenceClient(token=hf_token)

def download_font():
    """Downloads a bold, readable font for the TikTok captions."""
    font_url = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
    font_path = "montserrat_bold.ttf"
    if not os.path.exists(font_path):
        print("Downloading font...")
        r = requests.get(font_url)
        with open(font_path, "wb") as f:
            f.write(r.content)
    return font_path

def generate_script_and_timing():
    """Generates a structured TikTok script with segment timings using Llama 3."""
    print("Generating script and timing via Hugging Face (Llama 3)...")
    
    prompt = (
        "You are an expert TikTok content creator. Generate an engaging script about deep ocean mysteries. "
        "The script must take at least 61 seconds to read aloud to qualify for monetization. "
        "Return STRICTLY a JSON object with a single key 'segments'. No conversational introduction, no markdown backticks, no text before or after the JSON structure. "
        "The 'segments' key must map to an array of objects. Each object represents a short phrase "
        "and must have exactly two keys: 'text' (a phrase of 3 to 5 words max) and 'duration' "
        "(a float representing how many seconds it takes to read that specific phrase naturally). "
        "Ensure the total sum of durations is at least 61 seconds."
    )
    
    # Utilizing Llama-3-8B-Instruct for high-quality structured generation
    response = client.text_generation(
        prompt=f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        max_new_tokens=2048,
        temperature=0.7
    )
    
    # Clean up any potential markdown formatting the LLM accidentally returned
    clean_json_str = response.strip()
    if "```json" in clean_json_str:
        clean_json_str = clean_json_str.split("
```json")[1].split("```")[0].strip()
    elif "```" in clean_json_str:
        clean_json_str = clean_json_str.split("
```")[1].split("```")[0].strip()
        
    try:
        data = json.loads(clean_json_str)
        return data["segments"]
    except Exception as e:
        print("Failed to parse JSON directly. Attempting regex rescue...")
        # Fallback regex parsing if the LLM output included conversational text
        json_match = re.search(r'\{\s*"segments".*\}', clean_json_str, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))["segments"]
        raise ValueError(f"Could not parse valid JSON from LLM output: {clean_json_str}")

def generate_voiceover(full_text):
    """Generates a free text-to-speech file using Google TTS."""
    print("Generating free voiceover audio via gTTS...")
    output_audio_path = "voiceover.mp3"
    
    # 'en' for English, tld='co.uk' or 'com' can be used to tweak accent styles slightly
    tts = gTTS(text=full_text, lang='en', tld='com', slow=False)
    tts.save(output_audio_path)
    return output_audio_path

def create_video_pipeline(script_segments, audio_path, font_path):
    """Assembles the video frames and merges the audio track."""
    print("Starting video composition...")
    
    timeline = []
    current_time = 0.0
    for segment in script_segments:
        start = current_time
        end = current_time + segment["duration"]
        timeline.append({"text": segment["text"].upper(), "start": start, "end": end})
        current_time = end
        
    total_duration = current_time

    def make_frame(t):
        # Create a deep-sea dark theme canvas (1080x1920 vertical)
        image = Image.new("RGB", (1080, 1920), color=(10, 15, 28))
        draw = ImageDraw.Draw(image)
        
        current_text = ""
        for clip in timeline:
            if clip["start"] <= t < clip["end"]:
                current_text = clip["text"]
                break
        if not current_text and timeline:
            current_text = timeline[-1]["text"]
            
        if current_text:
            font = ImageFont.truetype(font_path, 65)
            
            try:
                bbox = draw.textbbox((0, 0), current_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                text_width, text_height = draw.textsize(current_text, font=font)
                
            x = (1080 - text_width) // 2
            y = (1920 - text_height) // 2
            
            # Dynamic high-contrast caption bubble
            padding = 25
            draw.rectangle(
                [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
                fill=(0, 242, 234) # Vibrant TikTok Cyan for high visual retention
            )
            draw.text((x, y), current_text, font=font, fill=(0, 0, 0))
            
        return np.array(image)

    print("Rendering video file (running ffmpeg backend processing)...")
    video_clip = VideoClip(make_frame, duration=total_duration)
    audio_clip = AudioFileClip(audio_path)
    
    # Attach and sync the audio track
    final_video = video_clip.set_audio(audio_clip)
    
    final_video.write_videofile(
        "free_tiktok_output.mp4",
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="veryfast"
    )
    
    video_clip.close()
    audio_clip.close()
    print("Success! 'free_tiktok_output.mp4' has been saved.")

if __name__ == "__main__":
    if not hf_token:
        print("Warning: HF_TOKEN environment variable not found. Requesting unauthenticated public endpoint...")
        
    font_file = download_font()
    segments = generate_script_and_timing()
    
    full_script_text = " ".join([seg["text"] for seg in segments])
    audio_file = generate_voiceover(full_script_text)
    
    create_video_pipeline(segments, audio_file, font_file)
