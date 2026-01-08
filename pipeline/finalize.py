
from pipeline.utils import get_video_duration, get_audio_duration, check_gpu_support, console
from config import CONFIG
import subprocess
import json
import re
from datetime import datetime
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
from pilmoji import Pilmoji

def extract_first_sentence(subtitles_path):
    """Extract the first sentence from ASS subtitle file."""
    try:
        with open(subtitles_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the [Events] section
        events_start = content.find('[Events]')
        if events_start == -1:
            return "Check out this amazing video!"
        
        # Get content after [Events]
        events_content = content[events_start:]
        
        # Find all dialogue lines
        dialogue_pattern = r'Dialogue:[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,(.+?)(?:\n|$)'
        matches = re.findall(dialogue_pattern, events_content)
        
        if not matches:
            return "Check out this amazing video!"
        
        # Extract text from the first few subtitles and clean ASS formatting
        text_parts = []
        for match in matches[:15]:  # Get first 15 subtitle lines
            # Remove ASS tags like {\\c&Hxxxxxx&}, {\\blur...}, etc.
            cleaned = re.sub(r'\{[^}]*\}', '', match)
            cleaned = cleaned.strip()
            if cleaned:
                text_parts.append(cleaned)
        
        full_text = ' '.join(text_parts)
        
        # Extract first sentence (ends with . ! or ?)
        sentence_match = re.search(r'^(.+?[.!?])\s', full_text)
        if sentence_match:
            return sentence_match.group(1)
        
        # If no punctuation, return first 50 chars
        if full_text:
            return full_text[:50].rstrip() + '...'
        
        return "Check out this amazing video!"
    except Exception as e:
        console.print(f"[yellow]Warning: Could not extract subtitle text: {e}[/]")
        return "Check out this amazing video!"


def get_font(font_name, size):
    """
    Load fonts. Adjusted to look for Bold/Regular weights.
    """
    try:
        # Update these paths to where your fonts actually live
        base_path = "/run/media/predator/volume/DEV/auto-audio-generator/fonts/static/"
        
        # Mapping generic names to your likely file names
        if font_name == "Bold":
            path = os.path.join(base_path, "Roboto-Bold.ttf")
        elif font_name == "Regular":
            path = os.path.join(base_path, "Roboto-Regular.ttf")
        else:
            path = os.path.join(base_path, f"Roboto-{font_name}.ttf")

        if os.path.exists(path):
            return ImageFont.truetype(path, size)
            
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        print(f"⚠️ Warning: Could not load {font_name} font. Using default.")
        return ImageFont.load_default()

def wrap_text_by_pixel(text, font, max_width, draw):
    """
    Wraps text based on pixel width.
    """
    lines = []
    words = text.split()
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        
        if w > max_width:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)

def draw_verified_badge(draw, x, y, size=25):
    """Draws a simple Twitter/Reddit style verified badge."""
    # Blue scalloped circle (simplified as circle)
    draw.ellipse((x, y, x + size, y + size), fill=(29, 155, 240)) # Twitter/Reddit Blue
    # White checkmark
    # Coordinates for a simple check
    check_points = [
        (x + size * 0.25, y + size * 0.5),
        (x + size * 0.45, y + size * 0.7),
        (x + size * 0.75, y + size * 0.3)
    ]
    draw.line(check_points, fill="white", width=3)

