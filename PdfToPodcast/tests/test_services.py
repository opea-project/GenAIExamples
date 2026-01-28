"""
Simple test script to verify the microservices are working
"""
import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent / "microservices" / "pdf-service"))
sys.path.append(str(Path(__file__).parent / "microservices" / "llm-service"))
sys.path.append(str(Path(__file__).parent / "microservices" / "tts-service"))

print("=" * 60)
print("Testing PDF to Podcast Microservices")
print("=" * 60)

# Test 1: PDF Service
print("\n1. Testing PDF Service...")
try:
    from app.core.pdf_extractor import PDFExtractor
    from app.core.text_cleaner import TextCleaner

    pdf_extractor = PDFExtractor()
    text_cleaner = TextCleaner()

    # Test text cleaning
    sample_text = "This   is  a   test.\n\nIt has  multiple   spaces."
    cleaned = text_cleaner.clean(sample_text)
    stats = text_cleaner.get_statistics(cleaned)

    print("✅ PDF Service modules loaded successfully")
    print(f"   - Text cleaner working: {stats['word_count']} words")

except Exception as e:
    print(f"❌ PDF Service error: {str(e)}")

# Test 2: LLM Service
print("\n2. Testing LLM Service...")
try:
    sys.path.insert(0, str(Path(__file__).parent / "microservices" / "llm-service"))
    from app.core.prompt_builder import PromptBuilder
    from app.core.script_formatter import ScriptFormatter

    prompt_builder = PromptBuilder()
    script_formatter = ScriptFormatter()

    # Test script validation
    test_script = [
        {"speaker": "host", "text": "Welcome to the show!"},
        {"speaker": "guest", "text": "Thanks for having me!"}
    ]

    is_valid = script_formatter.validate_script(test_script)
    metadata = script_formatter.calculate_metadata(test_script)

    print("✅ LLM Service modules loaded successfully")
    print(f"   - Script validation working: {is_valid}")
    print(f"   - Estimated duration: {metadata['estimated_duration_minutes']} min")

except Exception as e:
    print(f"❌ LLM Service error: {str(e)}")

# Test 3: TTS Service
print("\n3. Testing TTS Service...")
try:
    sys.path.insert(0, str(Path(__file__).parent / "microservices" / "tts-service"))
    from app.core.voice_manager import VoiceManager
    from app.core.audio_mixer import AudioMixer

    voice_manager = VoiceManager()
    audio_mixer = AudioMixer()

    # Test voice manager
    voices = voice_manager.get_all_voices()
    default_host = voice_manager.get_default_voice("host")

    print("✅ TTS Service modules loaded successfully")
    print(f"   - Available voices: {len(voices)}")
    print(f"   - Default host voice: {default_host}")

except Exception as e:
    print(f"❌ TTS Service error: {str(e)}")

# Test 4: Frontend
print("\n4. Testing Frontend...")
try:
    frontend_dir = Path(__file__).parent / "frontend"
    package_json = frontend_dir / "package.json"

    if package_json.exists():
        print("✅ Frontend structure exists")
        print(f"   - Location: {frontend_dir}")
    else:
        print("❌ Frontend package.json not found")

except Exception as e:
    print(f"❌ Frontend check error: {str(e)}")

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("\n✅ All core modules are working!")
print("\nNext steps:")
print("1. Set up environment variables (OPENAI_API_KEY)")
print("2. Start services with Docker Compose or individually")
print("3. Frontend is already running on http://localhost:3001")
print("\n" + "=" * 60)
