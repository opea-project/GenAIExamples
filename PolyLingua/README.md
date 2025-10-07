# PloyLingua

A production-ready translation service built with **OPEA (Open Platform for Enterprise AI)** components, featuring a modern Next.js UI and microservices architecture.

## 🏗️ Architecture

This service implements a **5-layer microservices architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                       │
│                        (Port 80)                             │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴─────────┐
        │                  │
┌───────▼────────┐  ┌──────▼──────────────────┐
│   Next.js UI   │  │  Translation Megaservice │
│   (Port 5173)  │  │     (Port 8888)          │
└────────────────┘  └──────┬──────────────────┘
                           │
                  ┌────────▼────────────┐
                  │  LLM Microservice   │
                  │    (Port 9000)      │
                  └────────┬────────────┘
                           │
                  ┌────────▼────────────┐
                  │   TGI Model Server  │
                  │    (Port 8008)      │
                  └─────────────────────┘
```

### Components

1. **TGI Service** - HuggingFace Text Generation Inference for model serving
2. **LLM Microservice** - OPEA wrapper providing standardized API
3. **Translation Megaservice** - Orchestrator that formats prompts and routes requests
4. **UI Service** - Next.js 14 frontend with React and TypeScript
5. **Nginx** - Reverse proxy for unified access

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- HuggingFace Account (for model access)
- 8GB+ RAM recommended
- ~10GB disk space for models

### 1. Clone and Setup

```bash
cd PolyLingua

# Configure environment variables
./set_env.sh
```

You'll be prompted for:
- **HuggingFace API Token** - Get from https://huggingface.co/settings/tokens
- **Model ID** - Default: `haoranxu/ALMA-13B` (translation-optimized model)
- **Host IP** - Your server's IP address
- **Ports and proxy settings**

### 2. Build Images

```bash
./deploy/build.sh
```

This builds:
- Translation backend service
- Next.js UI service

### 3. Start Services

```bash
./deploy/start.sh
```

Wait for services to initialize (~2-5 minutes for first run as models download).

### 4. Access the Application

- **Web UI**: http://localhost:80
- **API Endpoint**: http://localhost:8888/v1/translation

### 5. Test the Service

```bash
./deploy/test.sh
```

Or test manually:

```bash
curl -X POST http://localhost:8888/v1/translation \
  -H "Content-Type: application/json" \
  -d '{
    "language_from": "English",
    "language_to": "Spanish",
    "source_language": "Hello, how are you today?"
  }'
```

## 📋 Configuration

### Environment Variables

Key variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_TOKEN` | HuggingFace API token | Required |
| `LLM_MODEL_ID` | Model to use for translation | `haoranxu/ALMA-13B` |
| `MODEL_CACHE` | Directory for model storage | `./data` |
| `host_ip` | Server IP address | `localhost` |
| `NGINX_PORT` | External port for web access | `80` |

See `.env.example` for full configuration options.

### Supported Models

The service works with any HuggingFace text generation model. Recommended models:

- **swiss-ai/Apertus-8B-Instruct-2509** - Multilingual translation (default)
- **haoranxu/ALMA-7B** - Specialized translation model


## 🛠️ Development

### Project Structure

```
opea-translation/
├── translation.py          # Backend translation service
├── requirements.txt        # Python dependencies
├── Dockerfile             # Backend container definition
├── docker-compose.yaml    # Multi-service orchestration
├── set_env.sh            # Environment setup script
├── .env.example          # Environment template
├── ui/                   # Next.js frontend
│   ├── app/             # Next.js app directory
│   ├── components/      # React components
│   ├── Dockerfile       # UI container definition
│   └── package.json     # Node dependencies
└── deploy/              # Deployment scripts
    ├── nginx.conf       # Nginx configuration
    ├── build.sh         # Image build script
    ├── start.sh         # Service startup script
    ├── stop.sh          # Service shutdown script
    └── test.sh          # API testing script
```

### Running Locally (Development)

**Backend:**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export LLM_SERVICE_HOST_IP=localhost
export LLM_SERVICE_PORT=9000
export MEGA_SERVICE_PORT=8888

# Run service
python translation.py
```

**Frontend:**
```bash
cd ui
npm install
npm run dev
```

### API Reference

#### POST /v1/translation

Translate text between languages.

**Request:**
```json
{
  "language_from": "English",
  "language_to": "Spanish",
  "source_language": "Your text to translate"
}
```

**Response:**
```json
{
  "model": "translation",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Translated text here"
    },
    "finish_reason": "stop"
  }],
  "usage": {}
}
```

## 🔧 Operations

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f translation-backend-server
docker compose logs -f translation-ui-server
```

### Stop Services

```bash
./deploy/stop.sh
```

### Update Services

```bash
# Rebuild images
./deploy/build.sh

# Restart services
docker compose down
./deploy/start.sh
```

### Clean Up

```bash
# Stop and remove containers
docker compose down

# Remove volumes (including model cache)
docker compose down -v
```

## 🐛 Troubleshooting

### Service won't start

1. Check if ports are available:
   ```bash
   sudo lsof -i :80,8888,9000,8008,5173
   ```

2. Verify environment variables:
   ```bash
   cat .env
   ```

3. Check service health:
   ```bash
   docker compose ps
   docker compose logs
   ```

### Model download fails

- Ensure `HF_TOKEN` is set correctly
- Check internet connection
- Verify model ID exists on HuggingFace
- Check disk space in `MODEL_CACHE` directory

### Translation errors

- Wait for TGI service to fully initialize (check logs)
- Verify LLM service is healthy: `curl http://localhost:9000/v1/health`
- Check TGI service: `curl http://localhost:8008/health`

### UI can't connect to backend

- Verify `BACKEND_SERVICE_ENDPOINT` in `.env`
- Check if backend is running: `docker compose ps`
- Test API directly: `curl http://localhost:8888/v1/translation`



## 🔗 Resources

- [OPEA Project](https://github.com/opea-project)
- [GenAIComps](https://github.com/opea-project/GenAIComps)
- [GenAIExamples](https://github.com/opea-project/GenAIExamples)
- [HuggingFace Text Generation Inference](https://github.com/huggingface/text-generation-inference)

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review OPEA documentation

---

**Built with OPEA - Open Platform for Enterprise AI** 🚀
