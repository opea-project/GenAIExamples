"""
Generate OpenAI TTS voice sample audio files for voice preview
"""
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from LLM service
load_dotenv("microservices/llm-service/.env")

# Get API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Voice configurations
voices = {
    "alloy": {"name": "Alloy", "description": "Neutral and balanced"},
    "echo": {"name": "Echo", "description": "Clear and expressive"},
    "fable": {"name": "Fable", "description": "Warm and engaging"},
    "onyx": {"name": "Onyx", "description": "Deep and authoritative"},
    "nova": {"name": "Nova", "description": "Friendly and conversational"},
    "shimmer": {"name": "Shimmer", "description": "Bright and energetic"},
}

# Create output directory
output_dir = Path("frontend/public/voice-samples")
output_dir.mkdir(parents=True, exist_ok=True)

print("Generating OpenAI TTS voice samples...\n")

for voice_id, voice_info in voices.items():
    print(f"Generating sample for {voice_info['name']}...")

    # Create speech sample
    text = f"Hello, I'm {voice_info['name']}. {voice_info['description']}. I'll be your podcast voice."

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice_id,
            input=text,
            speed=1.0
        )

        # Save audio file
        output_path = output_dir / f"{voice_id}.mp3"
        response.stream_to_file(str(output_path))

        print(f"Generated: {output_path}")

    except Exception as e:
        print(f"Error generating {voice_id}: {e}")

print(f"\nVoice samples generated successfully in {output_dir}")
print("\nNext steps:")
print("1. Update simple_backend.py to serve these audio files")
print("2. Modify VoiceSelector.jsx to play the audio files")
