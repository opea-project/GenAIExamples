# 🔐 COGNIWARE CORE - LICENSING & AUTHENTICATION GUIDE

**Company**: Cogniware Incorporated  
**Version**: 1.0.0  
**Last Updated**: October 17, 2025

---

## 🎯 OVERVIEW

Cogniware Core now includes a complete licensing and customer management system with:

✅ **Online & Offline License Validation**  
✅ **Multi-Tenant Organization Management**  
✅ **Role-Based Access Control (RBAC)**  
✅ **API Key & JWT Authentication**  
✅ **Feature-Based Licensing**  
✅ **Usage Tracking & Analytics**  
✅ **Super Admin Portal**  
✅ **Service Management**  
✅ **Audit Logging**  

---

## 🌐 FOUR SERVERS NOW RUNNING

| Server | Port | Purpose | Auth Required |
|--------|------|---------|---------------|
| **Demo** | 8080 | Architecture showcase | ❌ No |
| **Production** | 8090 | Real operations | ❌ No (for now) |
| **Business** | 8095 | Business use cases | ❌ No (legacy) |
| **Admin** | 8099 | Super admin portal | ✅ Yes |
| **Business Protected** | 8096 | Protected business API | ✅ Yes |

---

## 🔑 DEFAULT SUPER ADMIN

**Created automatically on first startup:**

```
Username: superadmin
Password: Cogniware@2025
Role: super_admin
```

⚠️ **IMPORTANT**: Change this password immediately after first login!

---

## 🚀 QUICK START

### 1. Login as Super Admin

```bash
curl -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "superadmin",
    "password": "Cogniware@2025"
  }'
```

**Response**:
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "user_id": "USR-...",
    "username": "superadmin",
    "email": "admin@cogniware.com",
    "full_name": "Super Administrator",
    "role": "super_admin",
    "org_id": "ORG-..."
  },
  "license_key": null
}
```

Save the token - use it for subsequent requests!

### 2. Create a Customer Organization

```bash
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:8099/admin/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "org_name": "Acme Corporation",
    "org_type": "customer",
    "contact_email": "admin@acme.com",
    "contact_phone": "+1-555-1234",
    "address": "123 Main St, Tech City, TC 12345"
  }'
```

**Response**:
```json
{
  "success": true,
  "org_id": "ORG-1729203456789-a1b2c3d4",
  "org_name": "Acme Corporation"
}
```

### 3. Create a License for the Organization

```bash
curl -X POST http://localhost:8099/admin/licenses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "ORG-1729203456789-a1b2c3d4",
    "license_type": "enterprise",
    "features": ["database", "code_generation", "documents", "integration", "workflow"],
    "max_users": 50,
    "max_api_calls": 1000000,
    "days_valid": 365
  }'
```

**Response**:
```json
{
  "success": true,
  "license_key": "A1B2C3D4-E5F6G7H8-I9J0K1L2-M3N4O5P6",
  "org_id": "ORG-1729203456789-a1b2c3d4",
  "license_type": "enterprise",
  "expiry_date": "2026-10-17T..."
}
```

### 4. Create a User in the Organization

```bash
curl -X POST http://localhost:8099/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "ORG-1729203456789-a1b2c3d4",
    "username": "john.doe",
    "email": "john.doe@acme.com",
    "password": "SecurePassword123!",
    "full_name": "John Doe",
    "role": "admin"
  }'
```

### 5. Login as the New User

```bash
curl -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "SecurePassword123!"
  }'
```

### 6. Create an API Key

```bash
USER_TOKEN="user_jwt_token_here"

curl -X POST http://localhost:8099/admin/api-keys \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "permissions": ["read", "write", "admin"],
    "days_valid": 365
  }'
```

**Response**:
```json
{
  "success": true,
  "api_key": "cw_abc123...",
  "expires_at": "2026-10-17T..."
}
```

### 7. Use the API Key to Access Protected Endpoints

```bash
API_KEY="cw_abc123..."

# Access protected business API
curl -X POST http://localhost:8096/api/database/create \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_database",
    "schema": {
      "users": [
        {"name": "id", "type": "INTEGER PRIMARY KEY"},
        {"name": "name", "type": "TEXT"}
      ]
    }
  }'
