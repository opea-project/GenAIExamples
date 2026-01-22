# TTS Audio Generation Microservice

Converts podcast scripts into high-quality audio using OpenAI's Text-to-Speech API.

## Features

**OpenAI TTS Integration**
- High-definition audio (tts-1-hd model)
- Multiple voice options (alloy, echo, fable, onyx, nova, shimmer)
- High-quality 24kHz audio output

**Intelligent Audio Processing**
- Concurrent segment generation (up to 5 parallel requests)
- Automatic audio mixing with silence between turns
- MP3 compression (192kbps) for optimal file size
- Metadata tagging (title, artist, album)

**Advanced Voice Management**
- 6 distinct voice personalities
- Host and guest voice selection
- Voice sample generation
- Voice metadata and descriptions

## API Endpoints

### 1. Generate Audio

**POST** `/generate-audio`

Convert script dialogue into podcast audio.

**Request:**
```json
{
  "script": [
    {
      "speaker": "host",
      "text": "Welcome to today's show!"
    },
    {
      "speaker": "guest",
      "text": "Thanks for having me!"
    }
  ],
  "host_voice": "alloy",
  "guest_voice": "shimmer",
  "job_id": "optional-tracking-id"
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "audio_url": "/static/abc123/podcast_abc123.mp3",
  "local_path": "/path/to/file.mp3",
  "metadata": {
    "duration_seconds": 125.5,
    "duration_minutes": 2.09,
    "total_segments": 24,
    "host_voice": "alloy",
    "guest_voice": "shimmer",
    "file_size_mb": 2.4
  },
  "status": "completed"
}
```

### 2. Download Audio

**GET** `/download/{job_id}`

Download generated podcast audio file.

**Response:** MP3 audio file

### 3. Get Available Voices

**GET** `/voices`

List all available TTS voices with descriptions.

**Response:**
```json
{
  "voices": [
    {
      "id": "alloy",
      "name": "Alloy",
      "description": "Neutral and balanced",
      "gender": "neutral"
    },
    {
      "id": "echo",
      "name": "Echo",
      "description": "Deep and resonant",
      "gender": "male"
    }
  ],
  "default_host": "alloy",
  "default_guest": "nova"
}
```

### 4. Generate Voice Sample

**POST** `/voice-sample/{voice_id}`

Generate a sample audio clip for a specific voice.

**Request:**
```json
{
  "text": "Hello! This is a sample of my voice."
}
```

**Response:**
```json
{
  "voice_id": "alloy",
  "sample_path": "/static/samples/sample_alloy.mp3",
  "status": "success"
}
```

### 5. Job Status

**GET** `/status/{job_id}`

Check generation status for a specific job.

**Response:**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "progress": 100,
  "message": "Audio generation complete",
  "audio_url": "/download/abc123"
}
```

### 6. Health Check

**GET** `/health`

Check service health and API availability.

**Response:**
```json
{
  "status": "healthy",
  "openai_available": true,
  "version": "1.0.0"
}
```

## Prerequisites

- OpenAI API key
- FFmpeg (included in Docker)
- Python 3.9+

## Installation

### Using Docker

```bash
cd microservices/tts-service
docker build -t tts-service .
docker run -p 8003:8003 \
  -e OPENAI_API_KEY=your_key \
  tts-service
```

### Manual Installation

Install FFmpeg:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create `.env` file:

```env
# Required
OPENAI_API_KEY=sk-proj-your-key-here

# Optional
TTS_MODEL=tts-1-hd
DEFAULT_HOST_VOICE=alloy
DEFAULT_GUEST_VOICE=nova
AUDIO_QUALITY=192k
SAMPLE_RATE=24000
CONCURRENT_REQUESTS=5
SERVICE_PORT=8003
```

## Usage Examples

### Python

```python
import requests

# Generate audio
response = requests.post(
    "http://localhost:8003/generate-audio",
    json={
        "script": [
            {"speaker": "host", "text": "Welcome!"},
            {"speaker": "guest", "text": "Thanks!"}
        ],
        "host_voice": "onyx",
        "guest_voice": "shimmer"
    }
)

result = response.json()
print(f"Audio generated: {result['audio_url']}")
print(f"Duration: {result['metadata']['duration_minutes']} minutes")
```

### cURL

```bash
# Generate audio
curl -X POST http://localhost:8003/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "script": [
      {"speaker": "host", "text": "Hello!"},
      {"speaker": "guest", "text": "Hi there!"}
    ],
    "host_voice": "alloy",
    "guest_voice": "nova"
  }'

# Download audio
curl http://localhost:8003/download/abc123 -o podcast.mp3

# Get voices
curl http://localhost:8003/voices
```

## Available Voices

| Voice ID | Name | Description | Gender | Best For |
|----------|------|-------------|--------|----------|
| **alloy** | Alloy | Neutral and balanced | Neutral | General purpose |
| **echo** | Echo | Deep and resonant | Male | Professional content |
| **fable** | Fable | Expressive and dynamic | Neutral | Storytelling |
| **onyx** | Onyx | Strong and authoritative | Male | Educational content |
| **nova** | Nova | Warm and friendly | Female | Casual conversations |
| **shimmer** | Shimmer | Bright and energetic | Female | Engaging discussions |

## Testing

Test audio generation:
```bash
curl -X POST http://localhost:8003/generate-audio \
  -H "Content-Type: application/json" \
  -d @test_script.json
```

Test health:
```bash
curl http://localhost:8003/health
```

Test voices:
```bash
curl http://localhost:8003/voices
```

## Troubleshooting

### OpenAI API Errors

**Error**: `AuthenticationError`
- Check `OPENAI_API_KEY` in environment
- Verify API key is active
- Check account has TTS access

**Error**: `RateLimitError`
- Service will retry automatically
- Consider reducing concurrent_requests

### FFmpeg Not Found

**Error**: `FileNotFoundError: ffmpeg`

**Solution**:
```bash
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # macOS
```

### Slow Generation

**Causes**:
- Large number of dialogue turns
- Network latency
- API rate limits

**Solutions**:
- Break into smaller jobs
- Use faster model (tts-1 instead of tts-1-hd)

## API Documentation

View interactive API docs at `http://localhost:8003/docs`
