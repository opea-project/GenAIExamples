# Troubleshooting Guide

This document contains all common issues encountered during development and their solutions.

## Table of Contents

- [Docker Compose Issues](#docker-compose-issues)
- [API Common Issues](#api-common-issues)
- [UI Common Issues](#ui-common-issues)

## Docker Compose Issues

### Error: "LOCAL_URL_ENDPOINT variable is not set"

**Problem**:
```
level=warning msg="The \"LOCAL_URL_ENDPOINT\" variable is not set. Defaulting to a blank string."
decoding failed due to the following error(s):
'services[backend].extra_hosts' bad host name ''
```

**Solution**:

1. Create a `.env` file in the **root** `rag-chatbot` directory (not in `api/`):
   ```bash
   echo "LOCAL_URL_ENDPOINT=not-needed" > .env
   ```
2. If using a local domain (e.g., `inference.example.com`), replace `not-needed` with your domain name (without `https://`)
3. Restart Docker Compose: `docker compose down && docker compose up`

### Error: "404 Not Found" when uploading PDF

**Problem**:
```
HTTP Request: POST https://api.example.com/BAAI/bge-base-en-v1.5/v1/embeddings "HTTP/1.1 404 Not Found"
openai.NotFoundError: Error code: 404 - {'detail': 'Not Found'}
```

**Solution**:

1. Verify your `api/.env` file has the **correct** API endpoint (not the placeholder):
   ```bash
   INFERENCE_API_ENDPOINT=https://your-actual-api-endpoint.com
   INFERENCE_API_TOKEN=your-actual-token-here
   ```

2. Check available models on your inference service:
   ```bash
   curl https://your-api-endpoint.com/v1/models \
     -H "Authorization: Bearer your-token"
   ```

3. Update model names to match the exact names from your API:
   ```bash
   EMBEDDING_MODEL_NAME=BAAI/bge-base-en-v1.5
   INFERENCE_MODEL_NAME=Qwen/Qwen3-4B-Instruct-2507
   ```

4. Restart containers: `docker compose down && docker compose up --build`

### Containers fail to start

**Problem**: Docker containers won't start or crash immediately

**Solution**:

1. Check logs for specific errors:
   ```bash
   docker compose logs backend
   docker compose logs frontend
   ```

2. Ensure ports 5001 and 3000 are available:
   ```bash
   # Windows
   netstat -ano | findstr :5001
   netstat -ano | findstr :3000

   # Unix/Mac
   lsof -i :5001
   lsof -i :3000
   ```

3. Clean up and rebuild:
   ```bash
   docker compose down -v
   docker compose up --build
   ```

4. Restart Docker Desktop if issues persist

## API Common Issues

#### "INFERENCE_API_ENDPOINT and INFERENCE_API_TOKEN must be set"

**Solution**:

1. Create a `.env` file in the `api` directory
2. Add your inference configuration:
   ```bash
   INFERENCE_API_ENDPOINT=https://your-actual-api-endpoint.com
   INFERENCE_API_TOKEN=your-actual-token-here
   EMBEDDING_MODEL_NAME=BAAI/bge-base-en-v1.5
   INFERENCE_MODEL_NAME=Qwen/Qwen3-4B-Instruct-2507
   ```
3. Restart the server

#### "No documents uploaded"

**Solution**:

- Upload a PDF first using the `/upload-pdf` endpoint
- Check server logs for any upload errors
- Verify the PDF is not corrupted or empty

#### "Could not load vector store"

**Solution**:

- The vector store is created when you upload your first PDF
- Check that the application has write permissions in the directory
- Verify `dmv_index/` directory exists and is accessible

#### Import errors

**Solution**:

1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Verify you're using Python 3.10 or higher: `python --version`
3. Activate your virtual environment if using one

#### Server won't start

**Solution**:

1. Check if port 5000 is already in use: `lsof -i :5000` (Unix) or `netstat -ano | findstr :5000` (Windows)
2. Use a different port: `uvicorn server:app --port 5001`
3. Check the logs for specific error messages

#### PDF upload fails

**Solution**:

1. Verify the file is a valid PDF
2. Check file size (must be under 50MB by default)
3. Ensure the PDF contains extractable text (not just images)
4. Check server logs for detailed error messages

#### Query returns no answer

**Solution**:

1. Verify a document has been uploaded successfully
2. Try rephrasing your question
3. Check if the document contains relevant information
4. Increase `TOP_K_DOCUMENTS` in `config.py` for broader search

## UI Common Issues

### API Connection Issues

**Problem**: "Failed to upload PDF" or "Failed to get response"

**Solution**:

1. Ensure the API server is running on `http://localhost:5000`
2. Check browser console for detailed errors
3. Verify CORS is enabled in the API

### Build Issues

**Problem**: Build fails with dependency errors

**Solution**:

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Styling Issues

**Problem**: Styles not applying

**Solution**:

```bash
# Rebuild Tailwind CSS
npm run dev
```
