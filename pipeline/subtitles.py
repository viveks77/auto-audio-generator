import whisper
from pipeline.sub_format import format_time_ass, create_highlighted_subtitle
from pipeline.utils import console
from config import CONFIG



def generate_subtitles(audio_path, output_path, speed_factor=1.3, device=None):
    console.print("🧠 [bold yellow]Generating enhanced subtitles using Whisper...[/]")
    whisper_device = device or CONFIG.get("WHISPER_DEVICE", "cpu")
    model = whisper.load_model(CONFIG["WHISPER_MODEL"], device=whisper_device)
    result = model.transcribe(audio_path, word_timestamps=True)

    ass_output = output_path.replace(".srt", ".ass")
    with open(ass_output, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nTitle: Enhanced Subtitles\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        fancy_font = CONFIG.get('FONT_NAME', 'Montserrat')
        font_size = CONFIG.get('FONT_SIZE', 78)
        outline_size = CONFIG.get('OUTLINE_SIZE', 5)
        shadow_size = CONFIG.get('SHADOW_SIZE', 2)
        # Force white font, black outline, border style 1
        primary = '&H00FFFFFF'   # white
        outline = '&H00000000'   # black
        shadow = '&H80000000'    # semi-transparent black
        background = '&H00000000' # transparent
        # Style: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
        f.write(f"Style: Default,{fancy_font},{font_size},{primary},{primary},{outline},{background},1,0,0,0,100,100,0,0,1,{outline_size},{shadow_size},5,10,10,80,1\n\n")
        f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for segment in result["segments"]:
            words = segment.get("words", [])
            if not words:
                continue

            if CONFIG["HIGHLIGHT_MODE"] == "word":
                for word in words:
                    start = word["start"] / speed_factor
                    end = word["end"] / speed_factor
                    text = create_highlighted_subtitle([word["word"]], 0)
                    f.write(f"Dialogue: 0,{format_time_ass(start)},{format_time_ass(end)},Default,,0,0,0,,{text}\n")
            else:
                for i in range(0, len(words), CONFIG["MAX_WORDS_PER_SUBTITLE"]):
                    chunk = words[i:i + CONFIG["MAX_WORDS_PER_SUBTITLE"]]
                    chunk_text = [w["word"] for w in chunk]
                    chunk_start = chunk[0]["start"] / speed_factor
                    chunk_end = chunk[-1]["end"] / speed_factor
                    for j in range(len(chunk)):
                        word_start = chunk[j]["start"] / speed_factor
                        word_end = chunk[j]["end"] / speed_factor
                        text = create_highlighted_subtitle(chunk_text, j)
                        f.write(f"Dialogue: 0,{format_time_ass(word_start)},{format_time_ass(word_end)},Default,,0,0,0,,{text}\n")

    console.print(f"✅ [green]Subtitles saved to {ass_output}[/]")
    return ass_output