```

---

## 📊 AUTHENTICATION METHODS

### Method 1: JWT Token (Recommended for User Sessions)

```bash
# Login to get token
TOKEN=$(curl -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john.doe","password":"SecurePassword123!"}' \
  | jq -r '.token')

# Use token
curl http://localhost:8096/status \
  -H "Authorization: Bearer $TOKEN"
```

**JWT Tokens**:
- Valid for 24 hours
- Contain user info and permissions
- Validated cryptographically
- Work offline after initial validation

### Method 2: API Keys (Recommended for Service-to-Service)

```bash
# Use API key
curl http://localhost:8096/api/database/query \
  -H "X-API-Key: cw_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"database":"my_db","question":"Show all users"}'
```

**API Keys**:
- Long-lived (365 days default)
- Can be revoked instantly
- Tracked per-usage
- Tied to specific user and organization

---

## 🏢 ORGANIZATION HIERARCHY

```
Cogniware Incorporated (System Org)
    └── Super Admin User
        ├── Can create organizations
        ├── Can create licenses
        ├── Can manage all users
        └── Can control services

Customer Organization (e.g., Acme Corp)
    ├── License (Enterprise)
    │   ├── Features: database, code_generation, documents...
    │   ├── Max Users: 50
    │   ├── Max API Calls: 1,000,000/month
    │   └── Expires: 2026-10-17
    │
    ├── Admin Users
    │   ├── Can create users in org
    │   ├── Can create API keys
    │   ├── Can view usage stats
    │   └── Cannot modify license
    │
    └── Regular Users
        ├── Can create API keys
        ├── Can use licensed features
        └── Cannot manage users
```

---

## 👥 USER ROLES

| Role | Permissions |
|------|-------------|
| **super_admin** | • Manage all organizations<br>• Create/revoke licenses<br>• Manage all users<br>• Control system services<br>• Access all audit logs |
| **admin** | • Manage users in own organization<br>• Create API keys<br>• View usage statistics<br>• Cannot modify licenses |
| **user** | • Create personal API keys<br>• Use licensed features<br>• View own usage stats |

---

## 📜 LICENSE TYPES

### Basic License
```json
{
  "license_type": "basic",
  "features": ["database"],
  "max_users": 5,
  "max_api_calls": 10000
}
```

### Professional License
```json
{
  "license_type": "professional",
  "features": ["database", "code_generation", "documents"],
  "max_users": 20,
  "max_api_calls": 100000
}
```

### Enterprise License
```json
{
  "license_type": "enterprise",
  "features": ["database", "code_generation", "documents", "integration", "workflow"],
  "max_users": 100,
  "max_api_calls": 1000000
}
```

### Available Features:
- `database` - Database Q&A system
- `code_generation` - Code and project generation
- `documents` - Document processing and search
- `integration` - Data integration and ETL
- `workflow` - Workflow automation
- `gpu_inference` - GPU-accelerated inference (future)
- `multi_llm` - Multi-LLM orchestration (future)

---

## 🔒 ENDPOINT PROTECTION

All protected endpoints automatically validate:

1. **Authentication** - Valid JWT or API key
2. **License Status** - Active and not expired
3. **Feature Access** - License includes required features
4. **Rate Limiting** - Within API call limits
5. **Organization Access** - User belongs to correct org

Example protected endpoint:

```python
@app.route('/api/database/create', methods=['POST'])
@require_license(features=['database'])
def create_database():
    # This endpoint requires:
    # - Valid authentication
    # - Active license
    # - 'database' feature in license
    pass
```

---

## 📊 USAGE TRACKING

### View Organization Usage

```bash
curl http://localhost:8099/admin/usage/ORG-123 \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "org_id": "ORG-123",
  "period_days": 30,
  "total_api_calls": 15234,
  "average_response_time_ms": 45.23,
  "top_endpoints": [
    {"endpoint": "/api/database/query", "count": 5234},
    {"endpoint": "/api/code/project/create", "count": 3421}
  ]
}
```

---

## 🎮 SYSTEM MANAGEMENT (Super Admin Only)

### List Services

```bash
curl http://localhost:8099/admin/system/services \
  -H "Authorization: Bearer $TOKEN"
```

### Control Services

```bash
# Start service
curl -X POST http://localhost:8099/admin/system/services/cogniware-business/start \
  -H "Authorization: Bearer $TOKEN"

# Stop service
curl -X POST http://localhost:8099/admin/system/services/cogniware-business/stop \
  -H "Authorization: Bearer $TOKEN"

# Restart service
curl -X POST http://localhost:8099/admin/system/services/cogniware-business/restart \
  -H "Authorization: Bearer $TOKEN"

# Check status
curl -X POST http://localhost:8099/admin/system/services/cogniware-business/status \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📝 AUDIT LOGGING

All actions are automatically logged:

```bash
curl http://localhost:8099/admin/audit?limit=50 \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "success": true,
  "logs": [
    {
      "id": 1,
      "user_id": "USR-123",
      "org_id": "ORG-456",
      "action": "create_license",
      "resource": "license",
      "details": "{\"license_key\":\"ABC-123\"}",
      "timestamp": "2025-10-17T10:30:00",
      "ip_address": "192.168.1.100"
    }
  ],
  "count": 50
}
```

---

## 🔐 LICENSE VALIDATION (Online & Offline)

### Online Validation
- Checks database for license status
- Validates expiry date
- Checks feature access
- Logs usage

### Offline Validation
- Uses cryptographically signed license keys
- Works without internet
- Validates locally
- Periodic sync when online

