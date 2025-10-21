# 🚀 COGNIWARE CORE - QUICK START GUIDE

**Welcome to Cogniware Core!** This guide will get you up and running in minutes.

**Company**: Cogniware Incorporated  
**Version**: 1.0.0  
**Date**: October 2025

---

## 📑 TABLE OF CONTENTS

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Default Credentials](#default-credentials)
4. [Starting the Platform](#starting-the-platform)
5. [Accessing the Platform](#accessing-the-platform)
6. [First Steps](#first-steps)
7. [Common Tasks](#common-tasks)
8. [Troubleshooting](#troubleshooting)

---

## SYSTEM REQUIREMENTS

### Minimum Requirements
- **OS**: Ubuntu 20.04+ / Debian 11+ (Other Linux distributions supported with modifications)
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 50 GB free space
- **Network**: Internet connection for initial setup

### Recommended Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 8+ cores
- **RAM**: 16 GB+
- **GPU**: NVIDIA GPU with CUDA support (optional, for ML features)
- **Storage**: 100 GB+ SSD
- **Network**: High-speed internet

### Supported GPUs
- **NVIDIA**: RTX series, Tesla, A100, H100 (recommended)
- **AMD**: ROCm-compatible GPUs
- **Intel**: Basic support

---

## QUICK INSTALLATION

### Option 1: Automated Deployment (Recommended)

**For Production Deployment with systemd services:**

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/your-org/cogniware-core.git
cd cogniware-core

# Run automated deployment (requires root/sudo)
sudo bash deploy.sh
```

This script will:
- ✅ Detect your operating system and GPU
- ✅ Install all dependencies (CUDA, Python, etc.)
- ✅ Create system user and directories
- ✅ Set up Python virtual environment
- ✅ Install all Python packages
- ✅ Create 5 systemd services
- ✅ Configure firewall rules
- ✅ Start all services automatically
- ✅ Run health checks

**Installation takes 10-30 minutes depending on your system.**

### Option 2: Development Setup (Quick Start)

**For development or testing (no root required):**

```bash
# Clone repository
git clone https://github.com/your-org/cogniware-core.git
cd cogniware-core

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start all services
bash start_all_services.sh
```

**Takes 5-10 minutes.**

---

## DEFAULT CREDENTIALS

### 🔐 Super Administrator Account

**IMPORTANT: These are the default credentials for first login.**

| Field | Value |
|-------|-------|
| **Username** | `superadmin` |
| **Password** | `Cogniware@2025` |
| **Role** | Super Administrator |
| **Access** | Full platform control |

### ⚠️ CRITICAL SECURITY NOTICE

**YOU MUST CHANGE THE DEFAULT PASSWORD IMMEDIATELY AFTER FIRST LOGIN!**

Steps to change password:
1. Log in with default credentials
2. Go to "User Management" or "Profile Settings"
3. Click "Change Password"
4. Use a strong password (minimum 8 characters, with uppercase, lowercase, numbers, and special characters)

### Additional Default Users

During development, you may have created additional users. Check your `databases/licenses.db` for full list.

**Common test accounts:**
- Username: `testuser`, Password: `Test123!`
- Username: `admin`, Password: `Admin123!`

*Note: These test accounts should be deleted in production.*

---

## STARTING THE PLATFORM

### Method 1: Using Management Command (Production)

If you used the automated deployment:

```bash
# Start all services
sudo cogniware start

# Check status
sudo cogniware status

# View logs
sudo cogniware logs

# Test endpoints
sudo cogniware test

# Stop all services
sudo cogniware stop

# Restart services
sudo cogniware restart
```

### Method 2: Using systemd (Production)

```bash
# Start individual services
sudo systemctl start cogniware-admin
sudo systemctl start cogniware-business-protected
sudo systemctl start cogniware-demo
sudo systemctl start cogniware-production
sudo systemctl start cogniware-business

# Check status
sudo systemctl status cogniware-admin

# View logs
sudo journalctl -u cogniware-admin -f

# Enable on boot
sudo systemctl enable cogniware-admin
```

### Method 3: Development Script

```bash
# From repository root
bash start_all_services.sh
```

### Method 4: Manual Start (Development)

```bash
# Activate virtual environment
source venv/bin/activate

# Start each server in separate terminals
cd python
python3 api_server_admin.py          # Port 8099
python3 api_server_business_protected.py  # Port 8096
python3 api_server.py                # Port 8080
python3 api_server_production.py     # Port 8090
python3 api_server_business.py       # Port 8095
```

### Verify Services are Running

```bash
# Check all endpoints
curl http://localhost:8099/health
curl http://localhost:8096/health
curl http://localhost:8080/health
curl http://localhost:8090/health
curl http://localhost:8095/health

# All should return: {"status": "healthy"}
```

---

## ACCESSING THE PLATFORM

### 🌐 Web Interfaces

Once services are running, access the platform via web browser:

#### **Option A: Start with Login Portal (Recommended)**

**URL**: `http://localhost:8099/ui/login.html`  
or `http://your-server-ip:8099/ui/login.html`

This is the unified login portal that will automatically redirect you to the appropriate dashboard based on your role.

#### **Option B: Direct Access to Portals**

**Super Admin Portal**:
- **URL**: `http://localhost:8099/ui/admin-portal-enhanced.html`
- **For**: Super administrators only
- **Features**: Full platform control, organization management, licensing, LLM models

**Admin Dashboard**:
- **URL**: `http://localhost:8099/ui/admin-dashboard.html`
- **For**: Organization administrators
- **Features**: User management, organization settings, analytics

**User Portal**:
- **URL**: `http://localhost:8099/ui/user-portal.html`
- **For**: Regular users
- **Features**: All 8 AI capabilities (code gen, database Q&A, document processing, etc.)

### 📡 API Endpoints

**Base URLs**:
- **Admin API**: `http://localhost:8099`
- **Business Protected**: `http://localhost:8096`
- **Demo Server**: `http://localhost:8080`
- **Production Server**: `http://localhost:8090`
- **Business Server**: `http://localhost:8095`

**API Documentation**:
- OpenAPI Spec: `api/openapi.yaml`
- Postman Collections:
  - `api/Cogniware-Core-API.postman_collection.json`
  - `api/Cogniware-Business-API.postman_collection.json`

---

## FIRST STEPS

### Step 1: Login as Super Admin

1. Open browser: `http://localhost:8099/ui/login.html`
2. Enter credentials:
   - Username: `superadmin`
   - Password: `Cogniware@2025`
3. Click "Sign In"

### Step 2: Change Default Password

1. After login, go to "User Management" or profile settings
2. Click "Change Password"
3. Enter new strong password
4. Save changes
5. **Write down your new password securely!**

### Step 3: Create Your First Organization

1. Click "Organizations" tab
2. Click "+ Create Organization"
3. Fill in details:
   ```
   Name: Acme Corporation
   Contact Email: admin@acme.com
   Industry: Technology
   Size: 50-100 employees
   ```
4. Click "Create"

### Step 4: Issue a License

1. Go to "Licenses" tab
2. Click "+ Issue License"
3. Select the organization you created
4. Choose license tier:
   - **Starter**: Basic features, 100 API calls/day
   - **Professional**: All features, 1000 API calls/day
   - **Enterprise**: Custom features, 10,000+ API calls/day
5. Enable features you want:
   - ✅ Database Q&A
   - ✅ Code Generation
   - ✅ Document Processing
   - ✅ Data Integration
   - ✅ Workflow Automation
   - ✅ Browser Automation
   - ✅ Custom Training
   - ✅ Priority Support
6. Set expiration date (e.g., 1 year from now)
7. Click "Issue License"

### Step 5: Create an Admin User for the Organization

1. Go to "User Management" tab
2. Click "+ Create User"
3. Fill in details:
   ```
   Username: acme_admin
   Email: admin@acme.com
   Password: (generate secure password)
   Role: admin
   Organization: Acme Corporation
   ```
4. Click "Create User"
5. **Securely send credentials to the customer**

### Step 6: (Optional) Download AI Models

1. Go to "LLM Models" tab
2. Click "+ Interface LLM" or "+ Knowledge LLM"
3. Choose source (Ollama or HuggingFace)
4. Select model (e.g., "Llama 2 Chat 7B")
5. Click "Create & Download"
6. Monitor download progress
7. Model will be available when status = "Ready"

### Step 7: Test the Platform

1. **Test API**:
   ```bash
   # Get authentication token
   curl -X POST http://localhost:8099/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"superadmin","password":"YOUR_NEW_PASSWORD"}'
   
   # Use token for API calls
   TOKEN="your_token_here"
   
   curl http://localhost:8099/admin/organizations \
     -H "Authorization: Bearer $TOKEN"
   ```

2. **Test User Portal**:
   - Log out
   - Log in as the user you created
   - Try generating code or asking database questions

---

## COMMON TASKS

### Creating a New Customer Organization

```bash
# As Super Admin in the UI
1. Organizations → + Create Organization
2. Fill in details
3. Licenses → + Issue License → Select organization
4. User Management → + Create User → Select organization, Role: admin
5. Provide credentials to customer
```

### Adding Users to an Organization

```bash
# As Organization Admin
1. Login to Admin Dashboard
2. User Management → + Create User
3. Fill in details (automatically assigned to your org)
4. Provide credentials to new user
```

### Checking Platform Health

```bash
# Command line
sudo cogniware status
sudo cogniware test

# Or visit health endpoints
curl http://localhost:8099/health
curl http://localhost:8096/health
curl http://localhost:8080/health
curl http://localhost:8090/health
curl http://localhost:8095/health
```

### Viewing Logs

```bash
# Using management command
sudo cogniware logs                    # Default: demo server
sudo cogniware logs cogniware-admin    # Specific server

# Using systemd
sudo journalctl -u cogniware-admin -f
sudo journalctl -u cogniware-production -f

# Log files (production deployment)
tail -f /var/log/cogniware/admin.log
tail -f /var/log/cogniware/production.log

# Log files (development)
tail -f logs/admin.log
tail -f logs/production.log
```

### Restarting Services

```bash
# All services
sudo cogniware restart

# Individual service
sudo systemctl restart cogniware-admin
```

### Upgrading the Platform

```bash
# Stop services
sudo cogniware stop

# Pull latest code
cd /opt/cogniware-core  # or your installation directory
sudo git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Start services
sudo cogniware start

# Verify
sudo cogniware test
```

### Backup and Restore

```bash
# Backup databases
sudo cp -r /var/lib/cogniware/databases /backup/location/databases-$(date +%Y%m%d)

# Backup configuration
sudo cp /opt/cogniware-core/config.json /backup/location/

# Restore
sudo cp -r /backup/location/databases-20251019/* /var/lib/cogniware/databases/
sudo systemctl restart cogniware-admin
```

---

## TROUBLESHOOTING

### Issue: Services Won't Start

**Symptoms**: `systemctl start cogniware-admin` fails

**Solutions**:
```bash
# Check service status
sudo systemctl status cogniware-admin

# Check logs for errors
sudo journalctl -u cogniware-admin -n 50

# Common fixes:
# 1. Check Python path
which python3

# 2. Check virtual environment
ls -la /opt/cogniware-core/venv/

# 3. Reinstall dependencies
cd /opt/cogniware-core
source venv/bin/activate
pip install -r requirements.txt

# 4. Check ports are not in use
sudo netstat -tulpn | grep 8099

# 5. Check file permissions
sudo chown -R cogniware:cogniware /opt/cogniware-core
```

### Issue: Cannot Access Web Interface

**Symptoms**: Browser shows "Connection refused"

**Solutions**:
```bash
# 1. Check services are running
sudo cogniware status

# 2. Check firewall
sudo ufw status
sudo ufw allow 8099/tcp

# 3. Check if binding to correct interface
# Edit /opt/cogniware-core/config.json
# Change "host": "127.0.0.1" to "host": "0.0.0.0"

# 4. Check from server itself
curl http://localhost:8099/health

# 5. Check from network
curl http://YOUR_SERVER_IP:8099/health
```

### Issue: Login Fails

**Symptoms**: "Invalid username or password"

**Solutions**:
```bash
# 1. Verify database exists
ls -la /var/lib/cogniware/databases/licenses.db

# 2. Reset super admin password (if needed)
cd /opt/cogniware-core
source venv/bin/activate
python3 python/licensing_service.py --reset-admin

# 3. Check database permissions
sudo chown cogniware:cogniware /var/lib/cogniware/databases/licenses.db

# 4. Check API server logs
sudo journalctl -u cogniware-admin -f
```

### Issue: High CPU/Memory Usage

**Solutions**:
```bash
# Check resource usage
top
htop

# Check specific processes
ps aux | grep python

# View detailed service stats
systemctl status cogniware-production

# Restart high-usage service
sudo systemctl restart cogniware-production

# Check for memory leaks in logs
sudo journalctl -u cogniware-production | grep -i "memory\|leak"
```

### Issue: API Requests Failing

**Symptoms**: 401, 403, or 500 errors

**Solutions**:
```bash
# 1. Check token is valid
# Re-login to get new token

# 2. Check license is active
# Login to Super Admin portal → Licenses

# 3. Check API server logs
sudo journalctl -u cogniware-admin -n 100

# 4. Verify endpoint exists
curl http://localhost:8099/health

# 5. Check request format
# Make sure Content-Type: application/json header is set
```

### Issue: GPU Not Detected

**Symptoms**: GPU features not working

**Solutions**:
```bash
# Check NVIDIA GPU
nvidia-smi

# If command not found, install drivers
sudo apt update
sudo apt install nvidia-driver-535

# Reboot
sudo reboot

# Verify after reboot
nvidia-smi

# Check CUDA installation
nvcc --version

# Reinstall CUDA toolkit if needed
sudo apt install cuda-toolkit-12-2
```

### Issue: Port Already in Use

**Symptoms**: "Address already in use"

**Solutions**:
```bash
# Find what's using the port
sudo netstat -tulpn | grep 8099

# Kill the process
sudo kill -9 <PID>

# Or change port in config
vim /opt/cogniware-core/config.json
# Change port number, save, and restart services
```

---

## GETTING HELP

### Documentation

- **User Personas Guide**: `/USER_PERSONAS_GUIDE.md`
- **API Reference**: `/api/openapi.yaml`
- **Deployment Guide**: `/DEPLOYMENT_GUIDE.md`
- **Use Cases**: `/USE_CASES_GUIDE.md`

### Support Channels

- **Email**: support@cogniware.com
- **GitHub Issues**: https://github.com/your-org/cogniware-core/issues
- **Community Forum**: https://community.cogniware.com
- **Enterprise Support**: enterprise@cogniware.com (24/7 for Enterprise customers)

### Before Contacting Support

Please gather this information:

```bash
# System information
uname -a
cat /etc/os-release

# Service status
sudo cogniware status

# Recent logs (last 50 lines)
sudo journalctl -u cogniware-admin -n 50

# Configuration
cat /opt/cogniware-core/config.json

# Python version
python3 --version

# Pip packages
pip list
```

---

## NEXT STEPS

After completing the Quick Start:

1. **Review User Personas Guide** - Understand different user roles
2. **Explore Use Cases** - See what the platform can do
3. **Read API Documentation** - Integrate with your applications
4. **Try Examples** - Check `/examples/` directory
5. **Configure Security** - Set up SSL/TLS, firewall rules
6. **Set Up Monitoring** - Configure logging and alerts
7. **Plan for Scale** - Review capacity planning guide

---

## QUICK REFERENCE

### Default Credentials
```
Username: superadmin
Password: Cogniware@2025
⚠️ CHANGE IMMEDIATELY!
```

### Service Ports
```
8099 - Admin Server (Protected)
8096 - Business Protected
8080 - Demo Server
8090 - Production Server (GPU)
8095 - Business Server (Legacy)
```

### Management Commands
```bash
sudo cogniware start     # Start all services
sudo cogniware stop      # Stop all services
sudo cogniware restart   # Restart all services
sudo cogniware status    # Check status
sudo cogniware logs      # View logs
sudo cogniware test      # Test endpoints
```

### Key Directories
```
/opt/cogniware-core/          # Installation
/var/lib/cogniware/           # Data
/var/log/cogniware/           # Logs
/opt/cogniware-core/ui/       # Web interfaces
```

### Important Files
```
/opt/cogniware-core/config.json                    # Configuration
/var/lib/cogniware/databases/licenses.db           # License database
/etc/systemd/system/cogniware-*.service            # Service definitions
/usr/local/bin/cogniware                           # Management script
```

---

## SECURITY CHECKLIST

Before going to production:

- [ ] Changed default super admin password
- [ ] Removed or disabled test accounts
- [ ] Configured firewall (UFW/iptables)
- [ ] Set up SSL/TLS certificates
- [ ] Enabled HTTPS only
- [ ] Configured proper file permissions
- [ ] Set up regular database backups
- [ ] Enabled audit logging
- [ ] Configured rate limiting
- [ ] Set up monitoring and alerts
- [ ] Reviewed and updated security policies
- [ ] Documented admin procedures

---

**🎉 Congratulations!** You're now ready to use Cogniware Core!

For detailed information about features and capabilities, see:
- **USER_PERSONAS_GUIDE.md** - Complete guide to all user roles
- **USE_CASES_GUIDE.md** - 30+ business use cases
- **DEPLOYMENT_GUIDE.md** - Comprehensive deployment information

---

**© 2025 Cogniware Incorporated - All Rights Reserved**

*Need help? Contact support@cogniware.com*

---

*Last Updated: October 2025*  
*Document Version: 1.0.0*  
*Platform Version: Production Ready*
