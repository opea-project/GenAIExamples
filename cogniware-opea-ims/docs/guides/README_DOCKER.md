# MSmartCompute Platform - Docker Setup Guide

This guide provides comprehensive instructions for setting up and running the MSSmartCompute Platform using Docker containers.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS, or Linux
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: At least 10GB free space
- **GPU**: NVIDIA GPU with CUDA support (optional, for GPU acceleration)

### Required Software
1. **Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and restart your computer
   - Ensure Docker Desktop is running

2. **NVIDIA Docker Runtime** (Optional, for GPU support)
   - Install nvidia-docker2 for Linux
   - For Windows/macOS, GPU support is included in Docker Desktop

## Quick Start

### 1. Clone and Navigate
```bash
cd cogniware_engine_cpp
```

### 2. Start the Platform

#### Windows
```cmd
scripts\start-containers.bat
```

#### Linux/macOS
```bash
chmod +x scripts/start-containers.sh
./scripts/start-containers.sh
```

### 3. Test the Platform

#### Windows
```cmd
scripts\test-api.bat
```

#### Linux/macOS
```bash
chmod +x scripts/test-api.sh
./scripts/test-api.sh
```

## Platform Architecture

The MSSmartCompute Platform consists of the following services:

### Core Services
- **MSSmartCompute Platform** (Port 8080): Main API server with CUDA virtualization
- **Nginx** (Port 80): Reverse proxy and load balancer
- **PostgreSQL** (Port 5432): Metadata and session storage
- **Redis** (Port 6379): Caching and session management

### Monitoring Services
- **Grafana** (Port 3000): Metrics visualization dashboard
- **Prometheus** (Port 9090): Metrics collection and storage

### Test Services
- **Test Client**: Automated API testing container

## Service Endpoints

Once the platform is running, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| MSSmartCompute API | http://localhost:8080 | Main platform API |
| Nginx Proxy | http://localhost:80 | Reverse proxy |
| Grafana | http://localhost:3000 | Monitoring dashboard |
| Prometheus | http://localhost:9090 | Metrics collection |

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Grafana | admin | admin123 |
| PostgreSQL | cogniware | cogniware123 |
| API Access | test-api-key-123 | (API Key) |

## API Testing

### Manual Testing with curl

#### Health Check
```bash
curl http://localhost:8080/health
```

#### List Models
```bash
curl http://localhost:8080/api/v1/models
```

#### Create Session
```bash
curl -X POST http://localhost:8080/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-123" \
  -d '{
    "user_id": "test-user-123",
    "model_id": "test-model"
  }'
```

#### Run Inference
```bash
curl -X POST http://localhost:8080/api/v1/inference \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-123" \
  -d '{
    "model_id": "test-model",
    "batch_size": 1,
    "sequence_length": 128,
    "data_type": "float32",
    "input_data": [0.1, 0.2, 0.3, 0.4, 0.5]
  }'
```

#### Get Performance Metrics
```bash
curl http://localhost:8080/api/v1/metrics
```

## Container Management

### View Container Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f cogniware
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Stop the Platform
```bash
docker-compose down
```

### Restart the Platform
```bash
docker-compose restart
```

### Rebuild Containers
```bash
docker-compose up -d --build
```

## Configuration

### Environment Variables
Key configuration options can be modified in `docker-compose.yml`:

```yaml
environment:
  - NVIDIA_VISIBLE_DEVICES=all
  - NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

### Volume Mounts
The platform uses the following volume mounts:

- `./models:/opt/cogniware/models:ro` - Model files (read-only)
- `./logs:/opt/cogniware/logs` - Application logs
- `./cache:/opt/cogniware/cache` - Cache directory
- `./temp:/opt/cogniware/temp` - Temporary files

### Database Configuration
PostgreSQL configuration is in `init-db.sql`:
- Database: `cogniware`
- User: `cogniware`
- Password: `cogniware123`

## Monitoring and Metrics

### Grafana Dashboard
1. Open http://localhost:3000
2. Login with `admin/admin123`
3. Navigate to Dashboards to view:
   - GPU utilization
   - Memory usage
   - API request metrics
   - System performance

### Prometheus Metrics
1. Open http://localhost:9090
2. Query metrics like:
   - `cogniware_gpu_utilization`
   - `cogniware_memory_usage`
   - `cogniware_api_requests_total`

## Troubleshooting

### Common Issues

#### Docker Not Running
```
[ERROR] Docker is not running. Please start Docker Desktop and try again.
```
**Solution**: Start Docker Desktop and wait for it to fully initialize.

#### Port Already in Use
```
[ERROR] Port 8080 is already in use
```
**Solution**: Stop other services using the port or modify the port in `docker-compose.yml`.

#### GPU Not Available
```
[WARNING] NVIDIA Docker runtime is not available. GPU acceleration will not work.
```
**Solution**: Install nvidia-docker2 or use CPU-only mode.

#### Container Build Fails
```
[ERROR] Failed to build container
```
**Solution**: 
1. Check Docker has enough resources (RAM, disk space)
2. Ensure stable internet connection for downloading images
3. Try rebuilding: `docker-compose build --no-cache`

### Log Analysis

#### Check Container Logs
```bash
# Recent logs
docker-compose logs --tail=50 cogniware

# Follow logs in real-time
docker-compose logs -f cogniware

# Logs with timestamps
docker-compose logs -t cogniware
```

#### Check Resource Usage
```bash
# Container resource usage
docker stats

# Disk usage
docker system df
```

### Performance Tuning

#### Memory Allocation
Increase Docker Desktop memory allocation:
1. Open Docker Desktop Settings
2. Go to Resources > Memory
3. Increase to 8GB or more

#### GPU Memory
For GPU workloads, ensure sufficient GPU memory:
```bash
# Check GPU memory
nvidia-smi
```

## Development

### Building from Source
```bash
# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build cogniware
```

### Adding Custom Models
1. Place model files in the `models/` directory
2. Update the database with model metadata
3. Restart the platform

### Custom Configuration
1. Modify `config.json` for platform settings
2. Update `docker-compose.yml` for container settings
3. Modify `nginx/nginx.conf` for proxy settings

## Security Considerations

### Production Deployment
For production use:
1. Change default passwords
2. Enable HTTPS with SSL certificates
3. Configure firewall rules
4. Use secrets management for sensitive data
5. Enable authentication and authorization

### API Security
- Use API keys for authentication
- Implement rate limiting
- Validate all input data
- Log security events

## Support

### Getting Help
1. Check the logs: `docker-compose logs -f`
2. Review this documentation
3. Check the API documentation: `docs/API_DOCUMENTATION.md`
4. Review deployment guide: `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`

### Reporting Issues
When reporting issues, include:
1. Operating system and version
2. Docker version
3. Container logs
4. Steps to reproduce
5. Expected vs actual behavior

## Next Steps

After successful setup:
1. Explore the API endpoints
2. Load your own models
3. Configure monitoring dashboards
4. Set up production deployment
5. Integrate with your applications

For detailed API documentation, see `docs/API_DOCUMENTATION.md`.
For production deployment guide, see `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`. 