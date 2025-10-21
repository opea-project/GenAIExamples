# 🔐 COGNIWARE CORE - DEFAULT CREDENTIALS

**⚠️ CRITICAL SECURITY INFORMATION ⚠️**

**Status**: Production Deployment  
**Last Updated**: October 21, 2025

---

## ⚡ QUICK ACCESS

### Super Administrator

```
Username: superadmin
Password: Cogniware@2025
Role: super_admin
Access Level: FULL SYSTEM ACCESS
```

**⚠️ CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!**

### Regular User (Demo)

```
Username: demousercgw
Password: Cogniware@2025
Role: user
Access Level: Standard user features
```

---

## 🌐 ACCESS POINTS

### Web Interfaces

| Interface | URL | Purpose |
|-----------|-----|---------|
| **Login Portal** | http://localhost:8000/login.html | Main login |
| **Admin Portal** | http://localhost:8000/admin-portal-enhanced.html | Admin dashboard |
| **User Portal** | http://localhost:8000/user-portal.html | User dashboard |

### API Endpoints

| Server | Port | URL | Purpose |
|--------|------|-----|---------|
| **Admin API** | 8099 | http://localhost:8099 | Administration |
| **Production API** | 8090 | http://localhost:8090 | Main API |
| **Business Protected** | 8096 | http://localhost:8096 | Protected business |
| **Business API** | 8095 | http://localhost:8095 | Business operations |
| **Demo API** | 8080 | http://localhost:8080 | Demo/testing |
| **Web Server** | 8000 | http://localhost:8000 | Frontend UI |

---

## 👥 USER ACCOUNTS

### 1. Super Administrator

**Username**: `superadmin`  
**Password**: `Cogniware@2025`  
**Email**: superadmin@cogniware.com  
**Role**: `super_admin`  
**License**: Platform administrator (no expiry)  
**API Key**: Generated on first login

**Capabilities**:
- ✅ Full system administration
- ✅ User management (create, modify, delete)
- ✅ Organization management
- ✅ License management
- ✅ LLM model management
- ✅ System configuration
- ✅ Audit log access
- ✅ All API endpoints
- ✅ Database access
- ✅ Service management

**Default Organization**: Cogniware Incorporated  
**Organization ID**: cogniware-corp

---

### 2. Regular User (Demo)

**Username**: `demousercgw`  
**Password**: `Cogniware@2025`  
**Email**: demouser@cogniware.com  
**Role**: `user`  
**License**: Standard license  
**API Key**: Generated on first login

**Capabilities**:
- ✅ Natural language processing
- ✅ Code generation
- ✅ Document Q&A
- ✅ Browser automation
- ✅ Database queries
- ✅ Use all 12 Cogniware LLMs
- ✅ Parallel LLM execution
- ✅ API key management
- ❌ Admin operations
- ❌ User management
- ❌ System configuration

**Organization**: Demo Organization  
**License Expiry**: December 31, 2025

---

## 🔑 PASSWORD REQUIREMENTS

### Format

