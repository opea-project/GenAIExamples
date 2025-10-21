# ⚡ COGNIWARE CORE - QUICK REFERENCE CARD

**Version 2.0** | **One-Page Reference** | **Print-Friendly**

---

## 🚀 QUICK START

```bash
# Complete installation (one command)
./scripts/00_master_setup.sh

# Then open browser
http://localhost:8000/login.html

# Login
Username: superadmin
Password: Cogniware@2025

⚠️  CHANGE PASSWORD IMMEDIATELY!
```

---

## 📜 ESSENTIAL SCRIPTS

| Script | Purpose | Usage |
|--------|---------|-------|
| **00_master_setup.sh** | Complete setup | `./scripts/00_master_setup.sh` |
| **01_check_requirements.sh** | Check deps | `./scripts/01_check_requirements.sh` |
| **02_install_requirements.sh** | Install deps | `./scripts/02_install_requirements.sh` |
| **03_setup_services.sh** | Setup + start | `./scripts/03_setup_services.sh` |
| **04_start_services.sh** | Start services | `./scripts/04_start_services.sh` |
| **05_stop_services.sh** | Stop services | `./scripts/05_stop_services.sh` |
| **06_verify_deliverables.sh** | Verify all | `./scripts/06_verify_deliverables.sh` |
| **07_build.sh** | Build C++ | `./scripts/07_build.sh` |
| **08_test_build.sh** | Test build | `./scripts/08_test_build.sh` |

---

## 🌐 ACCESS POINTS

### Web Interfaces

| Interface | URL |
|-----------|-----|
| **Login Portal** | http://localhost:8000/login.html |
| **Admin Portal** | http://localhost:8000/admin-portal-enhanced.html |
| **User Portal** | http://localhost:8000/user-portal.html |

### API Servers

| Server | Port | URL |
|--------|------|-----|
| **Admin** | 8099 | http://localhost:8099 |
| **Production** | 8090 | http://localhost:8090 |
| **Business Protected** | 8096 | http://localhost:8096 |
| **Business** | 8095 | http://localhost:8095 |
| **Demo** | 8080 | http://localhost:8080 |
| **Web Server** | 8000 | http://localhost:8000 |

---

## 🔐 DEFAULT CREDENTIALS

### Super Admin
```
Username: superadmin
Password: Cogniware@2025
Role:     super_admin
```

### Demo User
```
Username: demousercgw
Password: Cogniware@2025
Role:     user
```

⚠️ **CHANGE THESE IMMEDIATELY!**

---

## 📚 KEY DOCUMENTS

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Main documentation |
| [DEFAULT_CREDENTIALS.md](DEFAULT_CREDENTIALS.md) | All credentials |
| [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) | Directory layout |
| [docs/INDEX.md](docs/INDEX.md) | Doc index |
| [docs/guides/QUICK_START_GUIDE.md](docs/guides/QUICK_START_GUIDE.md) | Quick start |

---

## 🛠️ DAILY OPERATIONS

```bash
# Start services
./scripts/04_start_services.sh

# Stop services
./scripts/05_stop_services.sh

# Check status
./scripts/06_verify_deliverables.sh

# View logs
tail -f logs/*.log
```

---

## 🔄 SERVICE MANAGEMENT

### With systemd (if installed as root)

```bash
# Status
systemctl status cogniware-admin
systemctl status cogniware-production

# Start
sudo systemctl start cogniware-admin

# Stop
sudo systemctl stop cogniware-admin

# Restart
sudo systemctl restart cogniware-admin

# Logs
journalctl -u cogniware-admin -f
```

### Without systemd

```bash
# Use scripts
./scripts/04_start_services.sh
./scripts/05_stop_services.sh
```

---

## 🧪 TESTING

```bash
# Verify installation
./scripts/06_verify_deliverables.sh

# Test authentication
curl -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Cogniware@2025"}'

# Health check
curl http://localhost:8099/health
```

---

## 📊 REPOSITORY STRUCTURE

```
cogniware-core/
├── README.md                   ⭐ Start here
├── DEFAULT_CREDENTIALS.md      🔐 Credentials
├── REPOSITORY_STRUCTURE.md     📁 Layout
├── scripts/                    📜 20 automation scripts
├── python/                     🐍 Python source
├── ui/                         🎨 User interfaces
├── docs/                       📚 81 documentation files
├── api/                        🔌 Postman collections
├── databases/                  🗄️  SQLite databases
└── misc/                       📂 Archived files
```

