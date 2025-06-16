import os
import subprocess
import requests
import whisper
import random
from datetime import timedelta
from elevenlabs.client import ElevenLabs
from elevenlabs import save
from rich.console import Console
from rich.text import Text

DIR_BASE_DIRECTORY = "YOUR_DIRECTORY"

# --------- CONFIG ---------
VIDEOS_DIR = DIR_BASE_DIRECTORY
VOICE_OUTPUT = "voice.mp3"
VIDEO_WITH_VOICE = "video_with_voice.mp4"
SUBTITLE_FILE = "subtitles.ass"
FINAL_OUTPUT = "final_output.mp4"
ELEVEN_API_KEY = "ELEVEN_LABS_API_KEY"
VOICE_ID = "ELEVEN_LABS_VOICE_ID"
WHISPER_MODEL = "base"  # or "small", "medium", "large"
FONT_NAME = "Adwaita Sans"
FONT_SIZE = 14
MAX_WORDS_PER_SUBTITLE = 4

USE_GPU = True  # Set to False to disable GPU acceleration
GPU_ENCODER = "h264_nvenc"  # Options: "h264_nvenc", "hevc_nvenc", "h264_vaapi", "h264_qsv"
GPU_DECODER = "h264_cuvid"  # Options: "h264_cuvid", "hevc_cuvid", None for CPU decoding

# Random video segment settings
USE_RANDOM_SEGMENT = True  # Set to False to use full video
MIN_SEGMENT_DURATION = 30  # Minimum segment duration in seconds
MAX_SEGMENT_DURATION = 180  # Maximum segment duration in seconds (3 minutes)



console = Console()


# ==== Video Utilities ====
def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        console.print(f"❌ [red]Could not get duration for {video_path}[/]")
        return None


def get_random_segment(video_duration, voice_duration):
    """Calculate random start time and duration for video segment"""
    if not USE_RANDOM_SEGMENT:
        return 0, min(video_duration, voice_duration + 5)  # Add 5 seconds buffer
    
    # Determine segment duration based on voice duration
    target_duration = max(voice_duration + 10, MIN_SEGMENT_DURATION)  # Add buffer
    target_duration = min(target_duration, MAX_SEGMENT_DURATION, video_duration)
    
    # Calculate random start time
    max_start_time = max(0, video_duration - target_duration)
    start_time = random.uniform(0, max_start_time) if max_start_time > 0 else 0
    
    console.print(f"🎲 [yellow]Random segment:[/] {start_time:.1f}s to {start_time + target_duration:.1f}s")
    return start_time, target_duration


def get_audio_duration(audio_path):
    """Get audio duration in seconds"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        console.print(f"❌ [red]Could not get duration for {audio_path}[/]")
        return 60  # Default fallback


def check_gpu_support():
    """Check if GPU encoding is available"""
    if not USE_GPU:
        return False, "CPU", "CPU"
        
    try:
        # Test NVENC support
        cmd = ["ffmpeg", "-hide_banner", "-encoders"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if GPU_ENCODER in result.stdout:
            console.print(f"✅ [green]GPU encoder {GPU_ENCODER} available[/]")
            return True, GPU_ENCODER, GPU_DECODER
        else:
            console.print(f"❌ [yellow]GPU encoder {GPU_ENCODER} not available, using CPU[/]")
            return False, "libx264", None
            
    except subprocess.CalledProcessError:
        console.print("❌ [yellow]Could not check GPU support, using CPU[/]")
        return False, "libx264", None


def list_videos(directory):
    return [f for f in os.listdir(directory) if f.endswith((".mp4", ".mkv", ".mov"))]


def select_video(videos):
    for idx, video in enumerate(videos):
        console.print(f"[bold cyan]{idx}[/]: {video}")
    return os.path.join(VIDEOS_DIR, videos[0])


def overlay_voice_on_video(video_path, audio_path, output_path):
    console.print("🎬 [bold green]Cropping video to 9:16 and adding voice-over...[/]")

    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
        "-vf", "crop=in_h*9/16:in_h,scale=1080:1920",
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-c:a", "aac", "-shortest", output_path
    ]
    subprocess.run(cmd, check=True)
    console.print(f"✅ [green]Video processed with voice-over:[/] {output_path}")


def format_time_ass(seconds):
    """Format time for ASS subtitle format"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 100)  # ASS uses centiseconds
    return f"{h:01}:{m:02}:{s:02}.{ms:02}"


# ==== ElevenLabs ====
def get_voice_from_elevenlabs(text, output_path):
    elevenlabs = ElevenLabs(api_key=ELEVEN_API_KEY)
    console.print("🔊 [bold yellow]Generating voice with ElevenLabs SDK...[/]")
    audio = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    save(audio, output_path)
    console.print(f"✅ [green]Voice-over saved to:[/] {output_path}")


