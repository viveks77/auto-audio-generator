# Utility functions for pipeline
import subprocess
import os
from rich.console import Console
from config import CONFIG

console = Console()

def get_video_duration(video_path):
    try:
        cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        console.print(f"❌ [red]Could not get duration for {video_path}[/]")
        return None

def get_audio_duration(audio_path):
    try:
        cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        console.print(f"❌ [red]Could not get duration for {audio_path}[/]")
        return 60

def check_gpu_support():
    if not CONFIG.get("USE_GPU"):
        return False, "libx264", ""
    try:
        cmd = ["ffmpeg", "-hide_banner", "-encoders"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if CONFIG.get("GPU_ENCODER") in result.stdout:
            console.print(f"✅ [green]GPU encoder {CONFIG['GPU_ENCODER']} available[/]")
            return True, CONFIG.get("GPU_ENCODER"), CONFIG.get("GPU_DECODER")
        else:
            console.print(f"❌ [yellow]GPU encoder {CONFIG['GPU_ENCODER']} not available[/]")
            return False, "libx264", ""
    except subprocess.CalledProcessError:
        return False, "libx264", ""

def list_videos(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith((".mp4", ".mkv", ".mov"))]
