import os
import subprocess
import requests
import whisper
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
FONT_SIZE = 95
# --------------------------



console = Console()


# ==== Video Utilities ====
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


def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02}.{ms:02}"


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


# ==== Subtitles ====
def generate_subtitles_with_whisper(audio_path, output_path):
    console.print("🧠 [bold magenta]Generating subtitles using Whisper...[/]")
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(audio_path)

    ass_output = output_path
    with open(ass_output, "w", encoding="utf-8") as f:
        # Header and style
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, "
                "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
                "MarginL, MarginR, MarginV, Encoding\n")
        f.write(f"Style: Default,{FONT_NAME},{FONT_SIZE},&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,"
                "100,100,0,0,1,2,0,5,20,20,40,1\n\n")  # center-middle

        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for segment in result["segments"]:
            start = format_time(segment["start"])
            end = format_time(segment["end"])
            text = segment["text"].strip().upper().replace('\n', '\\N')  # multi-line
            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    console.print(f"✅ [green]Styled subtitles written to:[/] {ass_output}")
    return ass_output


def embed_subtitles(video_path, subtitle_path, output_path):
    console.print("🎞️ [bold cyan]Embedding styled subtitles into video...[/]")

    style = (
        f"Alignment=10,"
        f"Fontname={FONT_NAME},"
        f"Fontsize={FONT_SIZE},"
        f"Bold=1,"
        f"Outline=1,"
        f"PrimaryColour=&HFFFFFF&,"
        f"BackColour=&H000000&,"
        f"MarginV=40,"
        f"MarginL=5"
    )

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"subtitles={subtitle_path},setpts=PTS/1.3",
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


def process_final_video(input_video, voice_audio, subtitles_path, output_path):
    print("🎬 Processing final video with voice, subtitles, crop, and 1.3× speed...")

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", voice_audio,
        "-filter_complex",
        f"[0:v]crop=in_h*9/16:in_h,scale=1080:1920,setpts=PTS/1.3,subtitles={subtitles_path}[v];"
        f"[1:a]atempo=1.3[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-c:a", "aac", "-preset", "fast", "-shortest",
        output_path
    ]

    subprocess.run(cmd, check=True)
    print(f"✅ Final video saved to: {output_path}")

# ==== Main ====
def main():
    console.print("📂 [bold blue]Scanning for videos...[/]")
    videos = list_videos(VIDEOS_DIR)
    if not videos:
        console.print("❌ [red]No videos found in directory.[/]")
        return

    selected_video = select_video(videos)
    console.print(f"🎥 Selected video: [bold]{selected_video}[/]")

    text = input("✍️ Enter voice-over text: ").strip()
    if not text:
        print("❌ Text cannot be empty.")
        return

    preview_subtitle_style()

    print(text)

    get_voice_from_elevenlabs(text, VOICE_OUTPUT)
    # overlay_voice_on_video(selected_video, VOICE_OUTPUT, VIDEO_WITH_VOICE)
    generate_subtitles_with_whisper(VOICE_OUTPUT, SUBTITLE_FILE)
    # embed_subtitles(VIDEO_WITH_VOICE, SUBTITLE_FILE, FINAL_OUTPUT)
    process_final_video(selected_video, VOICE_OUTPUT, SUBTITLE_FILE, FINAL_OUTPUT)

    console.print("\n✅ [bold green]All steps completed successfully![/]")


if __name__ == "__main__":
    main()
