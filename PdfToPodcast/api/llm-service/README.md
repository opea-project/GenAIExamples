# LLM Script Generation Microservice

Converts PDF text into engaging podcast dialogue using enterprise inference endpoints.

## Features

**Inference API Integration**
- Supports custom inference models
- Automatic retry with exponential backoff
- Token-based authentication

**Intelligent Dialogue Generation**
- Natural, conversational podcast scripts
- Host and guest roles
- Questions, reactions, and transitions
- Context-aware explanations

**Multiple Conversation Tones**
- Conversational (friendly, accessible)
- Educational (structured, informative)
- Professional (polished, authoritative)

**Script Formatting & Validation**
- JSON output parsing
- Format validation
- TTS preparation
- Metadata calculation

## API Endpoints

### 1. Generate Script

**POST** `/generate-script`

Convert text content into podcast dialogue.

**Request:**
```json
{
  "text": "PDF content here...",
  "host_name": "Alex",
  "guest_name": "Sam",
  "tone": "conversational",
  "max_length": 2000,
  "provider": "inference",
  "job_id": "optional-tracking-id"
}
```

**Response:**
```json
{
  "script": [
    {
      "speaker": "host",
      "text": "Welcome to today's show! We're exploring..."
    },
    {
      "speaker": "guest",
      "text": "Thanks for having me! This topic is fascinating because..."
    }
  ],
  "metadata": {
    "total_turns": 24,
    "host_turns": 12,
    "guest_turns": 12,
    "total_words": 1850,
    "estimated_duration_minutes": 12.3,
    "tone": "conversational"
  },
  "status": "success"
}
```

### 2. Refine Script

**POST** `/refine-script`

Improve an existing script.

**Request:**
```json
{
  "script": [
    {"speaker": "host", "text": "..."},
    {"speaker": "guest", "text": "..."}
  ],
  "provider": "inference"
}
```

### 3. Validate Content

**POST** `/validate-content`

Check if content is suitable for podcast generation.

**Response:**
```json
{
  "valid": true,
  "word_count": 1500,
  "char_count": 9000,
  "token_count": 2250,
  "issues": [],
  "recommendations": ["Consider using 'educational' tone for technical content"]
}
```

### 4. Health Check

**GET** `/health`

Check service health and provider availability.

**Response:**
```json
{
  "status": "healthy",
  "llm_available": true,
  "llm_provider": "Inference API",
  "version": "1.0.0"
}
```

### 5. Get Tones

**GET** `/tones`

List available conversation tones.

### 6. Get Models

**GET** `/models`

List available LLM models.

## Prerequisites

- Enterprise inference endpoint with token
- Python 3.9+

## Installation

### Using Docker

```bash
cd microservices/llm-service
docker build -t llm-service .
docker run -p 8002:8002 \
  -e INFERENCE_API_ENDPOINT=your_endpoint \
  -e INFERENCE_API_TOKEN=your_token \
  -e INFERENCE_MODEL_NAME=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
  llm-service
```

### Manual Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create `.env` file:

```env
# Required
INFERENCE_API_ENDPOINT=https://your-endpoint.com/deployment
INFERENCE_API_TOKEN=your-bearer-token-here
INFERENCE_MODEL_NAME=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B

# Optional
DEFAULT_TONE=conversational
DEFAULT_MAX_LENGTH=2000
TEMPERATURE=0.7
MAX_TOKENS=4000
SERVICE_PORT=8002
```

## Usage Examples

### Python

```python
import requests

response = requests.post(
    "http://localhost:8002/generate-script",
    json={
        "text": "Your PDF content here...",
        "host_name": "Alex",
        "guest_name": "Jordan",
        "tone": "conversational",
        "max_length": 2000
    }
)

result = response.json()
print(f"Generated {len(result['script'])} dialogue turns")
```

### cURL

```bash
curl -X POST http://localhost:8002/generate-script \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Content to convert...",
    "tone": "educational",
    "max_length": 1500
  }'
```

## Testing

Test script generation:
```bash
curl -X POST http://localhost:8002/generate-script \
  -H "Content-Type: application/json" \
  -d '{"text": "Test content", "tone": "conversational"}'
```

Test health:
```bash
curl http://localhost:8002/health
```

## Troubleshooting

### Inference API Errors

**Error**: `AuthenticationError` / `ValueError`
- Check `INFERENCE_API_ENDPOINT` and `INFERENCE_API_TOKEN` in environment
- Verify token is valid and not expired
- Confirm endpoint URL is correct

**Error**: Connection errors
- Verify network connectivity to inference endpoint
- Check firewall rules

### Slow Response Times

**Causes**:
- Large content (> 5000 words)
- Model processing time

**Solutions**:
- Break content into sections
- Reduce max_length
- Check network latency

## API Documentation

View interactive API docs at `http://localhost:8002/docs`
