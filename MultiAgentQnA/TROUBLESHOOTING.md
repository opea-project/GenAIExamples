# Troubleshooting Guide

This document addresses common issues you may encounter when running the Multi-Agent Q&A application.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [API Issues](#api-issues)
3. [UI Issues](#ui-issues)
4. [Agent Issues](#agent-issues)
5. [Docker Issues](#docker-issues)

---

## Environment Setup

### Issue: Missing environment variables

**Symptoms:**
- API fails to start
- Authentication errors
- "Configuration error" messages

**Solution:**
1. Ensure you have created `api/.env` file based on `api/env.example`
2. Verify all required variables are set:
   ```bash
   BASE_URL=https://your-api-url.com
   KEYCLOAK_CLIENT_ID=your_client_id
   KEYCLOAK_CLIENT_SECRET=your_client_secret
   ```
3. Check that the `.env` file is in the `api/` directory

### Issue: Python dependencies not installing

**Symptoms:**
- Import errors
- "Module not found" errors

**Solution:**
```bash
cd api
pip install -r requirements.txt
```

---

## API Issues

### Issue: Authentication fails

**Symptoms:**
- "Authentication failed" errors
- 401 Unauthorized responses

**Solution:**
1. Verify your `KEYCLOAK_CLIENT_SECRET` is correct
2. Check that `BASE_URL` points to the correct endpoint
3. Ensure network connectivity to the enterprise-inference API
4. Verify SSL certificate issues by checking if `verify=False` is needed in api_client.py

### Issue: API returns empty responses

**Symptoms:**
- No content in chat responses
- "Unexpected response structure" errors

**Solution:**
1. Check the model endpoints in `.env`:
   ```bash
   EMBEDDING_MODEL_ENDPOINT=bge-base-en-v1.5
   INFERENCE_MODEL_ENDPOINT=Llama-3.1-8B-Instruct
   ```
2. Verify the inference API is returning valid responses
3. Check API logs for detailed error messages

### Issue: API is slow to respond

**Symptoms:**
- Long wait times for responses
- Timeout errors

**Solution:**
1. Reduce `max_tokens` in agent configurations
2. Set `max_iter` to a lower value (e.g., 5-10 instead of 15)
3. Check network latency to enterprise-inference API

---

## UI Issues

### Issue: Cannot connect to API

**Symptoms:**
- "Failed to get response" errors
- Network errors in browser console

**Solution:**
1. Verify backend is running on port 5001:
   ```bash
   curl http://localhost:5001/health
   ```
2. Check Vite proxy configuration in `ui/vite.config.js`
3. Ensure CORS is properly configured in `api/server.py`

### Issue: Page doesn't load

**Symptoms:**
- Blank page
- JavaScript errors in console

**Solution:**
1. Install dependencies:
   ```bash
   cd ui
   npm install
   ```
2. Clear browser cache and reload
3. Check for console errors in browser DevTools

---

## Agent Issues

### Issue: Wrong agent is selected

**Symptoms:**
- Code questions routed to general agent
- RAG questions not using retrieval

**Solution:**
1. The routing is based on keyword detection in `agents.py`
2. Review `determine_agent_type()` function
3. Add custom keywords to improve routing accuracy

### Issue: Agent configuration not saved

**Symptoms:**
- Settings revert after saving
- Default configuration persists

**Solution:**
1. Check browser console for API errors
2. Verify `/config` POST endpoint is working:
   ```bash
   curl -X POST http://localhost:5001/config \
     -H "Content-Type: application/json" \
     -d '{"orchestration": {"role": "Test"}}'
   ```

---

## Docker Issues

### Issue: Containers won't start

**Symptoms:**
- `docker-compose up` fails
- Port already in use errors

**Solution:**
1. Stop existing containers:
   ```bash
   docker-compose down
   ```
2. Check for port conflicts:
   ```bash
   # Check if ports are in use
   lsof -i :5001  # API
   lsof -i :3000  # UI
   ```
3. Rebuild containers:
   ```bash
   docker-compose up --build
   ```

### Issue: Environment variables not loading

**Symptoms:**
- Configuration defaults being used
- Authentication errors in containers

**Solution:**
1. Ensure `.env` file exists in `api/` directory
2. Check docker-compose.yml references the env_file correctly:
   ```yaml
   env_file:
     - ./api/.env
   ```
3. Restart containers after creating `.env`:
   ```bash
   docker-compose restart backend
   ```

### Issue: Volume mounting not working

**Symptoms:**
- Code changes not reflecting in containers
- Hot reload not working

**Solution:**
1. Verify volume mounts in docker-compose.yml:
   ```yaml
   volumes:
     - ./api:/app
   ```
2. Check file permissions
3. Restart containers after configuration changes

---

## General Debugging Tips

### Check Logs

**Backend:**
```bash
# Docker
docker logs multiagent-qna-backend

# Local
tail -f api/logs/app.log
```

**Frontend:**
```bash
# Docker
docker logs multiagent-qna-frontend

# Local - check browser DevTools console
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:5001/health

# Configuration
curl http://localhost:5001/config

# Chat
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

### Common Python Debugging

```python
# Add verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check agent configuration
from services.agents import get_code_agent
agent = get_code_agent()
print(agent.role, agent.goal)
```

---

## Performance Optimization

1. **Reduce Token Usage:**
   - Lower `max_tokens` in API calls
   - Reduce `max_iter` for agents
   - Use caching where possible

2. **Optimize Agent Routing:**
   - Fine-tune keyword detection
   - Consider using more sophisticated classification

3. **Batch Processing:**
   - Process multiple queries in parallel
   - Use connection pooling for API calls

---

## Still Having Issues?

1. Check the [README.md](README.md) for setup instructions
2. Review error logs in detail
3. Verify all prerequisites are met
4. Ensure network connectivity to enterprise-inference API
5. Test API endpoints independently

For additional help, please check the project documentation or contact support.

