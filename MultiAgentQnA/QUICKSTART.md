# Quick Start Guide

Get up and running with the Multi-Agent Q&A application in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- Valid enterprise-inference API credentials

## Step-by-Step Setup

### 1. Configure Environment Variables

Create the API environment file:

```bash
cd multiagent-qna
cp api/env.example api/.env
```

Edit `api/.env` with your credentials:

```env
BASE_URL=https://your-enterprise-inference-url.com
KEYCLOAK_CLIENT_ID=your_client_id
KEYCLOAK_CLIENT_SECRET=your_client_secret
EMBEDDING_MODEL_ENDPOINT=bge-base-en-v1.5
INFERENCE_MODEL_ENDPOINT=Llama-3.1-8B-Instruct
EMBEDDING_MODEL_NAME=bge-base-en-v1.5
INFERENCE_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
```

### 2. Start with Docker Compose

```bash
cd multiagent-qna
docker-compose up --build
```

Wait for both services to start:
- Backend API on http://localhost:5001
- Frontend UI on http://localhost:3000

### 3. Access the Application

Open your browser and navigate to:

```
http://localhost:3000
```

You should see the Multi-Agent Q&A interface!

## Alternative: Local Development

### Backend

```bash
cd multiagent-qna/api

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn server:app --reload --host 0.0.0.0 --port 5001
```

### Frontend

```bash
cd multiagent-qna/ui

# Install dependencies
npm install

# Run development server
npm run dev
```

## Testing the Application

### Test the Chat Interface

1. Navigate to the Chat page
2. Type a question, for example:
   - **Code**: "How do I create a Python function?"
   - **RAG**: "Find information about machine learning"
   - **General**: "What is the weather like?"

3. The system will automatically route your question to the appropriate agent

### Test the Settings

1. Click on "Settings" in the header
2. Modify agent configurations:
   - Change roles, goals, or backstories
   - Adjust max iterations
   - Toggle verbose mode
3. Click "Save Configuration"
4. Test with new questions

## Verify Everything Works

### Check API Health

```bash
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "healthy",
  "api_configured": true
}
```

### Test Chat Endpoint

```bash
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

Expected response:
```json
{
  "response": "Response from agent...",
  "agent": "normal_agent"
}
```

## Common First-Time Issues

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find and kill process on port 5001
lsof -ti:5001 | xargs kill -9

# Find and kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or change ports in docker-compose.yml
```

### Cannot Connect to Enterprise API

**Error**: `Authentication failed`

**Solution**:
1. Double-check your `.env` credentials
2. Verify BASE_URL is correct
3. Ensure network access to enterprise-inference API

### UI Shows "Failed to get response"

**Solution**:
1. Check backend logs: `docker logs multiagent-qna-backend`
2. Verify API is running: `curl http://localhost:5001/health`
3. Check browser console for errors

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more help
- Customize agent configurations in the Settings page
- Integrate with your own knowledge bases or APIs

## Architecture Overview

```
User Query
    ↓
Orchestration Agent (routes to appropriate specialist)
    ↓
┌─────────────────────────────────────────┐
│                                         │
├─ Code Agent ─── For programming Q&A     │
├─ RAG Agent ──── For document retrieval  │
└─ Normal Agent ── For general questions  │
```

The system automatically detects query type and routes to the best agent!

## Need Help?

- Check logs: `docker logs multiagent-qna-backend`
- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Verify environment variables are set correctly

Happy chatting! 🚀

