# MSmartCompute Platform - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the MSmartCompute Platform in production environments. The platform includes enhanced CUDA kernels, virtualization drivers, and CogniDream APIs for high-performance machine learning workloads.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [Monitoring](#monitoring)
6. [Security](#security)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

## System Requirements

### Hardware Requirements

#### Minimum Requirements
- **GPU**: NVIDIA GPU with Compute Capability 7.0+ (Volta, Turing, Ampere, or newer)
- **Memory**: 16 GB RAM
- **Storage**: 100 GB SSD
- **CPU**: 8-core x86_64 processor

#### Recommended Requirements
- **GPU**: NVIDIA RTX 4090, A100, H100, or equivalent
- **Memory**: 64 GB RAM or more
- **Storage**: 1 TB NVMe SSD
- **CPU**: 16-core x86_64 processor
- **Network**: 10 Gbps Ethernet

#### Production Requirements
- **GPU**: Multiple NVIDIA A100/H100 GPUs
- **Memory**: 128 GB RAM or more
- **Storage**: 2 TB+ NVMe SSD with RAID
- **CPU**: 32-core x86_64 processor
- **Network**: 25/100 Gbps Ethernet
- **Power**: Redundant power supplies

### Software Requirements

#### Operating System
- Ubuntu 20.04 LTS or newer
- CentOS 8 or newer
- RHEL 8 or newer

#### CUDA Requirements
- CUDA Toolkit 11.8 or newer
- cuDNN 8.6 or newer
- cuBLAS 11.8 or newer

#### System Dependencies
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    libssl-dev \
    libcurl4-openssl-dev \
    libboost-all-dev \
    libspdlog-dev \
    nlohmann-json3-dev

# CentOS/RHEL
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
    cmake \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    openssl-devel \
    libcurl-devel \
    boost-devel \
    spdlog-devel \
    nlohmann-json-devel
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/cogniware-engine.git
cd cogniware-engine/cogniware_engine_cpp
```

### 2. Install CUDA Dependencies

```bash
# Download and install CUDA Toolkit
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run

# Set environment variables
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### 3. Install cuDNN

```bash
# Download cuDNN (requires NVIDIA developer account)
# Place the downloaded file in the project directory
tar -xzvf cudnn-*-archive.tar.xz
sudo cp cuda/include/cudnn*.h /usr/local/cuda/include
sudo cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
sudo chmod a+r /usr/local/cuda/include/cudnn*.h /usr/local/cuda/lib64/libcudnn*
```

### 4. Build the Project

```bash
# Create build directory
mkdir build && cd build

# Configure with CMake
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCUDA_ARCH="70;75;80;86;89" \
    -DENABLE_TENSOR_CORES=ON \
    -DENABLE_MIXED_PRECISION=ON \
    -DENABLE_PROFILING=ON

# Build
make -j$(nproc)

# Install
sudo make install
```

### 5. Create Required Directories

```bash
sudo mkdir -p /opt/cogniware/{logs,models,cache,temp}
sudo chown -R $USER:$USER /opt/cogniware
```

## Configuration

### 1. Basic Configuration

Copy the provided configuration file:

```bash
cp config.json /opt/cogniware/
```

### 2. Environment-Specific Configuration

#### Development Environment
```json
{
  "server": {
    "host": "localhost",
    "port": 8080,
    "log_level": "debug"
  },
  "compute": {
    "optimization_level": 1,
    "enable_profiling": true
  }
}
```

#### Staging Environment
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "log_level": "info"
  },
  "compute": {
    "optimization_level": 2,
    "enable_profiling": true
  },
  "security": {
    "enable_authentication": true,
    "enable_rate_limiting": true
  }
}
```

#### Production Environment
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "log_level": "warn"
  },
  "compute": {
    "optimization_level": 3,
    "enable_profiling": false
  },
  "security": {
    "enable_authentication": true,
    "enable_authorization": true,
    "enable_rate_limiting": true,
    "enable_ssl": true
  },
  "monitoring": {
    "enable_metrics_collection": true,
    "enable_alerting": true
  }
}
```

### 3. GPU Configuration

For multi-GPU setups:

```json
{
  "compute": {
    "device_id": 0,
    "num_streams": 8,
    "enable_tensor_cores": true,
    "enable_mixed_precision": true
  },
  "virtualization": {
    "enable_gpu_virtualization": true,
    "max_virtual_gpus": 8
  }
}
```

## Deployment

### 1. Systemd Service

Create a systemd service file:

```bash
sudo tee /etc/systemd/system/cogniware.service << EOF
[Unit]
Description=MSmartCompute Platform
After=network.target

[Service]
Type=simple
User=cogniware
Group=cogniware
WorkingDirectory=/opt/cogniware
ExecStart=/usr/local/bin/cogniware -c /opt/cogniware/config.json
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/cogniware

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Create Service User

```bash
sudo useradd -r -s /bin/false -d /opt/cogniware cogniware
sudo chown -R cogniware:cogniware /opt/cogniware
```

### 3. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable cogniware
sudo systemctl start cogniware
sudo systemctl status cogniware
```

### 4. Docker Deployment

Create a Dockerfile:

```dockerfile
FROM nvidia/cuda:11.8-devel-ubuntu20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    libssl-dev \
    libcurl4-openssl-dev \
    libboost-all-dev \
    libspdlog-dev \
    nlohmann-json3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . /app
WORKDIR /app/cogniware_engine_cpp

# Build
RUN mkdir build && cd build \
    && cmake .. -DCMAKE_BUILD_TYPE=Release \
    && make -j$(nproc) \
    && make install

# Create directories
RUN mkdir -p /opt/cogniware/{logs,models,cache,temp}

# Copy configuration
COPY config.json /opt/cogniware/

# Expose port
EXPOSE 8080

# Run
CMD ["/usr/local/bin/cogniware", "-c", "/opt/cogniware/config.json"]
```

Build and run:

```bash
docker build -t cogniware .
docker run --gpus all -p 8080:8080 -v /opt/cogniware:/opt/cogniware cogniware
```

## Monitoring

### 1. Health Checks

The platform provides health check endpoints:

```bash
# Basic health check
curl http://localhost:8080/health

# Detailed metrics
curl http://localhost:8080/api/v1/metrics

# Performance metrics
curl http://localhost:8080/api/v1/metrics/history
```

### 2. Log Monitoring

Monitor logs:

```bash
# View real-time logs
sudo journalctl -u cogniware -f

# View log file
tail -f /opt/cogniware/logs/cogniware.log

# Search for errors
grep -i error /opt/cogniware/logs/cogniware.log
```

### 3. GPU Monitoring

Monitor GPU usage:

```bash
# NVIDIA SMI
nvidia-smi

# Continuous monitoring
watch -n 1 nvidia-smi

# Detailed GPU info
nvidia-smi -q
```

### 4. System Monitoring

Monitor system resources:

```bash
# CPU and memory
htop

# Disk usage
df -h

# Network usage
iftop
```

### 5. Prometheus Integration

Add Prometheus metrics endpoint:

```json
{
  "monitoring": {
    "enable_prometheus_metrics": true,
    "prometheus_port": 9090
  }
}
```

## Security

### 1. Network Security

#### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 8080/tcp  # API server
sudo ufw allow 9090/tcp  # Prometheus metrics
sudo ufw enable
```

#### SSL/TLS Configuration

```json
{
  "security": {
    "enable_ssl": true,
    "ssl_cert_file": "/path/to/cert.pem",
    "ssl_key_file": "/path/to/key.pem"
  }
}
```

### 2. Authentication

Implement API key authentication:

```json
{
  "security": {
    "enable_authentication": true,
    "api_keys": {
      "admin": "your-secure-api-key",
      "user1": "user1-api-key"
    }
  }
}
```

### 3. Rate Limiting

```json
{
  "security": {
    "enable_rate_limiting": true,
    "rate_limit_requests_per_minute": 1000,
    "rate_limit_burst_size": 100
  }
}
```

### 4. Input Validation

All API endpoints include input validation:

- Model ID validation
- Data type validation
- Size limits
- Malicious input detection

## Performance Tuning

### 1. GPU Optimization

#### Memory Management

```json
{
  "compute": {
    "max_memory_pool_size": 2147483648,  # 2GB
    "memory_alignment": 256,
    "enable_memory_pooling": true
  }
}
```

#### Kernel Optimization

```json
{
  "compute": {
    "optimization_level": 3,
    "enable_tensor_cores": true,
    "enable_mixed_precision": true,
    "kernel_launch_timeout": 30000
  }
}
```

### 2. Batch Processing

```json
{
  "inference": {
    "enable_batching": true,
    "max_batch_size": 128,
    "batch_timeout": 1000,
    "enable_dynamic_batching": true
  }
}
```

### 3. Caching

```json
{
  "inference": {
    "enable_caching": true,
    "cache_size": 536870912,  # 512MB
    "cache_ttl": 3600
  }
}
```

### 4. Load Balancing

For multi-GPU setups:

```json
{
  "virtualization": {
    "load_balancing_strategy": "least_loaded",
    "scheduling_strategy": "round_robin",
    "enable_adaptive_scheduling": true
  }
}
```

## Troubleshooting

### 1. Common Issues

#### CUDA Errors

```bash
# Check CUDA installation
nvcc --version
nvidia-smi