- **Minimum length**: 8 characters
- **Required**: At least 1 uppercase letter
- **Required**: At least 1 lowercase letter
- **Required**: At least 1 number
- **Required**: At least 1 special character (@, #, $, %, etc.)

### Valid Example

```
Cogniware@2025
MyP@ssw0rd
Secure#123Pass
```

### Invalid Examples

```
password      (no uppercase, no number, no special char)
PASSWORD123   (no lowercase, no special char)
MyPassword    (no number, no special char)
```

---

## 🔄 CHANGING PASSWORDS

### Via Web Portal

1. Log in at http://localhost:8000/login.html
2. Navigate to **Profile** → **Change Password**
3. Enter current password
4. Enter new password (meeting requirements)
5. Confirm new password
6. Click **Update Password**

### Via API

```bash
curl -X POST http://localhost:8099/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "current_password": "Cogniware@2025",
    "new_password": "NewSecure@2025"
  }'
```

### Via Database (Emergency)

```bash
# Activate virtual environment
source venv/bin/activate

# Run password reset script
python3 python/reset_password.py superadmin NewPassword@2025
```

---

## 🎫 API KEYS

### What are API Keys?

API keys allow programmatic access to Cogniware APIs without username/password authentication.

### Generating API Keys

#### Via Web Portal

1. Log in at http://localhost:8000/login.html
2. Navigate to **Profile** → **API Keys**
3. Click **Generate New API Key**
4. Copy the key immediately (it won't be shown again)
5. Store securely

#### Via API

```bash
# 1. First, login to get JWT token
TOKEN=$(curl -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Cogniware@2025"}' | \
  grep -o '"token":"[^"]*"' | cut -d'"' -f4)

# 2. Generate API key
curl -X POST http://localhost:8099/api/keys/generate \
  -H "Authorization: Bearer $TOKEN"
```

### Using API Keys

```bash
# With API key
curl http://localhost:8090/api/nl/process \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"query":"Generate Python code to sort a list"}'
```

---

## 🏢 ORGANIZATION CREDENTIALS

### Default Organization

**Name**: Cogniware Incorporated  
**ID**: `cogniware-corp`  
**Created**: System initialization  
**License**: Platform license (no expiry)  
**Owner**: superadmin

### Demo Organization

**Name**: Demo Organization  
**ID**: `demo-org`  
**Created**: System initialization  
**License**: Standard license  
**Expires**: December 31, 2025  
**Owner**: demousercgw

---

## 📜 LICENSE INFORMATION

### Platform License (Super Admin)

```
License Key: PLATFORM-ADMIN-LICENSE
Type: Platform Administrator
Expires: Never
Features: ALL
Users: Unlimited
```

### Standard License (Demo User)

```
License Key: DEMO-USER-LICENSE
Type: Standard User
Expires: 2025-12-31
Features: NL Processing, Code Gen, Document Q&A, Browser Automation
Users: 1
```

---

## 🔒 SECURITY BEST PRACTICES

### Immediate Actions Required

1. ⚠️ **CHANGE DEFAULT PASSWORDS**
   - Change `superadmin` password immediately
   - Change `demousercgw` password
   - Use strong, unique passwords

2. ⚠️ **SECURE API KEYS**
   - Never commit API keys to Git
   - Use environment variables
   - Rotate keys regularly

3. ⚠️ **LIMIT SUPER ADMIN ACCESS**
   - Create organization admins instead
   - Use super admin only for system tasks
   - Log all super admin actions

4. ⚠️ **ENABLE LOGGING**
   - All authentication attempts logged
   - Monitor failed logins
   - Review audit logs regularly

### Production Deployment

1. **Use HTTPS**: Never use HTTP in production
2. **Firewall**: Restrict API port access
3. **VPN**: Require VPN for admin access
4. **2FA**: Enable two-factor authentication (if available)
5. **Backup**: Regular database backups
6. **Monitoring**: Set up monitoring and alerts

### Password Management

1. **Password Manager**: Use a password manager
2. **Unique Passwords**: Different for each account
3. **Regular Rotation**: Change passwords every 90 days
4. **No Sharing**: Never share credentials
5. **Secure Storage**: Encrypted storage only

---

## 🆘 EMERGENCY ACCESS

### Locked Out?

If you've lost your super admin password:

1. **Database Reset** (requires server access):

```bash
cd /home/deadbrainviv/Documents/GitHub/cogniware-core
source venv/bin/activate
python3 << 'EOF'
import sqlite3
import hashlib

# Reset super admin password to: Cogniware@2025
password = "Cogniware@2025"
hashed = hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect('databases/licenses.db')
cursor = conn.cursor()
cursor.execute("UPDATE users SET password = ? WHERE username = 'superadmin'", (hashed,))
conn.commit()
print("✅ Password reset to: Cogniware@2025")
EOF
```

2. **Recreate Database** (nuclear option):

```bash
rm databases/licenses.db
python3 python/licensing_service.py --init
```

### Lost API Key?

1. Log in with username/password
2. Revoke old key (if accessible)
3. Generate new API key

### Service Not Responding?

```bash
# Stop all services
./scripts/05_stop_services.sh

# Start all services
./scripts/04_start_services.sh

# Verify
./scripts/06_verify_deliverables.sh
```

---

## 🧪 TESTING CREDENTIALS

### Test Authentication

```bash
# Test super admin login
curl -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "superadmin",
    "password": "Cogniware@2025"
  }'

# Expected: Success with JWT token
```

### Test Regular User

```bash
# Test demo user login
curl -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demousercgw",
    "password": "Cogniware@2025"
  }'

# Expected: Success with JWT token
```

### Test API Key

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Cogniware@2025"}' | \
  grep -o '"token":"[^"]*"' | cut -d'"' -f4)

# Generate API key
API_KEY=$(curl -s -X POST http://localhost:8099/api/keys/generate \
  -H "Authorization: Bearer $TOKEN" | \
  grep -o '"api_key":"[^"]*"' | cut -d'"' -f4)

# Test API key
curl http://localhost:8090/health \
  -H "X-API-Key: $API_KEY"

# Expected: Service healthy response
```

---

## 📊 CREDENTIAL AUDIT LOG

### Logged Events

- ✅ Login attempts (success/failure)
- ✅ Password changes
- ✅ API key generation
- ✅ API key revocation
- ✅ Role changes
- ✅ Account creation
- ✅ Account deletion

### View Audit Log

#### Via Web Portal

1. Log in as super admin
2. Navigate to **Admin** → **Audit Logs**
3. Filter by event type, user, date

#### Via Database

```bash
sqlite3 databases/licenses.db
SELECT * FROM audit_log WHERE event_type = 'login' ORDER BY timestamp DESC LIMIT 10;
```

---

## 🎓 USER ROLES & PERMISSIONS

### Role: super_admin

- ✅ All system administration
- ✅ User management
- ✅ Organization management
- ✅ License management
- ✅ System configuration
- ✅ All API endpoints

### Role: admin

- ✅ Organization administration
- ✅ User management (within org)
- ✅ License viewing
- ✅ Most API endpoints
- ❌ System configuration
- ❌ Create organizations

### Role: user

- ✅ Use platform features
- ✅ Generate API keys
- ✅ NL processing
- ✅ Code generation
- ❌ User management
- ❌ Admin operations
- ❌ System configuration

---

## 📞 SUPPORT

### Security Issues

**Email**: security@cogniware.com  
**Priority**: Critical  
**Response Time**: < 4 hours

### Account Issues

**Email**: support@cogniware.com  
**Response Time**: < 24 hours

### Emergency Contact

**Phone**: +1 (XXX) XXX-XXXX  
**Available**: 24/7 for critical issues

---

## ✅ CHECKLIST

### First Time Setup

- [ ] Log in as superadmin
- [ ] Change super admin password
- [ ] Create organization admin account
- [ ] Change demo user password or delete
- [ ] Generate API keys for automation
- [ ] Review and update security settings
- [ ] Enable HTTPS (production)
- [ ] Configure firewall rules
- [ ] Set up monitoring
- [ ] Document new credentials securely
- [ ] Test all access methods
- [ ] Review audit logs

### Regular Maintenance

- [ ] Rotate passwords (every 90 days)
- [ ] Rotate API keys (every 30 days)
- [ ] Review audit logs (weekly)
- [ ] Check for failed login attempts
- [ ] Update documentation
- [ ] Test backup restoration
- [ ] Review user access levels

---

## 🎊 SUMMARY

### Key Credentials

| Account | Username | Password | Role | Access |
|---------|----------|----------|------|--------|
| **Super Admin** | superadmin | Cogniware@2025 | super_admin | FULL |
| **Demo User** | demousercgw | Cogniware@2025 | user | Standard |

### Key URLs

| Interface | URL |
|-----------|-----|
| **Login** | http://localhost:8000/login.html |
| **Admin API** | http://localhost:8099 |
| **Production API** | http://localhost:8090 |

### First Steps

1. Open http://localhost:8000/login.html
2. Login as `superadmin` / `Cogniware@2025`
3. **IMMEDIATELY change the password**
4. Explore the platform

---

**⚠️ REMEMBER: CHANGE ALL DEFAULT PASSWORDS IMMEDIATELY!**

---

**© 2025 Cogniware Incorporated - All Rights Reserved**

*Security is everyone's responsibility. Protect your credentials.*