def generate_reddit_post_image(subtitles_path, output_path, custom_title=None, subreddit="AskRedit"):
    # 1. Setup Content
    title_text = custom_title if custom_title else "Provide a title"
    
    # The "Awards" row as seen in your image
    # Note: You can change these emojis to whatever you want
    awards_string = "💀 ❤️ 🤝 ☀️ 💎 🏆 👻"

    # 2. Canvas Setup (1080x1920)
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 3. Visual Configuration (Matches the reference image)
    card_width = 850  # Wider to match the screenshot style
    padding = 50      
    
    # Colors
    color_bg = (255, 255, 255, 255)
    color_text_primary = (0, 0, 0)       # Pitch Black
    color_text_secondary = (101, 119, 134) # Grey for handle/meta
    
    # Fonts
    # Title needs to be heavy and readable
    font_name = get_font("Bold", 38)
    font_handle = get_font("Bold", 32) 
    font_awards = get_font("Regular", 30) # For emoji sizing fallback
    
    # 4. Layout Calculation
    
    # --- Body Text Wrapping ---
    text_max_width = card_width - (padding * 2)
    wrapped_title = wrap_text_by_pixel(title_text, font_name, text_max_width, draw)
    
    # Calculate height of wrapped title
    title_bbox = draw.multiline_textbbox((0, 0), wrapped_title, font=font_name, spacing=15)
    title_pixel_height = title_bbox[3] - title_bbox[1]
    
    # Height breakdown:
    # Padding Top (50) + Header (Avatar/Name/Awards ~120) + Spacing (30) + Title + Spacing (30) + Footer (Socials ~60) + Padding Bottom (50)
    header_height = 130 
    footer_height = 80
    card_height = padding + header_height + title_pixel_height + 40 + footer_height + padding
    
    card_x = (W - card_width) // 2
    card_y = (H - card_height) // 2 # Center in middle of screen

    # 5. Draw Card Background
    # Add a slight drop shadow
    shadow_offset = 10
    draw.rounded_rectangle(
        (card_x + shadow_offset, card_y + shadow_offset, card_x + card_width + shadow_offset, card_y + card_height + shadow_offset),
        radius=30,
        fill=(0, 0, 0, 60)
    )
    draw.rounded_rectangle(
        (card_x, card_y, card_x + card_width, card_y + card_height),
        radius=30,
        fill=color_bg,
    )

    # 6. Initialize Pilmoji (This is the magic part for Emojis)
    # It wraps the image object so when we call pilmoji.text, it renders colored emojis
    with Pilmoji(img) as pilmoji:

        # --- Draw Header ---
        cursor_x = card_x + padding
        cursor_y = card_y + padding
        
        # 1. Avatar (Blue circle with Snoo face or similar)
        avatar_size = 100
        # Draw avatar background
        draw.ellipse((cursor_x, cursor_y, cursor_x + avatar_size, cursor_y + avatar_size), fill=(24, 60, 200)) # Deep Blue
        # Draw a simple face (white circle + smile)
        draw.ellipse((cursor_x + 20, cursor_y + 20, cursor_x + 80, cursor_y + 80), fill="white")
        draw.arc((cursor_x + 35, cursor_y + 45, cursor_x + 65, cursor_y + 65), 0, 180, fill="black", width=3)
        
        # 2. Name and Verified Badge
        text_start_x = cursor_x + avatar_size + 25
        text_start_y = cursor_y + 10
        
        # Draw "Starterstories"
        pilmoji.text((text_start_x, text_start_y), subreddit, font=font_handle, fill=color_text_primary)
        
        # Calculate width of name to place badge next to it
        name_bbox = draw.textbbox((0, 0), subreddit, font=font_handle)
        name_width = name_bbox[2] - name_bbox[0]
        
        # Draw Blue Verified Badge
        draw_verified_badge(draw, text_start_x + name_width + 10, text_start_y + 8, size=28)
        
        # 3. Awards / Emojis Row
        # Located below the name
        awards_y = text_start_y + 45
        pilmoji.text((text_start_x, awards_y), awards_string, font=font_awards, fill=color_text_primary)

        # --- Draw Main Title ---
        title_y = cursor_y + header_height + 20
        pilmoji.text(
            (cursor_x, title_y),
            wrapped_title,
            font=font_name,
            fill=color_text_primary,
            spacing=15
        )

        # --- Draw Footer (Fake counts) ---
        footer_y = title_y + title_pixel_height + 50
        
        # Grey icons/text for 99+ likes/comments
        pilmoji.text((cursor_x, footer_y), "❤️ 99+", font=font_handle, fill=color_text_secondary)
        pilmoji.text((cursor_x + 180, footer_y), "💬 99+", font=font_handle, fill=color_text_secondary)
        pilmoji.text((card_x + card_width - padding - 100, footer_y), "Share", font=font_handle, fill=color_text_secondary)


    # 7. Save
    image_path = output_path.replace(".mp4", "_reddit_post.png")
    if not image_path: image_path = "reddit_post_gen.png"
    
    img.save(image_path)
    print(f"Saved Reddit card to {image_path}")
    return image_path, title_text


def process_video(input_video, voice_audio, subtitles_path, output_path, custom_title=None, overlay_duration=3.0):
    """
    Processes the video with an overlay image.
    Args:
        overlay_duration (float): How long the image stays on screen (in seconds).
    """
    console.print(f"🎬 [green]Processing final video... Image will show for {overlay_duration}s[/]")
    
    # Generate Reddit post image
    reddit_image_path, first_sentence = generate_reddit_post_image(subtitles_path, output_path, custom_title)
    
    use_gpu, video_encoder, video_decoder = check_gpu_support()
    voice_duration = get_audio_duration(voice_audio)
    start_time = 0
    segment_duration = voice_duration
    
    escaped_subtitles = subtitles_path.replace(":", "\\:").replace(",", "\\,")
    input_params = []
    if use_gpu and video_decoder:
        input_params.extend(["-hwaccel", "cuda", "-c:v", video_decoder])
    input_params.extend(["-ss", str(start_time), "-t", str(segment_duration)])

    # Filter complex with DYNAMIC duration
    # We use the overlay_duration variable here in the 'enable' clause
    filter_complex = (
        f"[0:v]crop=in_h*9/16:in_h,scale=1080:1920,setpts=PTS/1.3[v];"
        f"[v]ass={escaped_subtitles}[vv];"
        f"[1:v]scale=1080:1920[img];"
        f"[vv][img]overlay=0:0:enable='lt(t,{overlay_duration})'[out]"
    )
    
    cmd = ["ffmpeg", "-y",
        "-i", input_video,
        "-loop", "1", "-t", str(segment_duration), "-i", reddit_image_path,
        "-i", voice_audio,
        "-filter_complex", filter_complex,
        "-map", "[out]", "-map", "2:a",
        "-c:v", video_encoder, "-c:a", "aac",
        "-filter:a", "atempo=1.3",
        "-preset", "fast", "-crf", "23",
        "-shortest", output_path
    ]

    subprocess.run(cmd, check=True)
    console.print(f"✅ [green]Final video saved to:[/] {output_path}")
    
    return output_path
