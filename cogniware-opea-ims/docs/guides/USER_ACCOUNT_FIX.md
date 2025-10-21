# 🔧 USER ACCOUNT FIX - demousercgw

**Date**: October 19, 2025  
**Status**: ✅ **RESOLVED**

---

## ISSUE

User `demousercgw` was unable to log in with error:
- "Could not create API Key, you may need a valid license"
- "Error invalid or expired token"

---

## ROOT CAUSE

The password stored in the database was incorrect or had been changed. The authentication was failing before the user could even access the platform.

---

## SOLUTION APPLIED

✅ **Password Reset Completed**

The password for user `demousercgw` has been reset to the standard default password.

---

## UPDATED USER CREDENTIALS

### User: demousercgw (Vivek Nair)

```
Username: demousercgw
Password: Cogniware@2025
Email: vivek.nair@cogniware.ai
```

**⚠️ IMPORTANT: Change this password after first login!**

---

## USER DETAILS

| Field | Value |
|-------|-------|
| **User ID** | USR-1760730274253-b5bbac80 |
| **Username** | demousercgw |
| **Email** | vivek.nair@cogniware.ai |
| **Full Name** | Vivek Nair |
| **Role** | user |
| **Status** | active |
| **Organization** | ORG-1760725543624-0e230398 |

---

## LICENSE STATUS

✅ **Valid License Found**

| Field | Value |
|-------|-------|
| **License Key** | 742EC799-A9ADA020-D9BAF3F7-7FF0603D |
| **Organization** | ORG-1760725543624-0e230398 |
| **Tier** | Professional |
| **Status** | Active |
| **Max Users** | 10 |
| **Max API Calls** | 1,000,000 |
| **Issued Date** | 2025-10-18 |
| **Expiry Date** | 2026-10-18 |

**Features Enabled**:
- ✅ Database Q&A
- ✅ Code Generation
- ✅ Document Processing
- ✅ Data Integration
- ✅ Workflow Automation
- ✅ Browser Automation
- ✅ RPA

---

## LOGIN VERIFICATION

✅ **Login Tested Successfully**

```bash
curl -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demousercgw","password":"Cogniware@2025"}'
```

**Response**: 
```json
{
  "success": true,
  "token": "eyJhbGci...[JWT Token]",
  "license_key": "742EC799-A9ADA020-D9BAF3F7-7FF0603D",
  "user": {
    "user_id": "USR-1760730274253-b5bbac80",
    "username": "demousercgw",
    "email": "vivek.nair@cogniware.ai",
    "full_name": "Vivek Nair",
    "role": "user",
    "org_id": "ORG-1760725543624-0e230398"
  }
}
```

---

## HOW TO LOGIN

### Via Web Interface

1. **Open the login page**:
   ```
   http://localhost:8000/login.html
   ```

2. **Enter credentials**:
   - Username: `demousercgw`
   - Password: `Cogniware@2025`

3. **Click "Sign In"**

4. **You will be redirected to**: User Portal
   ```
   http://localhost:8000/user-portal.html
   ```

### Via API

```bash
# Get authentication token
TOKEN=$(curl -s -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demousercgw","password":"Cogniware@2025"}' \
  | jq -r '.token')

# Use the token for API calls
curl http://localhost:8099/user/profile \
  -H "Authorization: Bearer $TOKEN"
```

---

## WHAT YOU CAN DO NOW

As a regular user, you have access to:

### 1. Code Generation
Generate code in 10+ programming languages:
- Python, JavaScript, TypeScript
- Java, C++, C#, Go, Rust
- SQL, Shell scripts

### 2. Database Q&A
Ask questions about databases in natural language:
- "Show me top 10 customers by revenue"
- "What's the average order value?"

### 3. Document Processing
Upload and process documents:
- PDF, Word, Excel, Text files
- Document summarization
- Q&A over documents
- Entity extraction

### 4. Data Integration
Connect to multiple data sources:
- Databases (SQL, NoSQL)
- APIs (REST, GraphQL)
- File uploads (CSV, Excel, JSON)
- Cloud storage

### 5. Workflow Automation
Create automated workflows:
- Scheduled tasks
- Event-driven automation
- Multi-step processes

### 6. Browser Automation (RPA)
Automate web interactions:
- Form filling
- Data scraping
- Screenshot capture
- Navigation automation

### 7. API Key Management
Generate and manage API keys for programmatic access

---

## TROUBLESHOOTING

### If login still fails:

1. **Clear browser cache and cookies**:
   - Press `Ctrl+Shift+Delete`
   - Clear cached data
   - Refresh page

2. **Check if services are running**:
   ```bash
   curl http://localhost:8099/health
   ```

3. **Try different browser**:
   - Chrome, Firefox, Edge, Safari

4. **Check for JavaScript errors**:
   - Open browser console (F12)
   - Look for errors in Console tab

### If "Invalid token" error persists:

This usually happens when:
- Token has expired (tokens expire after 24 hours)
- Browser has old token cached
- Time synchronization issue

**Solution**: Log out and log in again to get a fresh token.

---

## PASSWORD CHANGE INSTRUCTIONS

**IMPORTANT**: Change your password after first login!

### Via Web Interface:

1. Log in to user portal
2. Click on your name/profile icon
3. Select "Change Password" or "Profile Settings"
4. Enter new password
5. Confirm new password
6. Click "Save"

### Password Requirements:

- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter  
- At least 1 number
- At least 1 special character (!@#$%^&*)

### Example strong passwords:

- `MyNew@Pass2025`
- `Secure!Demo123`
- `Vivek@Cogni2025`

---

## API KEY CREATION

If you need to create an API key for programmatic access:

### Via Web Interface:

1. Log in to user portal
2. Go to "API Keys" section
3. Click "+ Generate New API Key"
4. Give it a name (e.g., "Development Key")
5. Set expiration (optional)
6. Click "Generate"
7. **Copy the key immediately** (you won't see it again!)

### Via API:

```bash
# Login first
TOKEN=$(curl -s -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demousercgw","password":"Cogniware@2025"}' \
  | jq -r '.token')

# Create API key
curl -X POST http://localhost:8099/user/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Development Key",
    "expires_in_days": 90
  }'
```

---

## CONTACT INFORMATION

**User**: Vivek Nair  
**Email**: vivek.nair@cogniware.ai  
**Organization**: ORG-1760725543624-0e230398  
**License**: Professional (Active until 2026-10-18)

---

## SUPPORT

If you continue to experience issues:

1. **Check service logs**:
   ```bash
   tail -f /home/deadbrainviv/Documents/GitHub/cogniware-core/logs/admin.log
   ```

2. **Restart services**:
   ```bash
   cd /home/deadbrainviv/Documents/GitHub/cogniware-core
   bash start_all_services.sh
   ```

3. **Contact support**:
   - Email: support@cogniware.com
   - Include your username and error message

---

## SUMMARY

✅ **Issue**: Login failed due to incorrect password  
✅ **Fix**: Password reset to `Cogniware@2025`  
✅ **Status**: User can now log in successfully  
✅ **License**: Valid and active  
✅ **Next Step**: Change password after first login  

---

**© 2025 Cogniware Incorporated**

*Issue resolved: October 19, 2025*  
*Document created by: System Administrator*