def chunk_text_by_words(text, start_time, end_time, max_words=4):
    """Chunk text into groups of words with proper timing"""
    words = text.strip().split()
    if not words:
        return []
    
    chunks = []
    for i in range(0, len(words), max_words):
        chunk_words = words[i:i+max_words]
        chunks.append(' '.join(chunk_words))
    
    if not chunks:
        return []
    
    total_duration = end_time - start_time
    duration_per_chunk = total_duration / len(chunks)
    
    timings = []
    for i, chunk in enumerate(chunks):
        chunk_start = start_time + i * duration_per_chunk
        chunk_end = min(chunk_start + duration_per_chunk, end_time)
        timings.append((chunk_start, chunk_end, chunk.upper()))
    
    return timings


# ==== Subtitles ====
def generate_subtitles_with_whisper(audio_path, output_path, speed_factor=1.3):
    console.print("🧠 Generating subtitles using Whisper...")
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(audio_path)

    ass_output = output_path.replace(".srt", ".ass")
    console.print("Generating subtitle file with speed compensation...")
    
    with open(ass_output, "w", encoding="utf-8") as f:
        # ASS Header
        f.write("[Script Info]\n")
        f.write("Title: Generated Subtitles\n")
        f.write("ScriptType: v4.00+\n")
        f.write("WrapStyle: 0\n")
        f.write("ScaledBorderAndShadow: yes\n")
        f.write("YCbCr Matrix: TV.709\n\n")
        
        # Styles section
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        # Center alignment (5), white text, black outline, bold
        f.write(f"Style: Default,{FONT_NAME},{FONT_SIZE},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,1,5,10,10,30,1\n\n")
        
        # Events section
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        # Process each segment from Whisper
        for segment in result["segments"]:
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            
            if not text:
                continue
                
            # Adjust timing for speed change - divide by speed factor to compensate
            adjusted_start = start / speed_factor
            adjusted_end = end / speed_factor
            
            # Break text into chunks of 4-5 words
            chunks = chunk_text_by_words(text, adjusted_start, adjusted_end, MAX_WORDS_PER_SUBTITLE)
            
            for chunk_start, chunk_end, chunk_text in chunks:
                start_ts = format_time_ass(chunk_start)
                end_ts = format_time_ass(chunk_end)
                # Clean text and make uppercase
                clean_text = chunk_text.replace('\n', ' ').strip()
                f.write(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{clean_text}\n")

    console.print(f"✅ Styled subtitles saved to {ass_output} (adjusted for {speed_factor}x speed)")
    return ass_output


def process_final_video(input_video, voice_audio, subtitles_path, output_path):
    console.print("🎬 Processing final video with voice, subtitles, crop, and 1.3× speed...")

    # Check GPU support
    use_gpu, video_encoder, video_decoder = check_gpu_support()
    
    # Get video and audio durations
    video_duration = get_video_duration(input_video)
    voice_duration = get_audio_duration(voice_audio)
    
    if video_duration is None:
        console.print("❌ [red]Could not determine video duration[/]")
        return
    
    # Get random segment
    start_time, segment_duration = get_random_segment(video_duration, voice_duration)
    
    # Escape the subtitle path for ffmpeg
    escaped_subtitles = subtitles_path.replace(':', '\\:').replace(',', '\\,')
    
    # Build ffmpeg command with GPU support and random segment
    input_params = []
    if use_gpu and video_decoder:
        input_params.extend(["-hwaccel", "cuda", "-c:v", video_decoder])
    
    # Add seek and duration for random segment
    input_params.extend(["-ss", str(start_time), "-t", str(segment_duration)])
    
    # Use simpler filter chain - apply speed change to video only, keep audio normal speed
    # then sync subtitles with the sped-up video
    cmd = [
        "ffmpeg", "-y"
    ] + input_params + [
        "-i", input_video,
        "-i", voice_audio,
        "-filter_complex",
        f"[0:v]crop=in_h*9/16:in_h,scale=1080:1920,setpts=PTS/1.3[v_speed];"
        f"[v_speed]ass={escaped_subtitles}[v];"
        f"[1:a]atempo=1.3[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", video_encoder,
        "-c:a", "aac"
    ]
    
    # Add GPU-specific parameters
    if use_gpu and "nvenc" in video_encoder:
        cmd.extend([
            "-preset", "p4",  # Fast preset for NVENC
            "-tune", "hq",    # High quality
            "-rc", "vbr",     # Variable bitrate
            "-cq", "23",      # Quality level (lower = better quality)
            "-b:v", "5M",     # Target bitrate
            "-maxrate", "8M", # Max bitrate
            "-bufsize", "10M" # Buffer size
        ])
    elif use_gpu and "vaapi" in video_encoder:
        cmd.extend(["-vaapi_device", "/dev/dri/renderD128", "-qp", "23"])
    elif use_gpu and "qsv" in video_encoder:
        cmd.extend(["-preset", "fast", "-global_quality", "23"])
    else:
        cmd.extend(["-preset", "fast", "-crf", "23"])
    
    cmd.extend(["-shortest", output_path])

    try:
        console.print(f"🚀 [cyan]Using {'GPU' if use_gpu else 'CPU'} acceleration[/]")
        console.print(f"⏱️ [cyan]Processing segment: {start_time:.1f}s - {start_time + segment_duration:.1f}s[/]")
        subprocess.run(cmd, check=True)
        console.print(f"✅ [green]Final video saved to:[/] {output_path}")
    except subprocess.CalledProcessError as e:
        console.print(f"❌ [red]Error processing video:[/] {e}")
        console.print("Trying fallback method...")
        
        # Fallback method with better subtitle timing
        cmd_fallback = [
            "ffmpeg", "-y",
            "-ss", str(start_time), "-t", str(segment_duration),
            "-i", input_video,
            "-i", voice_audio,
            "-filter_complex",
            f"[0:v]crop=in_h*9/16:in_h,scale=1080:1920[v_crop];"
            f"[v_crop]setpts=PTS/1.3[v_speed];"
            f"[v_speed]subtitles={subtitles_path}:force_style='Alignment=5,Fontsize={FONT_SIZE},Fontname={FONT_NAME},PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Bold=1,Outline=2'[v];"
            f"[1:a]atempo=1.3[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-c:a", "aac", "-preset", "fast", "-crf", "23", "-shortest",
            output_path
        ]
        subprocess.run(cmd_fallback, check=True)
        console.print(f"✅ [green]Final video saved to:[/] {output_path}")


def embed_subtitles(video_path, subtitle_path, output_path):
    """Alternative subtitle embedding method"""
    console.print("🎞️ [bold cyan]Embedding styled subtitles into video...[/]")

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"ass={subtitle_path},setpts=PTS/1.3",
        "-filter:a", "atempo=1.3",
        "-c:v", "libx264", "-c:a", "aac", "-preset", "fast",
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
        console.print(f"✅ [green]Final video with subtitles saved to:[/] {output_path}")
    except subprocess.CalledProcessError:
        console.print("❌ [red]ASS filter failed, trying subtitles filter...[/]")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"subtitles={subtitle_path}:force_style='Alignment=5,Fontsize={FONT_SIZE}',setpts=PTS/1.3",
            "-filter:a", "atempo=1.3",
            "-c:v", "libx264", "-c:a", "aac", "-preset", "fast",
            output_path
        ]
        subprocess.run(cmd, check=True)
        console.print(f"✅ [green]Final video with subtitles saved to:[/] {output_path}")


