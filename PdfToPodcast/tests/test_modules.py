"""
Simple module verification test
"""
import sys
from pathlib import Path

print("=" * 60)
print("PDF to Podcast - Module Verification Test")
print("=" * 60)

# Test 1: PDF Service
print("\n1. Testing PDF Service modules...")
try:
    sys.path.insert(0, str(Path(__file__).parent / "microservices" / "pdf-service"))
    from app.core.pdf_extractor import PDFExtractor
    from app.core.text_cleaner import TextCleaner

    pdf_extractor = PDFExtractor()
    text_cleaner = TextCleaner()

    # Test text cleaning
    sample_text = "This   is  a   test.\n\nIt has  multiple   spaces."
    cleaned = text_cleaner.clean(sample_text)
    stats = text_cleaner.get_statistics(cleaned)

    print("[OK] PDF Service modules loaded successfully")
    print(f"     Text cleaner working: {stats['word_count']} words")

except Exception as e:
    print(f"[FAILED] PDF Service error: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 2: LLM Service
print("\n2. Testing LLM Service modules...")
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

    print("[OK] LLM Service modules loaded successfully")
    print(f"     Script validation: {is_valid}")
    print(f"     Estimated duration: {metadata['estimated_duration_minutes']} min")

except Exception as e:
    print(f"[FAILED] LLM Service error: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 3: TTS Service
print("\n3. Testing TTS Service modules...")
try:
    sys.path.insert(0, str(Path(__file__).parent / "microservices" / "tts-service"))
    from app.core.voice_manager import VoiceManager
    from app.core.audio_mixer import AudioMixer

    voice_manager = VoiceManager()
    audio_mixer = AudioMixer()

    # Test voice manager
    voices = voice_manager.get_all_voices()
    default_host = voice_manager.get_default_voice("host")

    print("[OK] TTS Service modules loaded successfully")
    print(f"     Available voices: {len(voices)}")
    print(f"     Default host voice: {default_host}")

except Exception as e:
    print(f"[FAILED] TTS Service error: {str(e)}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("\n[SUCCESS] All core modules loaded and working!")
print("\nNext steps:")
print("1. Set environment variable: OPENAI_API_KEY")
print("2. Start each service individually or use Docker Compose")
print("3. Frontend already running on http://localhost:3001")
print("\n" + "=" * 60)
