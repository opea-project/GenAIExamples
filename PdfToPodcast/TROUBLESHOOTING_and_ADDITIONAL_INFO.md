# Troubleshooting Guide

This guide provides solutions to common issues you may encounter while using the PDF to Podcast Generator.

## Services Not Starting

**Check container status:**
```bash
docker compose ps
```

**View error logs:**
```bash
docker compose logs backend
```

**Common issues:**

1. **Port conflicts** - Ports 3000, 8000-8003 already in use
   ```bash
   # Windows
   netstat -ano | findstr "3000 8000 8001 8002 8003"

   # Linux/Mac
   lsof -i :3000
   ```

2. **Missing API key** - Verify `.env` file contains valid OpenAI key

3. **Insufficient memory** - Docker Desktop needs at least 4GB RAM

4. **Docker not running** - Start Docker Desktop and wait for initialization

## PDF Upload Fails

**Possible causes:**
- File exceeds 10MB limit
- PDF is encrypted or password-protected
- PDF contains only images without text
- File is corrupted

**Solutions:**
```bash
# Check PDF service logs
docker compose logs pdf-service

# Verify file size
ls -lh your-file.pdf
```

## Script Generation Fails

**Check OpenAI API status:**
```bash
# Test API key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-your-key-here"
```

**Common issues:**
- Invalid or expired API key
- Insufficient API credits or quota exceeded
- Rate limit reached
- Network connectivity problems
- PDF text extraction failed

**Check LLM service logs:**
```bash
docker compose logs llm-service
```

## Audio Generation Fails

**Verify TTS service:**
```bash
# Check if service is running
docker compose ps tts-service

# View TTS logs
docker compose logs tts-service
```

**Common issues:**
- OpenAI TTS API rate limits
- Insufficient API credits
- Network timeout during audio synthesis
- Audio mixing errors
- FFmpeg not available in container (should be installed via Dockerfile)

## Audio Not Playing

**Browser console errors:**
- Open browser DevTools (F12)
- Check Console tab for errors
- Verify audio URL is accessible
- Check CORS headers

**Verify backend connectivity:**
```bash
curl http://localhost:8000/health
```

## Frontend Not Loading

**Check frontend service:**
```bash
# View frontend logs
docker compose logs frontend

# Verify backend is accessible
curl http://localhost:8000
```

**Common issues:**
- Backend service not ready
- CORS configuration incorrect
- Port 3000 already in use
- Build errors in frontend code

## Service Management

**View all service logs:**
```bash
docker compose logs -f
```

**Restart specific service:**
```bash
docker compose restart backend
docker compose restart frontend
```

**Restart all services:**
```bash
docker compose restart
```

**Stop all services:**
```bash
docker compose down
```

**Rebuild and restart:**
```bash
docker compose up -d --build
```

## Clean Up and Restart

**Complete reset:**
```bash
# Stop all containers
docker compose down

# Remove volumes
docker volume prune

# Remove images
docker compose down --rmi all

# Fresh start
docker compose up -d --build
```

## Performance Metrics

| Operation | Typical Duration | Notes |
|-----------|------------------|-------|
| PDF Upload | 1-3 seconds | Depends on file size |
| Text Extraction | 2-5 seconds | For standard PDFs |
| Script Generation | 15-25 seconds | Using GPT-4 |
| Audio Generation | 20-40 seconds | For 2-minute podcast |
| Total Workflow | 40-70 seconds | From PDF to audio |

## Audio Specifications

- Format: MP3
- Bitrate: 192 kbps
- Sample Rate: 24 kHz
- File Size: Approximately 2-3 MB per minute
- Quality: High-quality conversational audio

## Getting Additional Help

For issues not covered in this guide:
1. Review service logs with `docker compose logs`
2. Verify OpenAI API key and available credits
3. Check Docker container status with `docker compose ps`
4. Monitor API usage at https://platform.openai.com/usage
5. Review OpenAI TTS Documentation: https://platform.openai.com/docs/guides/text-to-speech
6. Check OpenAI API Reference: https://platform.openai.com/docs/api-reference
