# 🚀 COGNIWARE CORE - DEPLOYMENT GUIDE

**Company**: Cogniware Incorporated  
**Version**: 1.0.0  
**Last Updated**: October 17, 2025

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Automated Deployment](#automated-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Service Management](#service-management)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [Uninstallation](#uninstallation)

---

## 🎯 OVERVIEW

The Cogniware Core deployment system provides:

✅ **Automated GPU detection** (NVIDIA, AMD, Intel)  
✅ **Automatic driver installation** (NVIDIA CUDA, AMD ROCm)  
✅ **Custom kernel support** detection  
✅ **Complete dependency management**  
✅ **Systemd service configuration**  
✅ **Automatic service startup on boot**  
✅ **Centralized management tool**  
✅ **Firewall configuration**  

---

## 💻 REQUIREMENTS

### Minimum Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+ (x86_64)
- **RAM**: 4 GB minimum, 16 GB recommended
- **Storage**: 20 GB free space
- **CPU**: 4 cores minimum, 8+ cores recommended
- **Network**: Internet connection for dependencies

### Recommended Requirements

- **OS**: Ubuntu 22.04 LTS
- **RAM**: 32 GB or more
- **Storage**: 100 GB SSD
- **CPU**: AMD Threadripper or Intel Xeon (12+ cores)
- **GPU**: NVIDIA RTX 4000+ series, NVIDIA H100, AMD MI200+

### Supported GPUs

**NVIDIA**:
- RTX 4000 series (4050, 4060, 4070, 4080, 4090)
- RTX 3000 series (3060, 3070, 3080, 3090)
- A100, H100 (Data center)
- Tesla V100, P100

**AMD**:
- Radeon RX 6000/7000 series
- Radeon Pro series
- MI200 series (Data center)

**Intel**:
- Arc series
- Integrated graphics (limited functionality)

---

## 🚀 AUTOMATED DEPLOYMENT

### Quick Start (One Command)

```bash
sudo bash deploy.sh
```

The automated deployment script will:

1. ✅ Detect your operating system
2. ✅ Detect GPU hardware (NVIDIA, AMD, Intel, or none)
3. ✅ Install base dependencies
4. ✅ Install GPU drivers and tools (if needed)
5. ✅ Create system user and directories
6. ✅ Copy application files
7. ✅ Create Python virtual environment
8. ✅ Install Python dependencies
9. ✅ Create systemd services
10. ✅ Configure firewall
11. ✅ Start services
12. ✅ Test endpoints

### Step-by-Step Automated Deployment

```bash
# 1. Download or clone the repository
git clone https://github.com/yourusername/cogniware-core.git
cd cogniware-core

# 2. Make deployment script executable
chmod +x deploy.sh

# 3. Run deployment (requires sudo)
sudo ./deploy.sh

# 4. Wait for completion (5-30 minutes depending on GPU setup)
# The script will show progress for each step

# 5. Verify installation
cogniware status

# 6. Test endpoints
cogniware test
```

### What Gets Installed

**System Packages**:
- build-essential, cmake, git
- python3, python3-pip, python3-venv
- NVIDIA drivers and CUDA (if NVIDIA GPU detected)
- AMD ROCm (if AMD GPU detected)
- Various development libraries

**Python Packages**:
- flask, flask-cors
- requests, psutil
- pynvml, nvidia-ml-py3
- All requirements from requirements.txt

**System Services**:
- cogniware-demo.service (port 8080)
- cogniware-production.service (port 8090)
- cogniware-business.service (port 8095)

**Directories Created**:
- `/opt/cogniware-core` - Installation
- `/var/lib/cogniware` - Data storage
- `/var/log/cogniware` - Logs

**Management Tool**:
- `/usr/local/bin/cogniware` - System-wide command

---

## 🔧 MANUAL DEPLOYMENT

If you prefer manual deployment or need custom configuration:

### 1. Install Base Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential cmake git wget curl \
    python3 python3-pip python3-venv python3-dev \
    pkg-config software-properties-common
```

### 2. Install GPU Drivers (NVIDIA Example)

```bash
# Add NVIDIA repository
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update

# Install driver and CUDA
sudo apt-get install -y nvidia-driver-535 cuda-toolkit-12-2

# Verify
nvidia-smi
```

### 3. Create Installation Structure

```bash
# Create directories
sudo mkdir -p /opt/cogniware-core
sudo mkdir -p /var/lib/cogniware/{databases,projects,documents,models}
sudo mkdir -p /var/log/cogniware

# Create system user
sudo useradd -r -s /bin/bash -d /opt/cogniware-core cogniware

# Copy files
sudo cp -r . /opt/cogniware-core/
```

### 4. Setup Python Environment

```bash
cd /opt/cogniware-core

# Create virtual environment
python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install flask flask-cors requests psutil pynvml
pip install -r requirements.txt  # if exists

# Set permissions
sudo chown -R cogniware:cogniware /opt/cogniware-core
sudo chown -R cogniware:cogniware /var/lib/cogniware
sudo chown -R cogniware:cogniware /var/log/cogniware
```

### 5. Create Systemd Services

Create `/etc/systemd/system/cogniware-demo.service`:

```ini
[Unit]
Description=Cogniware Core - Demo Server
After=network.target

[Service]
Type=simple
User=cogniware
WorkingDirectory=/opt/cogniware-core
Environment="PATH=/opt/cogniware-core/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/cogniware-core/venv/bin/python3 /opt/cogniware-core/python/api_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/cogniware/demo.log
StandardError=append:/var/log/cogniware/demo-error.log

[Install]
WantedBy=multi-user.target
```

Repeat for `cogniware-production.service` and `cogniware-business.service`.

### 6. Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable cogniware-demo.service
sudo systemctl enable cogniware-production.service
sudo systemctl enable cogniware-business.service

sudo systemctl start cogniware-demo.service
sudo systemctl start cogniware-production.service
sudo systemctl start cogniware-business.service
```

---

## 🎮 SERVICE MANAGEMENT

### Using the Management Tool

The `cogniware` command provides easy service management:

```bash
# Start all services
cogniware start

# Stop all services
cogniware stop

# Restart all services
cogniware restart

# Check status
cogniware status

# View logs
cogniware logs cogniware-demo
cogniware logs cogniware-production
cogniware logs cogniware-business

# Enable on boot
cogniware enable

# Disable on boot
cogniware disable

# Test endpoints
cogniware test
```

### Using Systemctl Directly

```bash
# Individual service control
sudo systemctl start cogniware-demo
sudo systemctl stop cogniware-demo
sudo systemctl restart cogniware-demo
sudo systemctl status cogniware-demo

# View logs
sudo journalctl -u cogniware-demo -f
sudo journalctl -u cogniware-production -f
sudo journalctl -u cogniware-business -f

# Check if enabled
systemctl is-enabled cogniware-demo
```

### Log Files

Logs are stored in `/var/log/cogniware/`:

```bash
# View real-time logs
tail -f /var/log/cogniware/demo.log
tail -f /var/log/cogniware/production.log
tail -f /var/log/cogniware/business.log

# View error logs
tail -f /var/log/cogniware/demo-error.log
tail -f /var/log/cogniware/production-error.log
tail -f /var/log/cogniware/business-error.log

# Search logs
grep "ERROR" /var/log/cogniware/*.log
```

---

## ⚙️ CONFIGURATION

### Main Configuration File

Location: `/opt/cogniware-core/config.json`

```json
{
  "installation": {
    "install_dir": "/opt/cogniware-core",
    "data_dir": "/var/lib/cogniware",
    "log_dir": "/var/log/cogniware",
    "user": "cogniware"
  },
  "hardware": {
    "gpu_type": "nvidia",
    "gpu_model": "NVIDIA GeForce RTX 4050"
  },
  "servers": {
    "demo": {
      "host": "0.0.0.0",
      "port": 8080,
      "enabled": true
    },
    "production": {
      "host": "0.0.0.0",
      "port": 8090,
      "enabled": true
    },
    "business": {
      "host": "0.0.0.0",
      "port": 8095,
      "enabled": true
    }
  },
  "logging": {
    "level": "INFO",
    "directory": "/var/log/cogniware"
  }
}
```

### Changing Ports

Edit `/etc/systemd/system/cogniware-*.service` files or modify the Python server files to use different ports.

After changes:
```bash
sudo systemctl daemon-reload
sudo systemctl restart cogniware-demo
```

### Environment Variables

Add to service files under `[Service]` section:

```ini
Environment="CUDA_VISIBLE_DEVICES=0,1"
Environment="LOG_LEVEL=DEBUG"
Environment="MAX_WORKERS=4"
```

---

## 🔍 TROUBLESHOOTING

### Services Won't Start

```bash
# Check service status
systemctl status cogniware-demo

# Check logs
journalctl -u cogniware-demo -n 50

# Check permissions
ls -la /opt/cogniware-core/python/

# Verify Python environment
/opt/cogniware-core/venv/bin/python3 --version
/opt/cogniware-core/venv/bin/pip list
```

### GPU Not Detected

```bash
# Check if GPU is visible
lspci | grep -i vga
lspci | grep -i nvidia

# Check NVIDIA driver
nvidia-smi

# Check CUDA
nvcc --version

# Check Python can access GPU
/opt/cogniware-core/venv/bin/python3 << EOF
import pynvml
pynvml.nvmlInit()
print(f"GPU Count: {pynvml.nvmlDeviceGetCount()}")
EOF
```

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :8080
sudo lsof -i :8090
sudo lsof -i :8095

# Kill process
sudo kill <PID>

# Or change ports in configuration
```

### Permission Denied Errors

```bash
# Fix permissions
sudo chown -R cogniware:cogniware /opt/cogniware-core
sudo chown -R cogniware:cogniware /var/lib/cogniware
sudo chown -R cogniware:cogniware /var/log/cogniware

# Restart services
cogniware restart
```

### Python Dependencies Missing

```bash
# Reinstall dependencies
source /opt/cogniware-core/venv/bin/activate
pip install --upgrade pip
pip install -r /opt/cogniware-core/requirements.txt

# Restart services
cogniware restart
```

---

## 🗑️ UNINSTALLATION

### Automated Uninstallation

```bash
# Make script executable
chmod +x uninstall.sh

# Run uninstall
sudo ./uninstall.sh
```

The uninstall script will:
1. Ask for confirmation
2. Offer to backup data
3. Stop and disable all services
4. Remove service files
5. Remove installation directory
6. Remove logs
7. Optionally remove data directory
8. Optionally remove system user

### Manual Uninstallation

```bash
# Stop services
sudo systemctl stop cogniware-demo cogniware-production cogniware-business

# Disable services
sudo systemctl disable cogniware-demo cogniware-production cogniware-business

# Remove service files
sudo rm /etc/systemd/system/cogniware-*.service
sudo systemctl daemon-reload

# Remove management tool
sudo rm /usr/local/bin/cogniware

# Remove installation
sudo rm -rf /opt/cogniware-core

# Remove logs
sudo rm -rf /var/log/cogniware

# Remove data (if desired)
sudo rm -rf /var/lib/cogniware

# Remove user (if desired)
sudo userdel -r cogniware
```

---

## 🌐 NETWORK ACCESS

### Allow External Access

By default, services bind to `0.0.0.0` (all interfaces).

**Firewall Configuration**:

```bash
# UFW
sudo ufw allow 8080/tcp comment "Cogniware Demo"
sudo ufw allow 8090/tcp comment "Cogniware Production"
sudo ufw allow 8095/tcp comment "Cogniware Business"

# iptables
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8090 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8095 -j ACCEPT
```

### Reverse Proxy with Nginx

```nginx
server {
    listen 80;
    server_name cogniware.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /production/ {
        proxy_pass http://localhost:8090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /business/ {
        proxy_pass http://localhost:8095/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 MONITORING

### System Monitoring

```bash
# CPU and Memory
htop

# GPU monitoring (NVIDIA)
watch -n 1 nvidia-smi

# Disk usage
df -h
du -sh /var/lib/cogniware/*

# Network connections
netstat -tulpn | grep python
```

### Application Monitoring

```bash
# Service status
cogniware status

# Real-time logs
cogniware logs cogniware-production

# Test endpoints
cogniware test

# Detailed endpoint test
curl http://localhost:8090/system/gpu | jq '.'
```

---

## 🚀 PRODUCTION DEPLOYMENT CHECKLIST

- [ ] Server meets minimum requirements
- [ ] OS is updated: `sudo apt-get update && sudo apt-get upgrade`
- [ ] GPU drivers installed and tested
- [ ] Run deployment script: `sudo ./deploy.sh`
- [ ] Verify all services started: `cogniware status`
- [ ] Test all endpoints: `cogniware test`
- [ ] Configure firewall rules
- [ ] Setup reverse proxy (if needed)
- [ ] Configure SSL/TLS certificates
- [ ] Setup monitoring and alerting
- [ ] Create backup strategy
- [ ] Document custom configurations
- [ ] Test failover procedures

---

## 📞 SUPPORT

### Getting Help

1. Check logs: `cogniware logs`
2. Review this guide
3. Check GitHub issues
4. Contact support@cogniware.com

### Reporting Issues

Include:
- OS version: `cat /etc/os-release`
- GPU info: `lspci | grep -i vga`
- Service status: `cogniware status`
- Recent logs: Last 50 lines from error logs
- Configuration: `/opt/cogniware-core/config.json`

---

## ✅ VERIFICATION

After deployment, verify everything is working:

```bash
# 1. Check services
cogniware status

# 2. Test endpoints
curl http://localhost:8080/health
curl http://localhost:8090/health
curl http://localhost:8095/health

# 3. Test GPU (if available)
curl http://localhost:8090/system/gpu | jq '.gpus[0]'

# 4. Test business API
curl -X POST http://localhost:8095/api/database/create \
  -H "Content-Type: application/json" \
  -d '{"name":"test","schema":{"users":[{"name":"id","type":"INTEGER PRIMARY KEY"}]}}'

# 5. Check logs for errors
grep ERROR /var/log/cogniware/*.log
```

---

## 🎊 SUCCESS!

If all checks pass, Cogniware Core is successfully deployed and ready for production use!

**Servers Running**:
- Demo: http://localhost:8080
- Production: http://localhost:8090
- Business: http://localhost:8095

**Management**: `cogniware {start|stop|restart|status|logs|test}`

**Documentation**: 
- `/opt/cogniware-core/docs/`
- `ALL_SERVERS_GUIDE.md`
- `BUSINESS_API_GUIDE.md`

*© 2025 Cogniware Incorporated - All Rights Reserved - Patent Pending*