# ==== Preview ====
def preview_subtitle_style():
    sample = Text("THIS IS A SUBTITLE PREVIEW", style="bold white on black")
    console.rule("[bold yellow]Font Preview")
    console.print(sample, justify="center")
    console.rule()

# ==== Main ====
def main():
    console.print("📂 [bold blue]Scanning for videos...[/]")
    videos = list_videos(VIDEOS_DIR)
    if not videos:
        console.print("❌ [red]No videos found in directory.[/]")
        return

    selected_video = select_video(videos)
    console.print(f"🎥 Selected video: [bold]{selected_video}[/]")
    
    console.print(f"⚙️ [cyan]Settings:[/]")
    console.print(f"  • GPU Acceleration: {'✅ ON' if USE_GPU else '❌ OFF'}")
    console.print(f"  • Random Segments: {'✅ ON' if USE_RANDOM_SEGMENT else '❌ OFF'}")
    if USE_RANDOM_SEGMENT:
        console.print(f"  • Segment Range: {MIN_SEGMENT_DURATION}s - {MAX_SEGMENT_DURATION}s")
    console.print(f"  • Words per subtitle: {MAX_WORDS_PER_SUBTITLE}")

    text = input("✍️ Enter voice-over text: ").strip()
    if not text:
        print("❌ Text cannot be empty.")
        return

    preview_subtitle_style()

    get_voice_from_elevenlabs(text, VOICE_OUTPUT)
    generate_subtitles_with_whisper(VOICE_OUTPUT, SUBTITLE_FILE)
    process_final_video(selected_video, VOICE_OUTPUT, SUBTITLE_FILE, FINAL_OUTPUT)

    console.print("\n✅ [bold green]All steps completed successfully![/]")


if __name__ == "__main__":
    main()
