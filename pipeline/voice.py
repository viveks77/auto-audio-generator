from elevenlabs.client import ElevenLabs
from elevenlabs import save
from pipeline.utils import console
from config import CONFIG


def generate_voice(text, output_path):
    elevenlabs = ElevenLabs(api_key=CONFIG["ELEVEN_API_KEY"])
    console.print("🔊 [bold yellow]Generating voice with ElevenLabs SDK...[/]")
    audio = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id=CONFIG["VOICE_ID"],
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    save(audio, output_path)
    console.print(f"✅ [green]Voice-over saved to:[/] {output_path}")
    return output_path