---

## 🤖 12 BUILT-IN LLMs

### Interface LLMs (7)
1. Cogniware-Code-Interface-7B
2. Cogniware-NL-Interface-13B
3. Cogniware-Query-Interface-7B
4. Cogniware-Doc-Interface-7B
5. Cogniware-Web-Interface-7B
6. Cogniware-Math-Interface-7B
7. Cogniware-SQL-Interface-7B

### Knowledge LLMs (2)
8. Cogniware-Knowledge-Context-33B
9. Cogniware-Knowledge-Domain-70B

### Embedding LLMs (2)
10. Cogniware-Embed-Fast-384
11. Cogniware-Embed-Accurate-768

### Specialized LLMs (1)
12. Cogniware-Consensus-Validator-13B

---

## 🔄 API EXAMPLES

### Login
```bash
curl -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Cogniware@2025"}'
```

### Natural Language Processing
```bash
curl -X POST http://localhost:8090/api/nl/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Generate Python code to sort a list"}'
```

### Get LLMs
```bash
curl http://localhost:8090/api/llms/available \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔧 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Services won't start | `./scripts/05_stop_services.sh && ./scripts/04_start_services.sh` |
| Port in use | `lsof -i :8099` then `kill -9 <PID>` |
| Can't login | See [DEFAULT_CREDENTIALS.md](DEFAULT_CREDENTIALS.md) emergency access |
| Build fails | Check logs in `logs/` directory |

---

## 📞 SUPPORT

- **Documentation**: [docs/INDEX.md](docs/INDEX.md)
- **Email**: support@cogniware.com
- **Security**: security@cogniware.com
- **Emergency**: +1 (XXX) XXX-XXXX

---

## ✅ POST-INSTALLATION CHECKLIST

- [ ] Change super admin password
- [ ] Change or delete demo user
- [ ] Generate API keys
- [ ] Test all services
- [ ] Review documentation
- [ ] Configure for production (if needed)
- [ ] Enable HTTPS (production)
- [ ] Set up monitoring
- [ ] Configure backups

---

## 🎯 COMMON TASKS

### Create New User
```bash
curl -X POST http://localhost:8099/admin/users/create \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"Pass@123","email":"user@example.com"}'
```

### Generate API Key
```bash
curl -X POST http://localhost:8099/api/keys/generate \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### View Logs
```bash
tail -f logs/admin.log
tail -f logs/production.log
tail -f logs/webserver.log
```

---

## 📈 STATISTICS

- **Servers**: 6 (5 API + 1 Web)
- **LLMs**: 12 built-in
- **API Endpoints**: 110+
- **Documentation**: 81 files
- **Scripts**: 20
- **Use Cases**: 30+
- **User Roles**: 7

---

## 🎊 VERSION HISTORY

**v2.0** (October 21, 2025)
- Complete repository reorganization
- 9 new automation scripts
- Enhanced documentation
- Branding update (msmartcompute → cogniware)
- Professional structure

**v1.0** (August 2024)
- Initial release
- Basic functionality

---

## 📱 MOBILE ACCESS

Web interfaces are mobile-responsive:
- Access from any device
- Responsive design
- Touch-friendly UI

---

## 🔒 SECURITY REMINDERS

1. ⚠️ Change default passwords
2. ⚠️ Use HTTPS in production
3. ⚠️ Rotate API keys regularly
4. ⚠️ Review audit logs
5. ⚠️ Enable firewall rules
6. ⚠️ Set up monitoring

---

## 🌟 QUICK WINS

### 5-Minute Demo
```bash
./scripts/04_start_services.sh
# Open http://localhost:8000/login.html
# Login: superadmin / Cogniware@2025
# Try code generation!
```

### Complete Setup
```bash
./scripts/00_master_setup.sh
# Sit back and relax - it does everything!
```

---

**© 2025 Cogniware Incorporated - All Rights Reserved**

*Quick Reference Card v2.0*  
*Last Updated: October 21, 2025*

---

**💡 TIP**: Bookmark this page for quick reference!

**📄 PRINT**: This card is optimized for printing (single page)

