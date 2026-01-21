# Troubleshooting Guide

## Common Issues

### 1. Containers Not Starting

**Symptom**: Containers fail to start or exit immediately

**Check container status:**
```bash
docker compose ps
```

**View error logs:**
```bash
docker compose logs backend
docker compose logs frontend
```

**Solution:**
```bash
# Rebuild containers
docker compose down
docker compose up -d --build
```

### 2. Backend Connection Errors

**Symptom**: Frontend shows "Failed to connect" or network errors

**Check backend health:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status":"healthy","service":"Document Summarization Service","version":"2.0.0","llm_provider":"Enterprise Inference (Keycloak)"}
```

**Solution:**
- Verify backend container is running: `docker compose ps`
- Check backend logs: `docker compose logs backend -f`
- Restart backend: `docker compose restart backend`

### 3. Keycloak Authentication Errors

**Symptom**: Text/PDF summarization fails with authentication errors

**Error**: `Authentication error` or `Failed to resolve 'api.example.com'`

**Solution:**
- Check Keycloak credentials in `backend/.env`:
  - `BASE_URL` (enterprise inference endpoint)
  - `KEYCLOAK_REALM`
  - `KEYCLOAK_CLIENT_ID`
  - `KEYCLOAK_CLIENT_SECRET`
- Verify enterprise inference endpoint is accessible
- Test authentication:
```bash
curl -X POST https://your-api.example.com/token \
  -d "grant_type=client_credentials" \
  -d "client_id=your-client-id" \
  -d "client_secret=your-client-secret"
```

**Error**: `Connection timeout`

**Solution:**
- Verify `BASE_URL` is correct in `backend/.env`
- Check network connectivity to enterprise endpoint
- Verify firewall settings allow HTTPS connections

### 4. PDF Processing Errors

**Symptom**: PDF upload fails or returns empty text

**Error**: `Failed to extract text from PDF`

**Causes:**
- Scanned PDF without text layer (image-only PDF)
- Password-protected PDF
- Corrupted PDF file
- PDF with complex formatting

**Solution:**
- For scanned PDFs, ensure OCR was run during scanning
- Remove password protection before uploading
- Try re-saving PDF with Adobe Reader or similar tool
- Check backend logs for specific error details
- Maximum PDF size: 50MB

### 5. Frontend Not Loading

**Symptom**: Browser shows blank page or cannot connect to localhost:5173

**Check frontend status:**
```bash
docker compose ps frontend
```

**Check frontend logs:**
```bash
docker compose logs frontend -f
```

**Solution:**
- Clear browser cache and hard refresh (Ctrl+F5)
- Verify port 5173 is not in use: `netstat -ano | findstr :5173` (Windows)
- Kill conflicting process if port is occupied
- Restart frontend: `docker compose restart frontend`
- Check firewall settings allow localhost:5173

### 6. Port Already in Use

**Error**: `Port 5173 is already allocated` or `Port 8000 is already allocated`

**Find process using port:**
```bash
# Windows
netstat -ano | findstr :5173
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :5173
lsof -i :8000
```

**Solution:**
- Stop the conflicting process
- Or change ports in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # Change 8000 to 8001
    - "5174:80"    # Change 5173 to 5174
  ```

### 7. Out of Memory Errors

**Symptom**: Container crashes or backend becomes unresponsive

**Check logs:**
```bash
docker compose logs backend | grep -i "memory\|killed"
```

**Solution:**
- Reduce file sizes (use smaller PDFs)
- Reduce `max_tokens` in LLM requests
- Increase Docker memory limit in Docker Desktop settings (minimum 4GB recommended)
- Process one file at a time instead of multiple concurrent requests

### 8. Backend Service Unavailable

**Symptom**: 502 Bad Gateway or 503 Service Unavailable

**Check backend:**
```bash
docker compose logs backend --tail=50
```

**Common causes:**
- Backend still starting (wait 30-60 seconds after start)
- Configuration error in `.env` file
- Enterprise inference endpoint unreachable
- Keycloak authentication failing
- Python dependency issues

**Solution:**
```bash
# Restart backend
docker compose restart backend

# If issues persist, rebuild
docker compose down
docker compose up -d --build backend
```

## Configuration Issues

### Invalid .env Configuration

**Symptom**: Backend fails to start with configuration errors

**Check required variables in `backend/.env`:**

**For text/PDF/DOCX summarization:**
```bash
BASE_URL=https://api.example.com
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=api
KEYCLOAK_CLIENT_SECRET=your_client_secret
INFERENCE_MODEL_ENDPOINT=Llama-3.1-8B-Instruct
INFERENCE_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
```

**Common mistakes:**
- Missing required Keycloak variables
- Extra spaces in variable names
- Wrong endpoint format (missing https://)
- Quotes around values (not needed in .env files)
- Using placeholder values like "api.example.com" or "your_client_secret"

### File Size Limits

**Maximum file sizes:**
- PDF/DOCX documents: 50 MB

**Configured in `backend/config.py`:**
```python
MAX_PDF_SIZE = 52428800  # 50MB in bytes
```

## Advanced Troubleshooting

### Enable Debug Logging

Edit `backend/.env`:
```bash
LOG_LEVEL=DEBUG
```

Restart backend:
```bash
docker compose restart backend
docker compose logs backend -f
```

### Test Backend Directly

**Test text summarization:**
```bash
curl -X POST http://localhost:8000/v1/docsum \
  -F "type=text" \
  -F "messages=This is a test document about artificial intelligence and machine learning." \
  -F "max_tokens=100" \
  -F "stream=false"
```

**Test PDF summarization:**
```bash
curl -X POST http://localhost:8000/v1/docsum \
  -F "type=text" \
  -F "files=@test.pdf" \
  -F "max_tokens=100" \
  -F "stream=false"
```


### Inspect Container

**Access backend container shell:**
```bash
docker compose exec backend /bin/bash
```

**Check Python environment:**
```bash
docker compose exec backend pip list
docker compose exec backend python -c "import pypdf; print('pypdf installed')"
```

**Verify environment variables:**
```bash
docker compose exec backend env | grep -E "BASE_URL|KEYCLOAK"
```

### Clean Docker Environment

If issues persist, clean Docker completely:

```bash
# Stop and remove containers
docker compose down -v

# Remove unused images
docker system prune -a

# Rebuild from scratch
docker compose up -d --build
```

## Architecture-Specific Issues

### Enterprise Inference Connection

**Symptom**: All summarization fails (text, PDF)

**Required for**: ALL summarization operations

**Check configuration:**
1. Verify `BASE_URL` points to your enterprise inference endpoint
2. Confirm Keycloak credentials are correct
3. Test Keycloak authentication separately
4. Verify network access to enterprise endpoint
5. Check if model name matches available models

## Getting Help

If issues persist after following this guide:

1. **Collect Information:**
   - Docker logs: `docker compose logs > logs.txt`
   - Docker status: `docker compose ps`
   - Environment check: `docker compose config`

2. **Check Configuration:**
   - Review `backend/.env` file (remove sensitive data before sharing)
   - Verify Keycloak credentials with your admin

3. **Try Minimal Setup:**
   - Start with text summarization (simple, no files)
   - Then test PDF processing
   - This helps isolate which component is failing

4. **System Information:**
   - Docker version: `docker --version`
   - Docker Compose version: `docker compose version`
   - Operating system and version
   - Available memory and disk space
