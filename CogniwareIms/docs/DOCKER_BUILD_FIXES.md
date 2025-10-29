# Docker Build Fixes - Cogniware OPEA IMS

## Issues Fixed

### Error Messages

```
#20 [cogniwareims-backend stage-1 8/8] COPY --chown=appuser:appuser ./app ./app
#20 ERROR: failed to calculate checksum: "/app": not found

#26 [cogniwareims-ui deps 3/4] COPY package.json package-lock.json* ./
#26 ERROR: failed to calculate checksum: "/package.json": not found
```

### Root Cause

The docker-compose configuration sets the build context to the repository root:

```yaml
cogniwareims-backend:
    build:
      context: ../../..  # Points to cogniware-opea-ims/ root
      dockerfile: backend/Dockerfile
```

But the Dockerfiles were using relative paths assuming the context was the backend/frontend directory:

```dockerfile
# WRONG - assumes context is backend/
COPY requirements.txt .
COPY ./app ./app

# WRONG - assumes context is frontend/
COPY package.json package-lock.json* ./
```

## Fixes Applied

### 1. Backend Dockerfile (`backend/Dockerfile`)

#### Before:
```dockerfile
# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser ./app ./app
```

#### After:
```dockerfile
# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser backend/app ./app
```

### 2. Frontend Dockerfile (`frontend/Dockerfile`)

#### Before:
```dockerfile
# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Rebuild the source code
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
```

#### After:
```dockerfile
# Install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --only=production

# Rebuild the source code
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .
```

## Updated Files

1. ✅ `backend/Dockerfile` - Fixed COPY paths for repository root context
2. ✅ `frontend/Dockerfile` - Fixed COPY paths for repository root context

## Build Context Explanation

### Directory Structure:
```
cogniware-opea-ims/          # <-- Build context root
├── backend/
│   ├── Dockerfile           # dockerfile: backend/Dockerfile
│   ├── requirements.txt     # COPY backend/requirements.txt
│   └── app/                 # COPY backend/app
│       └── main.py
├── frontend/
│   ├── Dockerfile           # dockerfile: frontend/Dockerfile
│   ├── package.json         # COPY frontend/package.json
│   └── app/
│       └── page.tsx
└── docker_compose/
    └── intel/xeon/
        └── compose.yaml     # context: ../../.. (points to root)
```

### How Build Context Works:

When you specify:
```yaml
build:
  context: ../../..
  dockerfile: backend/Dockerfile
```

Docker:
1. Sets the build context to `cogniware-opea-ims/` (repository root)
2. Reads the Dockerfile from `backend/Dockerfile`
3. All COPY commands are relative to the context (repository root)

Therefore:
- ✅ `COPY backend/requirements.txt .` - Correct
- ❌ `COPY requirements.txt .` - Wrong (looks for cogniware-opea-ims/requirements.txt)

## Testing the Fix

### Build Images Manually:

```bash
cd /Users/deadbrain/cogniware-opea-ims

# Build backend
docker build -f backend/Dockerfile -t opea/cogniwareims-backend:latest .

# Build frontend
docker build -f frontend/Dockerfile -t opea/cogniwareims-ui:latest .
```

### Build with Docker Compose:

```bash
cd docker_compose/intel/xeon
docker compose build

# Or use the build.yaml
cd ../../..
cd docker_build_image
docker compose -f build.yaml build
```

### Verify Build Success:

```bash
# Check images
docker images | grep cogniware

# Expected output:
# opea/cogniwareims-backend   latest   <id>   <time>   <size>
# opea/cogniwareims-ui        latest   <id>   <time>   <size>
```

## Alternative Solution

If you prefer to keep Dockerfiles as-is, you could change the docker-compose context:

```yaml
# Option 1: Change context to backend directory
cogniwareims-backend:
    build:
      context: ../../../backend    # Points to backend/
      dockerfile: Dockerfile        # Now in backend/
```

However, the current fix (updating COPY paths) is better because:
- ✅ Maintains consistent build context at repository root
- ✅ Works with docker_build_image/build.yaml
- ✅ Allows copying files from anywhere in the repo
- ✅ Standard OPEA pattern for multi-component projects

## Validation Commands

```bash
# Check Dockerfile syntax
docker build --check -f backend/Dockerfile .
docker build --check -f frontend/Dockerfile .

# Build without cache to verify
docker build --no-cache -f backend/Dockerfile -t test-backend .
docker build --no-cache -f frontend/Dockerfile -t test-frontend .

# Clean up test images
docker rmi test-backend test-frontend
```

## Related Files

- `backend/Dockerfile` - Fixed COPY paths
- `frontend/Dockerfile` - Fixed COPY paths
- `docker_compose/intel/xeon/compose.yaml` - Build context configuration
- `docker_build_image/build.yaml` - Build configuration

## Notes

- ✅ Dockerfiles now work with repository root as build context
- ✅ Compatible with both docker-compose and manual builds
- ✅ Follows OPEA standard structure
- ✅ Multi-stage builds optimized for production
- ✅ Security: non-root users in containers
- ✅ Health checks included

## Next Steps

After this fix, you can successfully:

1. Build images:
```bash
cd docker_build_image
docker compose -f build.yaml build
```

2. Deploy:
```bash
cd ../docker_compose/intel/xeon
source ./set_env.sh
docker compose up -d
```

3. Initialize:
```bash
docker exec -it cogniwareims-backend python app/init_knowledge_base.py
```

---

**Last Updated**: October 21, 2025
**Status**: ✅ All Docker build issues resolved

