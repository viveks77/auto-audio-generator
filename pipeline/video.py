import random
import subprocess
from pipeline.utils import get_video_duration, get_audio_duration, list_videos, console


def combine_for_audio_duration(video_dir, audio_path, temp_output="output/combined.mp4"):
    import os
    console.print("🎞️ [cyan]Combining random video segments to match audio duration...[/]")
    # Ensure output directory exists
    output_dir = os.path.dirname(temp_output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    all_clips = list_videos(video_dir)
    audio_duration = get_audio_duration(audio_path)
    total = 0
    selected = []
    orig_clips = all_clips.copy()

    # Keep adding clips until we reach or exceed audio duration
    while total < audio_duration:
        if not all_clips:
            # If we've used all clips, start over (loop)
            all_clips = orig_clips.copy()
        clip = random.choice(all_clips)
        all_clips.remove(clip)
        duration = get_video_duration(clip)
        if duration:
            total += duration
            selected.append(clip)

    cmd = ["ffmpeg", "-y"]
    for path in selected:
        cmd.extend(["-i", path])

    filter_complex = "".join([f"[{i}:v:0][{i}:a:0]" for i in range(len(selected))])
    filter_complex += f"concat=n={len(selected)}:v=1:a=1[outv][outa]"

    cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "[outa]", temp_output])
    subprocess.run(cmd, check=True)
    return temp_output


def combine(video_paths, temp_output="output/combined.mp4"):
    import os
    console.print("📽️ [cyan]Combining multiple clips...[/]")
    # Ensure output directory exists
    output_dir = os.path.dirname(temp_output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    list_file = os.path.join(output_dir, "inputs.txt") if output_dir else "inputs.txt"
    with open(list_file, "w") as f:
        for path in video_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", temp_output]
    subprocess.run(cmd, check=True)
    return temp_output
