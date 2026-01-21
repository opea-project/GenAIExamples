# Troubleshooting Guide

This guide covers common issues and solutions for the Documentation Generator Micro-Agents application.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Errors](#configuration-errors)
- [Runtime Errors](#runtime-errors)
- [Agent Failures](#agent-failures)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)
- [Network and API Errors](#network-and-api-errors)

---

## Installation Issues

### Docker Container Build Fails

**Error:** `ERROR [internal] load build context`

**Cause:** Docker daemon not running or insufficient permissions.

**Solution:**
```bash
# Start Docker daemon (Linux/Mac)
sudo systemctl start docker

# On Windows, start Docker Desktop application

# Verify Docker is running
docker ps
```

### Port Already in Use

**Error:** `Error starting userland proxy: listen tcp 0.0.0.0:5001: bind: address already in use`

**Cause:** Another service is using port 5001 (backend) or 3000 (frontend).

**Solution:**
```bash
# Find process using the port
# On Linux/Mac:
lsof -i :5001
lsof -i :3000

# On Windows:
netstat -ano | findstr :5001
netstat -ano | findstr :3000

# Kill the process or change ports in docker-compose.yml
```

---

## Configuration Errors

### Missing GenAI Gateway API Key

**Error:** `ValueError: GENAI_GATEWAY_API_KEY not configured`

**Cause:** API key not set in `.env` file.

**Solution:**
```bash
# Copy environment template
cp api/.env.example api/.env

# Edit api/.env and add your API key
GENAI_GATEWAY_API_KEY=your_actual_api_key_here
```

### Invalid GitHub Token

**Error:** `401 Unauthorized` when creating pull requests

**Cause:** GitHub token missing, expired, or has insufficient permissions.

**Solution:**
1. Generate a new Personal Access Token at https://github.com/settings/tokens
2. Select `repo` scope (full control of repositories)
3. Update `GITHUB_TOKEN` in `api/.env`
4. Token format should be: `ghp_` followed by 36 alphanumeric characters

### Authentication Mode Mismatch

**Error:** `KeyError: 'KEYCLOAK_CLIENT_SECRET'` or connection refused

**Cause:** AUTH_MODE set to keycloak but credentials not configured.

**Solution:**
```bash
# For GenAI Gateway (recommended):
AUTH_MODE=genai_gateway
GENAI_GATEWAY_URL=https://your-gateway-url.com
GENAI_GATEWAY_API_KEY=your_key_here

# For Keycloak:
AUTH_MODE=keycloak
BASE_URL=https://your-inference-endpoint.com
KEYCLOAK_CLIENT_SECRET=your_secret_here
```

---

## Runtime Errors

### Repository Clone Fails

**Error:** `fatal: repository not found` or `Permission denied (publickey)`

**Cause:** Invalid repository URL or insufficient permissions.

**Solution:**
1. Verify the GitHub URL is correct and accessible
2. For private repositories, ensure:
   - Repository exists and you have access
   - Authentication is configured correctly
   - Organization SSO is authorized if applicable

### Repository Too Large

**Error:** `Repository exceeds maximum size of 10GB`

**Cause:** Repository size exceeds MAX_REPO_SIZE limit.

**Solution:**
```bash
# Option 1: Increase limit in api/.env
MAX_REPO_SIZE=21474836480  # 20GB in bytes

# Option 2: Use subfolder targeting
# Instead of: https://github.com/org/repo
# Use: https://github.com/org/repo/tree/main/backend
```

### File Size Limit Exceeded

**Error:** `File too large (X bytes). Maximum is 1.0MB`

**Cause:** Individual file exceeds MAX_FILE_SIZE limit.

**Solution:**
```bash
# Increase file size limit in api/.env
MAX_FILE_SIZE=2000000  # 2MB in bytes

# Or exclude large files by using subfolder targeting
```

### Too Many Files in Repository

**Error:** `Repository has X files, maximum is 500`

**Cause:** Repository exceeds MAX_FILES_TO_SCAN limit.

**Solution:**
```bash
# Increase file scan limit in api/.env
MAX_FILES_TO_SCAN=1000

# Or use subfolder targeting for specific directories
```

---

## Agent Failures

### Agent Timeout

**Error:** `Agent execution timed out after 300 seconds`

**Cause:** Agent taking too long to complete analysis.

**Solution:**
```bash
# Increase timeout in api/.env
AGENT_TIMEOUT=600  # 10 minutes

# Or reduce repository size using subfolder targeting
```

### Code Explorer Agent Fails

**Error:** `CodeExplorer failed: No code files found`

**Cause:** Repository contains no recognized programming language files.

**Solution:**
- Verify repository contains source code files (.py, .js, .ts, .go, .rs, etc.)
- Check if files are in subdirectories (agents scan recursively)
- Ensure repository cloning completed successfully

### API Reference Agent Returns Empty Results

**Error:** `No API endpoints extracted`

**Cause:** Repository doesn't contain API route definitions, or patterns not recognized.

**Solution:**
- This is normal for non-API projects (libraries, CLI tools)
- For API projects, ensure route definitions use standard patterns:
  - FastAPI: `@router.get("/endpoint")`, `@app.post("/endpoint")`
  - Flask: `@app.route("/endpoint")`
  - Express: `app.get("/endpoint")`
  - Spring: `@GetMapping("/endpoint")`

### Mermaid Diagram Validation Fails

**Error:** `Diagram has semantic issues: missing Backend node`

**Cause:** Generated diagram doesn't match detected project structure.

**Solution:**
- This is a warning, not a failure - diagram is still generated
- The system validates diagrams against detected components (backend, frontend, database)
- Check agent logs to see what was detected in Evidence Aggregator
- Diagram may need manual refinement if complex architecture

### QA Validator Detects Issues

**Error:** `QA validation failed: Low quality score`

**Cause:** README sections don't match detected evidence or contain hallucinations.

**Solution:**
- Review the QA validation output in agent logs
- Check if correct sections were generated by section-writer agents
- Verify Evidence Aggregator detected files correctly
- This doesn't block README generation - final output is still produced

---

## Performance Issues

### Slow Documentation Generation

**Symptom:** Workflow takes longer than 5 minutes

**Causes and Solutions:**

1. **Large repository**
   ```bash
   # Reduce scan limits in api/.env
   MAX_FILES_TO_SCAN=300
   MAX_LINES_PER_FILE=300
   ```

2. **High token usage**
   - Check metrics summary in agent logs
   - Typical usage: 20K-40K tokens per repository
   - If much higher, repository may have very large files

3. **Network latency to LLM backend**
   - Ensure low latency network connection to GenAI Gateway
   - Check GENAI_GATEWAY_URL is accessible

### High Token Usage

**Symptom:** Metrics show >60K tokens for small repository

**Cause:** Strategic sampling not working efficiently or very verbose files.

**Solution:**
```bash
# Reduce lines per file in api/.env
MAX_LINES_PER_FILE=300

# Agents automatically use pattern_window mode to minimize context
# This is the default and most efficient strategy
```

---

## Docker Issues

### Backend Container Won't Start

**Error:** `backend exited with code 1`

**Solution:**
```bash
# Check backend logs for specific error
docker-compose logs backend

# Common causes:
# 1. Missing .env file - solution above in Configuration Errors
# 2. Invalid Python dependencies - rebuild:
docker-compose build --no-cache backend
docker-compose up -d

# 3. Port conflict - solution above in Installation Issues
```

### Frontend Container Build Fails

**Error:** `npm install failed` or `Cannot find module`

**Solution:**
```bash
# Rebuild frontend with clean cache
docker-compose build --no-cache frontend
docker-compose up -d frontend

# Verify Node.js version in Dockerfile is compatible (16+)
```

### Container Memory Issues

**Error:** `Killed` or `Out of memory`

**Solution:**
```bash
# Increase Docker memory limit in Docker Desktop settings
# Recommended: 4GB minimum, 8GB preferred

# Or reduce repository analysis limits:
MAX_FILES_TO_SCAN=200
MAX_LINES_PER_FILE=300
```

### Cannot Connect to Backend from Frontend

**Error:** `Network error` or `Connection refused` in browser console

**Cause:** Docker network misconfiguration or CORS issue.

**Solution:**
```bash
# Verify both containers are running
docker-compose ps

# Check backend is accessible
curl http://localhost:5001/api/health

# Verify CORS_ORIGINS in api/.env includes frontend URL
CORS_ORIGINS=["http://localhost:3000"]

# Restart services
docker-compose restart
```

---

## Network and API Errors

### GenAI Gateway Connection Refused

**Error:** `ConnectionRefusedError: [Errno 111] Connection refused`

**Cause:** GenAI Gateway URL incorrect or service unavailable.

**Solution:**
```bash
# Verify GENAI_GATEWAY_URL is correct in api/.env
# Test connectivity:
curl https://your-gateway-url.com/health

# Check firewall/proxy settings allow outbound HTTPS
```

### LLM Request Timeout

**Error:** `Timeout waiting for LLM response`

**Cause:** LLM backend overloaded or network latency.

**Solution:**
```bash
# Increase agent timeout in api/.env
AGENT_TIMEOUT=600

# Check LLM backend status
# Contact infrastructure team if persistent
```

### Rate Limit Exceeded

**Error:** `429 Too Many Requests` or `Rate limit exceeded`

**Cause:** Too many concurrent requests to LLM backend.

**Solution:**
- Wait a few minutes before retrying
- Reduce concurrent documentation generation jobs
- Contact infrastructure team to increase rate limits
- The system processes agents sequentially to minimize rate limit issues

### GitHub API Rate Limit (PR Creation)

**Error:** `403 API rate limit exceeded`

**Cause:** Too many GitHub API calls within rate limit window.

**Solution:**
- Wait 1 hour for rate limit reset
- Authenticated requests have higher limits (5000/hour vs 60/hour)
- Ensure GITHUB_TOKEN is configured correctly
- Check rate limit status:
  ```bash
  curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
  ```

---

## Advanced Troubleshooting

### Enable Debug Logging

To get more detailed logs for debugging:

```bash
# Add to api/.env
LOG_LEVEL=DEBUG

# Restart backend
docker-compose restart backend

# View detailed logs
docker-compose logs -f backend
```

### Check Agent Execution Metrics

Metrics are displayed in the agent logs panel after workflow completion:

```
📊 Workflow Metrics Summary
├─ Total Agents: 9
├─ Successful: 9
├─ Failed: 0
├─ Total Duration: 155.59s
├─ Total Tokens: 33,135
│  ├─ Input: 30,728
│  └─ Output: 2,407
├─ Total Tool Calls: 23
├─ Total LLM Calls: 31
└─ Average TPS: 15.47 tokens/sec
```

**Analysis:**
- **Failed agents**: Should be 0 for successful runs
- **Total tokens**: Typical range 20K-40K for medium repositories
- **Average TPS**: Depends on LLM backend performance
- **Tool calls**: Indicates how many tool invocations agents made

### Manual Repository Cleanup

If cloned repositories aren't cleaned up automatically:

```bash
# Clean tmp directory
rm -rf api/tmp/repos/*

# Or within Docker:
docker-compose exec backend rm -rf /app/tmp/repos/*
```

### Reset Application State

To completely reset the application:

```bash
# Stop and remove containers
docker-compose down -v

# Remove temporary files
rm -rf api/tmp/*

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

---

## Getting Help

If you continue to experience issues:

1. **Check Logs:** Review backend logs with `docker-compose logs backend -f`
2. **Verify Configuration:** Ensure all required environment variables are set in `api/.env`
3. **Test Connectivity:** Verify network access to GenAI Gateway and GitHub
4. **Metrics Analysis:** Check workflow metrics for anomalies (token usage, duration, failed agents)
5. **Report Issues:** If the problem persists, collect:
   - Error messages from logs
   - Workflow metrics summary
   - Repository URL (if not sensitive)
   - Configuration (redact sensitive values)

---

## Common Success Indicators

A successful run should show:

```
✅ Repository cloned successfully
✅ Overview & Features sections completed
✅ Extracted X API endpoints
✅ Architecture section completed
✅ Troubleshooting section completed
✅ Configuration section completed
✅ Prerequisites & Deployment sections completed
✅ Evidence aggregated: X Python deps, Y Node deps
✅ Planner completed - Z sections planned
✅ Mermaid Generator completed
✅ QA Validator completed (Score: XX)
✅ Documentation generation complete!
📊 Workflow Metrics Summary
```

All agents should complete successfully with metrics showing reasonable token usage and no failed agents.
