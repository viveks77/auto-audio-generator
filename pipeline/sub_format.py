# Subtitle formatting helpers
from config import CONFIG


def format_time_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 100)
    return f"{h:01}:{m:02}:{s:02}.{ms:02}"


def create_highlighted_subtitle(words, highlight_index):
    outline_size = CONFIG.get('OUTLINE_SIZE', 5)
    bold = 1 if CONFIG.get('SUBTITLE_BOLD', True) else 0
    blur = CONFIG.get('SUBTITLE_BLUR', 3)
    shadow = CONFIG.get('SUBTITLE_SHADOW', 0)
    
    # Normal word colors
    normal_color = CONFIG.get('FONT_COLOR_PRIMARY', '&H00FFFFFF')
    normal_outline = CONFIG.get('FONT_COLOR_OUTLINE', '&H00000000')
    
    # Highlighted word colors
    highlight_color = CONFIG.get('HIGHLIGHT_COLOR_PRIMARY', '&H00FFFFFF')
    highlight_outline = CONFIG.get('HIGHLIGHT_COLOR_OUTLINE', '&H00000000')
    
    parts = []
    for i, word in enumerate(words):
        if i == highlight_index:
            # Highlighted word: use highlight colors and effects
            parts.append(f"{{\\b{bold}\\blur{blur}\\shad{shadow}\\bord{outline_size}\\1c{highlight_color}\\3c{highlight_outline}}}{word.upper()}{{\\r}}")
        else:
            # Normal word: use normal colors
            parts.append(f"{{\\b{bold}\\1c{normal_color}\\3c{normal_outline}}}{word.upper()}")
    return " ".join(parts)