**License Key Format**:
```
A1B2C3D4-E5F6G7H8-I9J0K1L2-M3N4O5P6
```

Each segment is cryptographically generated and validated.

---

## 📋 COMPLETE ADMIN API REFERENCE

### Authentication
```
POST /auth/login                    - User login
```

### Organizations (Super Admin)
```
POST   /admin/organizations         - Create organization
GET    /admin/organizations         - List organizations
GET    /admin/organizations/<id>    - Get organization details
```

### Users (Admin)
```
POST   /admin/users                 - Create user
GET    /admin/users/me              - Get current user
```

### Licenses (Super Admin)
```
POST   /admin/licenses              - Create license
GET    /admin/licenses              - List licenses
GET    /admin/licenses/<key>        - Get license details
POST   /admin/licenses/<key>/revoke - Revoke license
```

### API Keys (User/Admin)
```
POST   /admin/api-keys              - Create API key
```

### Usage Stats (Admin)
```
GET    /admin/usage/<org_id>        - Get usage statistics
```

### System Management (Super Admin)
```
GET    /admin/system/services                    - List services
POST   /admin/system/services/<name>/<action>    - Control service
```

### Audit Log (Admin)
```
GET    /admin/audit                 - Get audit log
```

---

## 🧪 COMPLETE TEST WORKFLOW

```bash
#!/bin/bash
# Complete licensing system test

echo "=== TESTING LICENSING SYSTEM ==="

# 1. Login as super admin
echo "1. Super Admin Login:"
TOKEN=$(curl -s -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Cogniware@2025"}' \
  | jq -r '.token')

echo "Token: ${TOKEN:0:20}..."

# 2. Create organization
echo -e "\n2. Create Organization:"
ORG=$(curl -s -X POST http://localhost:8099/admin/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "org_name":"Test Corp",
    "org_type":"customer",
    "contact_email":"test@test.com"
  }' | jq -r '.org_id')

echo "Org ID: $ORG"

# 3. Create license
echo -e "\n3. Create License:"
LICENSE=$(curl -s -X POST http://localhost:8099/admin/licenses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"org_id\":\"$ORG\",
    \"license_type\":\"enterprise\",
    \"features\":[\"database\",\"code_generation\"],
    \"max_users\":10,
    \"max_api_calls\":100000,
    \"days_valid\":365
  }" | jq -r '.license_key')

echo "License: $LICENSE"

# 4. Create user
echo -e "\n4. Create User:"
curl -s -X POST http://localhost:8099/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"org_id\":\"$ORG\",
    \"username\":\"testuser\",
    \"email\":\"test@test.com\",
    \"password\":\"Test123!\",
    \"full_name\":\"Test User\",
    \"role\":\"user\"
  }" | jq '.'

# 5. Login as new user
echo -e "\n5. User Login:"
USER_TOKEN=$(curl -s -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test123!"}' \
  | jq -r '.token')

echo "User Token: ${USER_TOKEN:0:20}..."

# 6. Create API key
echo -e "\n6. Create API Key:"
API_KEY=$(curl -s -X POST http://localhost:8099/admin/api-keys \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"license_key\":\"$LICENSE\",
    \"name\":\"Test Key\",
    \"permissions\":[\"read\",\"write\"]
  }" | jq -r '.api_key')

echo "API Key: ${API_KEY:0:20}..."

# 7. Test protected endpoint with API key
echo -e "\n7. Test Protected Endpoint:"
curl -s -X POST http://localhost:8096/api/database/create \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"test_db",
    "schema":{"users":[{"name":"id","type":"INTEGER PRIMARY KEY"}]}
  }' | jq '.'

echo -e "\n=== TEST COMPLETE ==="
```

---

## 🚨 IMPORTANT SECURITY NOTES

1. **Change Default Password**: Immediately change the super admin password!
2. **Use HTTPS in Production**: Always use HTTPS for API calls
3. **Rotate API Keys**: Regularly rotate API keys
4. **Monitor Audit Logs**: Review audit logs for suspicious activity
5. **Secure JWT Secret**: Set `LICENSE_SECRET` environment variable
6. **Rate Limiting**: Implement rate limiting in production
7. **Database Backups**: Regularly backup licenses.db
8. **Access Control**: Use firewall rules to restrict admin API access

---

## 🎊 SUMMARY

**You now have a complete licensing system with:**

✅ **Multi-tenant architecture**  
✅ **Role-based access control**  
✅ **Feature-based licensing**  
✅ **Online/offline validation**  
✅ **Usage tracking**  
✅ **API key management**  
✅ **JWT authentication**  
✅ **Service management**  
✅ **Audit logging**  
✅ **Super admin portal**  

**Servers**:
- Admin API: http://localhost:8099
- Protected Business API: http://localhost:8096

**Default Super Admin**:
- Username: `superadmin`
- Password: `Cogniware@2025` (CHANGE THIS!)

*© 2025 Cogniware Incorporated - All Rights Reserved - Patent Pending*

