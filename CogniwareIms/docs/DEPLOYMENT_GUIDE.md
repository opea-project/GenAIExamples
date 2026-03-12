# Deployment Guide - Cogniware OPEA IMS

Complete guide for deploying the AI-Powered Inventory Management System to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Local Development](#local-development)
4. [Production Deployment](#production-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Scaling](#scaling)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum System Requirements

- **CPU**: **Intel Xeon Processor** (3rd Gen Scalable or newer recommended)
  - Minimum: 4 cores (8+ cores recommended)
  - Optimized for Intel Xeon with AI acceleration
- **RAM**: 16GB minimum (32GB+ recommended for production)
- **Disk**: 50GB free space (SSD recommended)
- **OS**: Linux (Ubuntu 20.04/22.04 preferred), macOS, Windows with WSL2
- **Note**: This system is specifically optimized for Intel Xeon processors and leverages Intel-specific optimizations for AI workloads

### Software Requirements

```bash
# Docker
docker --version  # 24.0+
docker-compose --version  # 2.0+

# Optional (for local development)
python --version  # 3.11+
node --version  # 18+
```

### Network Requirements

- Outbound internet access (for pulling Docker images)
- Ports 3000, 8000 available (or configure alternatives)
- Optional: Domain name and SSL certificates for production

---

## Quick Start

### 1. Clone/Download Package

```bash
# If from repository
git clone https://github.com/your-org/cogniware-opea-ims.git
cd cogniware-opea-ims

# Or extract downloaded archive
unzip cogniware-opea-ims.zip
cd cogniware-opea-ims
```

### 2. Configure Environment

```bash
# Copy example environment file
cp env.example .env

# IMPORTANT: Edit .env and update security settings
nano .env  # or your preferred editor

# Generate strong JWT secret
openssl rand -hex 32
# Add this to JWT_SECRET_KEY in .env

# Set strong passwords for:
# - POSTGRES_PASSWORD
# - GRAFANA_PASSWORD (if using monitoring)
```

### 3. Deploy

```bash
# Make start script executable
chmod +x start.sh

# Run deployment
./start.sh
```

### 4. Initialize Knowledge Base

```bash
# After services are running
docker-compose exec backend python app/init_knowledge_base.py
```

### 5. Access Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **RedisInsight**: http://localhost:8001

**Default Login:**

- Email: `inventory@company.com`
- Password: `password123`

⚠️ **Change default passwords immediately!**

---

## Local Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/opea_ims"
export REDIS_URL="redis://localhost:6379"
export OPEA_EMBEDDING_URL="http://localhost:6000"
export OPEA_LLM_URL="http://localhost:9000"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
pytest --cov=app
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Set API URL
export NEXT_PUBLIC_API_URL="http://localhost:8000"

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### OPEA Services (Development)

```bash
# Start only OPEA microservices
docker-compose up -d embedding-service llm-service retrieval-service redis postgres
```

---

## Production Deployment

### Security Configuration

#### 1. Update Environment Variables

```env
# .env file
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Strong secrets (CRITICAL!)
JWT_SECRET_KEY=<generated-with-openssl-rand-hex-32>
POSTGRES_PASSWORD=<strong-password>

# Production URLs
ALLOWED_ORIGINS=https://your-domain.com
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

#### 2. Change Default Credentials

Create new admin users and disable defaults:

```bash
# Connect to backend
docker-compose exec backend python

# In Python shell
from app.core.security import SecurityManager
hashed = SecurityManager.get_password_hash("your-strong-password")
print(hashed)
# Use this hash to create new users
```

#### 3. Enable HTTPS

```bash
# Install certbot for Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Certificates will be auto-renewed
```

### nginx Configuration

```nginx
# /etc/nginx/sites-available/opea-ims

upstream frontend {
    server localhost:3000;
}

upstream backend {
    server localhost:8000;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name your-domain.com api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# Frontend
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for LLM requests
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable

# Block direct access to services
sudo ufw deny 3000/tcp  # Frontend (access via nginx)
sudo ufw deny 8000/tcp  # Backend (access via nginx)
sudo ufw deny 5432/tcp  # PostgreSQL
sudo ufw deny 6379/tcp  # Redis
```

---

## Cloud Deployment

### AWS Deployment

#### EC2 Instance

```bash
# Launch instance
# Recommended: t3.2xlarge or larger
# OS: Ubuntu 22.04 LTS

# Connect via SSH
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy application
git clone https://github.com/your-org/cogniware-opea-ims.git
cd cogniware-opea-ims
./start.sh
```

#### RDS for PostgreSQL (Optional)

```env
# Update .env
DATABASE_URL=postgresql://admin:password@your-rds-endpoint:5432/opea_ims
```

#### ElastiCache for Redis (Optional)

```env
# Update .env
REDIS_URL=redis://your-elasticache-endpoint:6379
```

### Azure Deployment

#### Azure Container Instances

```bash
# Create resource group
az group create --name opea-ims-rg --location eastus

# Deploy using Docker Compose
az container create \
  --resource-group opea-ims-rg \
  --file docker-compose.yml \
  --name opea-ims
```

#### Azure Database for PostgreSQL

```env
# Update .env
DATABASE_URL=postgresql://admin@your-server:password@your-server.postgres.database.azure.com:5432/opea_ims?sslmode=require
```

### Google Cloud Deployment

#### GCE Instance

```bash
# Create instance
gcloud compute instances create opea-ims \
  --machine-type n2-standard-8 \
  --image-family ubuntu-2204-lts \
  --image-project ubuntu-os-cloud \
  --boot-disk-size 100GB

# SSH and deploy
gcloud compute ssh opea-ims
# Follow standard deployment steps
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3

  frontend:
    deploy:
      replicas: 2
```

### Load Balancing

```nginx
# nginx upstream configuration
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Database Scaling

```bash
# PostgreSQL read replicas
# Configure replication in PostgreSQL

# Redis cluster
# Use Redis Cluster or Sentinel for HA
```

---

## Monitoring

### Enable Monitoring Stack

```bash
# Start with monitoring profile
docker-compose --profile monitoring up -d
```

### Access Monitoring Tools

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
- **RedisInsight**: http://localhost:8001

### Custom Metrics

```bash
# View application metrics
curl http://localhost:8000/metrics
```

### Log Aggregation

```bash
# View all logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Save logs
docker-compose logs > logs_$(date +%Y%m%d).txt
```

---

## Backup & Recovery

### Database Backup

```bash
# Manual backup
docker-compose exec postgres pg_dump -U postgres opea_ims > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20241013.sql | docker-compose exec -T postgres psql -U postgres opea_ims
```

### Automated Backups

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backups
DATE=$(date +%Y%m%d_%H%M%S)

# Database
docker-compose exec -T postgres pg_dump -U postgres opea_ims > $BACKUP_DIR/db_$DATE.sql

# Redis
docker-compose exec -T redis redis-cli BGSAVE

# Compress
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/db_$DATE.sql

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete
EOF

chmod +x backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

---

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend

# Restart service
docker-compose restart backend
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready

# Connect to database
docker-compose exec postgres psql -U postgres opea_ims

# Check Redis
docker-compose exec redis redis-cli ping
```

### OPEA Service Issues

```bash
# Check health
curl http://localhost:6000/health  # Embedding
curl http://localhost:9000/health  # LLM

# View logs
docker-compose logs embedding-service
docker-compose logs llm-service

# Restart services
docker-compose restart embedding-service llm-service
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check disk space
df -h

# Check memory
free -h
```

### Common Issues

#### Issue: Services timeout

**Solution**: Increase timeouts in docker-compose.yml

```yaml
services:
  llm-service:
    healthcheck:
      start_period: 300s # Increase from 120s
```

#### Issue: Out of memory

**Solution**: Increase resource limits

```yaml
services:
  llm-service:
    deploy:
      resources:
        limits:
          memory: 32G # Increase from 16G
```

---

## Support

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Email**: support@cogniware.com

---

## Next Steps

After deployment:

1. ✅ Initialize knowledge base
2. ✅ Change default passwords
3. ✅ Configure backups
4. ✅ Set up monitoring
5. ✅ Test all functionality
6. ✅ Configure SSL/HTTPS
7. ✅ Set up firewall rules
8. ✅ Review security checklist

---

**Your OPEA IMS system is production-ready! 🚀**
