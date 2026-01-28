# Troubleshooting Guide

This document contains all common issues encountered during development and their solutions.

## Table of Contents

- [API Common Issues](#api-common-issues)
- [UI Common Issues](#ui-common-issues)

### API Common Issues

#### "API client not initialized. Check inference API configuration."

**Solution**:

1. Create a `.env` file in the root directory
2. Add your inference API credentials:
   ```
   INFERENCE_API_ENDPOINT=https://your-api-endpoint.com/deployment
   INFERENCE_API_TOKEN=your-pre-generated-token-here
   INFERENCE_MODEL_NAME=codellama/CodeLlama-34b-Instruct-hf
   ```
3. Restart the server

#### "Code too long. Maximum length is 10000 characters"

**Solution**:

- The limit exists due to model context window constraints
- Break your code into smaller modules
- Translate one class or function at a time
- Or adjust `MAX_CODE_LENGTH` in `.env` if needed

#### "Source language not supported"

**Solution**:

- Only 6 languages are supported: Java, C, C++, Python, Rust, Go
- Check the `/languages` endpoint for the current list
- Ensure language names are lowercase (e.g., "python" not "Python")

#### Import errors

**Solution**:

1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Verify you're using Python 3.10 or higher: `python --version`
3. Activate your virtual environment if using one

#### Server won't start

**Solution**:

1. Check if port 5001 is already in use: `lsof -i :5001` (Unix) or `netstat -ano | findstr :5001` (Windows)
2. Use a different port by updating `BACKEND_PORT` in `.env`
3. Check the logs for specific error messages

#### PDF upload fails

**Solution**:

1. Verify the file is a valid PDF
2. Check file size (must be under 10MB by default)
3. Ensure the PDF contains extractable text (not just images)
4. Check server logs for detailed error messages

#### Translation returns empty result

**Solution**:

1. Verify inference API authentication is working (check `/health` endpoint)
2. Check if the model endpoint is accessible
3. Verify INFERENCE_API_TOKEN is valid and not expired
4. Try with simpler code first
5. Check server logs for API errors

#### "No module named 'pypdf'"

**Solution**:

```bash
pip install pypdf
```

## UI Common Issues

### API Connection Issues

**Problem**: "Failed to translate" or "Failed to upload PDF"

**Solution**:

1. Ensure the API server is running on `http://localhost:5001`
2. Check browser console for detailed errors
3. Verify CORS is enabled in the API
4. Test API directly: `curl http://localhost:5001/health`

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

### Character Counter Not Updating

**Problem**: Character counter shows 0 / 10,000 even with code

**Solution**:

1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
3. Restart the dev server