# Check GPU compatibility
cuda-install-samples-11.8.sh ~
cd ~/NVIDIA_CUDA-11.8_Samples
make
```

#### Memory Issues

```bash
# Check GPU memory
nvidia-smi -l 1

# Check system memory
free -h

# Check swap usage
swapon --show
```

#### Performance Issues

```bash
# Check GPU utilization
nvidia-smi -l 1

# Check CPU usage
top

# Check disk I/O
iotop
```

### 2. Debug Mode

Enable debug logging:

```bash
# Start with debug logging
./cogniware -c config.json -l debug

# Or modify config
{
  "logging": {
    "level": "debug"
  }
}
```

### 3. Profiling

Enable profiling:

```json
{
  "compute": {
    "enable_profiling": true,
    "profiling_buffer_size": 1000
  }
}
```

## Maintenance

### 1. Regular Maintenance

#### Log Rotation

```bash
# Configure logrotate
sudo tee /etc/logrotate.d/cogniware << EOF
/opt/cogniware/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 cogniware cogniware
}
EOF
```

#### Cache Cleanup

```bash
# Clean old cache files
find /opt/cogniware/cache -type f -mtime +7 -delete

# Clean temporary files
find /opt/cogniware/temp -type f -mtime +1 -delete
```

### 2. Updates

#### Software Updates

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade

# Update CUDA drivers
sudo apt-get install nvidia-driver-xxx

# Rebuild application
cd /path/to/cogniware-engine
git pull
mkdir build && cd build
cmake .. && make -j$(nproc)
sudo make install
```

#### Configuration Updates

```bash
# Backup current config
cp /opt/cogniware/config.json /opt/cogniware/config.json.backup

# Update config
# ... modify config.json ...

# Restart service
sudo systemctl restart cogniware
```

### 3. Backup

#### Configuration Backup

```bash
# Backup configuration
tar -czf cogniware-config-$(date +%Y%m%d).tar.gz /opt/cogniware/config.json

# Backup models
tar -czf cogniware-models-$(date +%Y%m%d).tar.gz /opt/cogniware/models/
```

#### Database Backup

If using external databases:

```bash
# Backup PostgreSQL
pg_dump cogniware > cogniware-db-$(date +%Y%m%d).sql

# Backup Redis
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb cogniware-redis-$(date +%Y%m%d).rdb
```

## Support

### 1. Documentation

- [API Documentation](API_DOCUMENTATION.md)
- [CUDA Virtualization Guide](CUDA_VIRTUALIZATION_GUIDE.md)
- [Performance Tuning Guide](PERFORMANCE_TUNING_GUIDE.md)

### 2. Monitoring Tools

- Prometheus + Grafana for metrics
- ELK Stack for log analysis
- NVIDIA DCGM for GPU monitoring

### 3. Contact

For support and issues:
- GitHub Issues: [Repository Issues](https://github.com/your-org/cogniware-engine/issues)
- Email: support@cogniware.com
- Documentation: [docs.cogniware.com](https://docs.cogniware.com)

---

**Note**: This guide assumes a Linux environment. For Windows deployment, please refer to the Windows-specific deployment guide. 