# ⚡ COGNIWARE CORE - QUICK START

**Status**: ✅ ALL 5 SERVERS RUNNING  
**Admin Portal**: OPEN IN YOUR BROWSER

---

## 🚀 IMMEDIATE ACCESS

### Super Admin Portal (WEB UI) ⭐

**Open Now**:
```
file:///home/deadbrainviv/Documents/GitHub/cogniware-core/ui/admin-portal-enhanced.html
```

**Login**:
- Username: `superadmin`
- Password: `Cogniware@2025`

---

## ✅ 5 SERVERS OPERATIONAL

```
✅ Admin Portal       → http://localhost:8099 🔒
✅ Protected Business → http://localhost:8096 🔒  
✅ Production         → http://localhost:8090
✅ Business           → http://localhost:8095
✅ Demo               → http://localhost:8080
```

---

## 🎯 WHAT TO DO FIRST

### In the Admin Portal:

1. **Login** with superadmin/Cogniware@2025
2. **Click "Organizations"** tab
3. **Create an organization** (e.g., "Acme Corp")
4. **Click "Licenses"** tab
5. **Create a license** for the organization
   - Select organization
   - Choose "Enterprise" type
   - Check all features
   - Set 365 days validity
6. **Save the license key!** (shown in alert)
7. **Click "Users"** tab
8. **Create a user** for the organization
9. **Click "Use Cases"** tab to see 30+ business scenarios

---

## 📋 QUICK COMMANDS

### Management
```bash
# Start all
./start_all_services.sh

# Stop all
pkill -f api_server

# Check status
for port in 8099 8096 8090 8095 8080; do
    curl -s http://localhost:$port/health | jq -r '.status'
done
```

### Test Complete Workflow
```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8099/auth/login \
  -d '{"username":"superadmin","password":"Cogniware@2025"}' \
  | jq -r '.token')

# 2. Create org
curl -X POST http://localhost:8099/admin/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"org_name":"Test Corp","contact_email":"test@test.com"}'

# 3. View organizations
curl http://localhost:8099/admin/organizations \
  -H "Authorization: Bearer $TOKEN" | jq '.count'
```

---

## 📊 FEATURES AVAILABLE NOW

✅ **Database Q&A** - Natural language queries  
✅ **Code Generation** - Generate projects & functions  
✅ **Document Processing** - Create, analyze, search  
✅ **Data Integration** - Import, export, transform  
✅ **Workflow Automation** - Multi-step processes  
✅ **Browser Automation** - Chrome control, screenshots  
✅ **RPA** - Automated workflows  
✅ **Real GPU Monitoring** - NVIDIA RTX 4050  
✅ **Licensing System** - Complete customer management  

---

## 🎊 SUCCESS METRICS

- **Servers**: 5 running ✅
- **Endpoints**: 100+ operational ✅
- **Capabilities**: 60+ features ✅
- **Use Cases**: 30+ documented ✅
- **Users in DB**: 3 (including you!) ✅
- **Admin Portal**: Enhanced with use cases ✅

---

## 📖 DOCUMENTATION

- **COMPLETE_SYSTEM_SUMMARY.md** - Full overview
- **LICENSING_GUIDE.md** - Licensing system
- **USE_CASES_GUIDE.md** - 30+ use cases
- **ALL_SERVICES_RUNNING.md** - Service details

---

## ⚡ ONE-MINUTE START

```bash
# 1. Start services
./start_all_services.sh

# 2. Open admin portal
file:///home/.../ui/admin-portal-enhanced.html

# 3. Login
superadmin / Cogniware@2025

# 4. Create customer, license, user

# 5. Start using!
```

---

**🎉 READY TO USE!**

**Admin Portal**: In your browser  
**All Services**: Running ✅  
**Status**: Production Ready ✅  

*© 2025 Cogniware Incorporated*

