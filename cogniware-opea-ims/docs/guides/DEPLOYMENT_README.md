# 🚀 COGNIWARE CORE - DEPLOYMENT SCRIPTS

**Quick deployment for production servers with automated GPU detection and driver installation**

---

## ⚡ QUICK START

```bash
# One command deployment
sudo bash deploy.sh
```

That's it! The script will handle everything automatically.

---

## 📦 WHAT'S INCLUDED

| File | Size | Description |
|------|------|-------------|
| `deploy.sh` | 21 KB | Automated deployment script |
| `uninstall.sh` | 4.8 KB | Clean uninstallation script |
| `DEPLOYMENT_GUIDE.md` | Detailed | Complete deployment documentation |

---

## ✨ AUTOMATED FEATURES

The deployment script automatically:

✅ Detects your OS (Ubuntu/Debian)  
✅ Detects GPU hardware (NVIDIA/AMD/Intel/none)  
✅ Installs NVIDIA drivers + CUDA (if NVIDIA GPU)  
✅ Installs AMD ROCm (if AMD GPU)  
✅ Installs all base dependencies  
✅ Creates Python virtual environment  
✅ Installs Python packages  
✅ Creates system user (cogniware)  
✅ Sets up directory structure  
✅ Configures 3 systemd services  
✅ Enables auto-start on boot  
✅ Configures firewall rules  
✅ Creates management tool  
✅ Tests all endpoints  

---

## 🎯 WHAT GETS DEPLOYED

### Three Services:

1. **Demo Server** (Port 8080)
   - Architecture demonstration
   - Patent showcase
   - All endpoints defined

2. **Production Server** (Port 8090)
   - Real GPU monitoring
   - Real file operations
   - MCP tools

3. **Business Server** (Port 8095)
   - Database Q&A
   - Code generation
   - Document processing
   - Data integration
   - Workflow automation

### Installation Paths:

- **Application**: `/opt/cogniware-core`
- **Data**: `/var/lib/cogniware`
- **Logs**: `/var/log/cogniware`
- **Config**: `/opt/cogniware-core/config.json`

---

## 🛠️ MANAGEMENT TOOL

After deployment, use the `cogniware` command:

```bash
cogniware start      # Start all services
cogniware stop       # Stop all services
cogniware restart    # Restart all services
cogniware status     # Check service status
cogniware logs       # View logs
cogniware test       # Test endpoints
cogniware enable     # Enable on boot
cogniware disable    # Disable on boot
```

---

## 💻 REQUIREMENTS

### Minimum:
- Ubuntu 20.04+ or Debian 11+
- 4 GB RAM
- 20 GB disk space
- Internet connection

### Recommended:
- Ubuntu 22.04 LTS
- 16+ GB RAM
- 100 GB SSD
- NVIDIA RTX 4000+ GPU

---

## 🔥 GPU SUPPORT

The script automatically detects and configures:

**NVIDIA GPUs**:
- RTX 4000/3000 series
- Tesla V100, P100
- A100, H100
- Installs: Driver 535+, CUDA 12.2, cuDNN

**AMD GPUs**:
- Radeon RX 6000/7000
- MI200 series
- Installs: ROCm, HIP SDK

**Intel/CPU-only**:
- Works without dedicated GPU
- CPU-based operations

---

## 📚 DOCUMENTATION

- **DEPLOYMENT_GUIDE.md** - Complete guide (read this first!)
- **ALL_SERVERS_GUIDE.md** - Server overview
- **BUSINESS_API_GUIDE.md** - Business API details
- **PRODUCTION_SERVER_LIVE.md** - Production server guide

---

## 🧪 TESTING

After deployment:

```bash
# Check services
cogniware status

# Test all endpoints
cogniware test

# Test specific endpoint
curl http://localhost:8090/system/gpu
```

---

## 🗑️ UNINSTALLATION

```bash
sudo bash uninstall.sh
```

The uninstall script will:
- Stop all services
- Remove service files
- Offer to backup data
- Clean installation

---

## 🔧 TROUBLESHOOTING

### Services won't start?
```bash
systemctl status cogniware-demo
journalctl -u cogniware-demo -n 50
```

### GPU not detected?
```bash
lspci | grep -i nvidia
nvidia-smi
```

### Permission errors?
```bash
sudo chown -R cogniware:cogniware /opt/cogniware-core
cogniware restart
```

See `DEPLOYMENT_GUIDE.md` for complete troubleshooting.

---

## 📞 SUPPORT

- Documentation: Check all `*.md` files
- Logs: `/var/log/cogniware/`
- Issues: GitHub issues
- Email: support@cogniware.com

---

## ✅ DEPLOYMENT CHECKLIST

Before deployment:
- [ ] Server meets minimum requirements
- [ ] Have sudo/root access
- [ ] Internet connection available
- [ ] Read DEPLOYMENT_GUIDE.md

Run deployment:
- [ ] `sudo bash deploy.sh`
- [ ] Wait for completion (5-30 minutes)

After deployment:
- [ ] `cogniware status` - Check services
- [ ] `cogniware test` - Test endpoints
- [ ] Configure firewall for external access
- [ ] Setup reverse proxy (if needed)
- [ ] Configure SSL certificates (if needed)

---

## 🎊 EXAMPLE SESSION

```bash
$ sudo bash deploy.sh

╔══════════════════════════════════════════════════════════════╗
║         COGNIWARE CORE AUTOMATED DEPLOYMENT                  ║
╚══════════════════════════════════════════════════════════════╝

[INFO] Detecting Operating System...
[SUCCESS] OS: Ubuntu 22.04

[INFO] Detecting GPU Hardware...
[SUCCESS] NVIDIA GPU detected: NVIDIA GeForce RTX 4050

[INFO] Installing NVIDIA Drivers and CUDA...
[SUCCESS] NVIDIA stack installation complete

... (continues with all steps)

╔══════════════════════════════════════════════════════════════╗
║        COGNIWARE CORE SUCCESSFULLY DEPLOYED!                 ║
╚══════════════════════════════════════════════════════════════╝

Services:
  Demo Server:       http://localhost:8080 ✅
  Production Server: http://localhost:8090 ✅
  Business Server:   http://localhost:8095 ✅

Management: cogniware {start|stop|status|test}
```

---

## 🚀 READY TO DEPLOY

```bash
sudo bash deploy.sh
```

**© 2025 Cogniware Incorporated - All Rights Reserved - Patent Pending**

