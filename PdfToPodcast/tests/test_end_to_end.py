"""
End-to-end test of the PDF to Podcast services
"""
import requests
import json
import time

print("=" * 70)
print("PDF to Podcast - End-to-End Test")
print("=" * 70)

# Service URLs
PDF_SERVICE = "http://localhost:8001"
LLM_SERVICE = "http://localhost:8002"
TTS_SERVICE = "http://localhost:8003"

# Test 1: Check service health
print("\n1. Checking service health...")
try:
    pdf_health = requests.get(f"{PDF_SERVICE}/health", timeout=5).json()
    print(f"   [OK] PDF Service: {pdf_health['status']}")
except Exception as e:
    print(f"   [FAILED] PDF Service: {e}")

try:
    llm_health = requests.get(f"{LLM_SERVICE}/health", timeout=5).json()
    print(f"   [OK] LLM Service: {llm_health['status']}")
    print(f"        OpenAI API: {'Available' if llm_health.get('openai_available') else 'Not configured'}")
except Exception as e:
    print(f"   [FAILED] LLM Service: {e}")

try:
    tts_health = requests.get(f"{TTS_SERVICE}/health", timeout=5).json()
    print(f"   [OK] TTS Service: {tts_health['status']}")
except Exception as e:
    print(f"   [FAILED] TTS Service: {e}")

# Test 2: Generate script from sample text
print("\n2. Testing LLM script generation...")
sample_text = """
Artificial Intelligence has revolutionized the way we interact with technology.
Machine learning algorithms can now recognize patterns in data that would be
impossible for humans to detect. Deep learning, a subset of machine learning,
uses neural networks with multiple layers to process information in ways that
mimic the human brain. These technologies are being applied in fields ranging
from healthcare to autonomous vehicles, promising to transform our daily lives.
"""

try:
    response = requests.post(
        f"{LLM_SERVICE}/generate-script",
        json={
            "text": sample_text,
            "host_name": "Alex",
            "guest_name": "Sam",
            "tone": "conversational",
            "max_length": 500,
            "provider": "openai"
        },
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        script = result.get("script", [])
        metadata = result.get("metadata", {})

        print(f"   [OK] Script generated successfully!")
        print(f"        Dialogue turns: {len(script)}")
        print(f"        Total words: {metadata.get('total_words', 0)}")
        print(f"        Estimated duration: {metadata.get('estimated_duration_minutes', 0)} minutes")

        # Show first 2 dialogue turns
        print("\n   Sample dialogue:")
        for i, turn in enumerate(script[:2]):
            speaker = turn.get('speaker', 'Unknown').upper()
            text = turn.get('text', '')[:100]
            print(f"      {speaker}: {text}...")

        # Save script for audio generation test
        with open("test_script.json", "w") as f:
            json.dump(script, f, indent=2)
        print("\n   Script saved to test_script.json")

    else:
        print(f"   [FAILED] Status code: {response.status_code}")
        print(f"        Error: {response.text}")

except Exception as e:
    print(f"   [FAILED] Error: {e}")

# Test 3: List available voices
print("\n3. Testing TTS voice listing...")
try:
    response = requests.get(f"{TTS_SERVICE}/voices", timeout=5)
    if response.status_code == 200:
        voices = response.json()
        print(f"   [OK] Available voices: {len(voices)}")
        for voice_id, info in list(voices.items())[:3]:
            print(f"        - {voice_id}: {info.get('name', 'N/A')}")
    else:
        print(f"   [FAILED] Could not fetch voices")
except Exception as e:
    print(f"   [FAILED] TTS Service not running: {e}")

print("\n" + "=" * 70)
print("Test Complete!")
print("=" * 70)
print("\nNext steps:")
print("1. If script generation worked, the services are functioning!")
print("2. To test audio generation, you would upload the script to TTS service")
print("3. Frontend at http://localhost:3001 can be used for full workflow")
print("\n" + "=" * 70)
