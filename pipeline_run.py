"""
Pipeline runner for auto-audio-generator
Allows skipping modules via CLI flags or config.
"""
import argparse
from config import CONFIG
from pipeline.voice import generate_voice
from pipeline.subtitles import generate_subtitles
from pipeline.video import combine_for_audio_duration, combine
from pipeline.finalize import process_video
from pipeline.utils import list_videos
from rich.console import Console
import os

console = Console()

def run_pipeline(skip_voice=False, skip_subtitles=False, skip_video=False, text=None, reddit_title=None):
    # 1. Get text from user if not provided (multiline, preserve all chars)
    if not text:
        console.print("[bold blue]Enter the text for voice generation (Ctrl+D to finish):[/]")
        try:
            import sys
            text = sys.stdin.read()
        except Exception as e:
            console.print(f"❌ [red]Error reading text: {e}[/]")
            return
    if not text or not text.strip():
        console.print("❌ [red]No text provided for voice generation.[/]")
        return

    # 2. Generate audio
    if not skip_voice:
        try:
            generate_voice(text, CONFIG["VOICE_OUTPUT"])
            console.print(f"[green]Voice generated: {CONFIG['VOICE_OUTPUT']}")
        except Exception as e:
            console.print(f"❌ [red]Voice generation failed: {e}[/]")
            return
    else:
        console.print("[yellow]Skipping voice generation")

    # 3. Combine video clips to match audio duration
    if not skip_video:
        try:
            selected_video = combine_for_audio_duration(CONFIG["VIDEOS_DIR"], CONFIG["VOICE_OUTPUT"])
            console.print(f"🎥 Using video: {selected_video}")
        except Exception as e:
            console.print(f"❌ [red]Video combining failed: {e}[/]")
            return
    else:
        video_files = list_videos(CONFIG["VIDEOS_DIR"])
        if not video_files:
            console.print("❌ [red]No video files found.[/]")
            return
        # selected_video = video_files[0]
        selected_video = os.path.join(CONFIG["DIR_BASE_DIRECTORY"], "output/combined.mp4")
        console.print(f"[yellow]Skipping video combining, using first video: {selected_video}")

    # 4. Generate subtitles
    if not skip_subtitles:
        try:
            generate_subtitles(CONFIG["VOICE_OUTPUT"], CONFIG["SUBTITLE_FILE"])
            console.print(f"[green]Subtitles generated: {CONFIG['SUBTITLE_FILE']}")
        except Exception as e:
            console.print(f"❌ [red]Subtitle generation failed: {e}[/]")
            return
    else:
        console.print("[yellow]Skipping subtitle generation")

    # 5. Finalize video
    try:
        process_video(selected_video, CONFIG["VOICE_OUTPUT"], CONFIG["SUBTITLE_FILE"], CONFIG["FINAL_OUTPUT"], reddit_title)
        console.print(f"[bold green]Pipeline complete! Output: {CONFIG['FINAL_OUTPUT']}")
    except Exception as e:
        console.print(f"❌ [red]Final video processing failed: {e}[/]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the audio-video pipeline with optional skips.")
    parser.add_argument('--skip-voice', action='store_true', help='Skip voice generation')
    parser.add_argument('--skip-subtitles', action='store_true', help='Skip subtitle generation')
    parser.add_argument('--skip-video', action='store_true', help='Skip video combining')
    parser.add_argument('--text', type=str, help='Text for voice generation')
    parser.add_argument('--reddit-title', type=str, help='Custom Reddit post title for the card')
    args = parser.parse_args()
    run_pipeline(skip_voice=args.skip_voice, skip_subtitles=args.skip_subtitles, skip_video=args.skip_video, text=args.text, reddit_title=args.reddit_title)
