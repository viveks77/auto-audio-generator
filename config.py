# Configuration for auto-audio-generator pipeline

CONFIG = {
    "DIR_BASE_DIRECTORY": "",
    "VIDEOS_DIR": "",
    "VOICE_OUTPUT": "voice.mp3",
    "VIDEO_WITH_VOICE": "video_with_voice.mp4",
    "SUBTITLE_FILE": "subtitles.ass",
    "FINAL_OUTPUT": "final_output.mp4",
    "ELEVEN_API_KEY": "",
    "VOICE_ID": "",
    "WHISPER_MODEL": "base",
    "FONT_NAME": "Inter",
    "FONT_SIZE": 102,
    "OUTLINE_SIZE": 5,
    "SHADOW_SIZE": 2,
    "MAX_WORDS_PER_SUBTITLE": 5,
    "USE_GPU": True,
    "USE_RANDOM_SEGMENT": True,
    "MIN_SEGMENT_DURATION": 30,
    "MAX_SEGMENT_DURATION": 120,
    "GPU_ENCODER": "h264_nvenc",
    "GPU_DECODER": "h264_cuvid",
    "IS_COMBINED": True,
    "HIGHLIGHT_MODE": "word",
    # Subtitle font color settings (ASS format: &HAABBGGRR)
    "FONT_COLOR_PRIMARY": "&H00FFFFFF",      # white
    "FONT_COLOR_OUTLINE": "&H00000000",      # black
    "FONT_COLOR_SHADOW": "&H80000000",       # semi-transparent black
    "FONT_COLOR_BACKGROUND": "&H000000FF",   # blue (example, not always used)
    # Subtitle text styling
    "SUBTITLE_BOLD": True,                   # bold text
    "SUBTITLE_BLUR": 3,                      # blur effect for highlighted words
    "SUBTITLE_SHADOW": 0,                    # shadow effect for highlighted words
    # Highlighted word color (ASS format: &HAABBGGRR)
    "HIGHLIGHT_COLOR_PRIMARY": "&H00FFFFFF", # white (same as normal for now)
    "HIGHLIGHT_COLOR_OUTLINE": "&H00000000"  # black outline
}
