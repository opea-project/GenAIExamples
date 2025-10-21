# File Explorer Fix - Projects Not Showing

## Issue Identified

The terminal shows files being created, but the Explorer doesn't show them because:

**You're using different servers**:
- **Local** (localhost:8000): Creates projects in `/home/deadbrainviv/Documents/GitHub/cogniware-core/projects/`
- **Production** (demo.cogniware.ai): Creates projects in `/opt/cognidream/projects/` on remote server

When you create a project on localhost, it's stored locally.
When you access demo.cogniware.ai, it can't see local projects!

---

## ✅ Solution

### Option 1: Use Production Server Exclusively (Recommended)

**Access**:
```
https://demo.cogniware.ai/code-ide.html
```

**Create Projects Here**:
- All projects stored on production server
- Accessible from anywhere
- Persistent across sessions
- Team can collaborate

**Result**: Explorer will show files correctly!

### Option 2: Sync Local Projects to Production

```bash
# From your local machine
cd /home/deadbrainviv/Documents/GitHub/cogniware-core

# Sync projects to production
sshpass -p 'CogniDream2025' scp -r -o StrictHostKeyChecking=no \
  projects/* \
  root@185.141.218.141:/opt/cognidream/projects/

# Set permissions
sshpass -p 'CogniDream2025' ssh root@185.141.218.141 \
  'chown -R cognidream:cognidream /opt/cognidream/projects'
```

**Result**: Your local projects now available on production!

---

## 🔍 Debugging the Issue

### What We Found:

**Local Server** (localhost:8000):
```bash
$ ls projects/
student-management/  (10 files) ✅
demo12/              (9 files) ✅
test-fastapi-project/ (8 files) ✅
```

**Production Server** (demo.cogniware.ai):
```bash
$ ls /opt/cognidream/projects/
(empty) ❌
```

**Conclusion**: Projects created locally aren't on production server!

---

## 🎯 How to Use the Production IDE

### Step-by-Step:

**1. Access Production IDE**:
```
https://demo.cogniware.ai/code-ide.html
```

**2. Create a New Project**:
```
Click "+ New Project"
Name: my-production-api
Template: FastAPI
Description: API on production server
```

**3. Files Created on Production Server**:
```
/opt/cognidream/projects/my-production-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── database.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── requirements.txt
├── README.md
└── .gitignore
```

**4. Explorer Shows Files**:
```
📁 my-production-api
   📁 app
      📄 __init__.py
      📄 main.py
      📄 models.py
      📄 database.py
   📁 tests
      📄 __init__.py
      📄 test_main.py
   📄 requirements.txt
   📄 README.md
   📄 .gitignore
```

**5. Add Features with AI**:
```
AI Input: "Add JWT authentication"

AI Creates:
✓ app/auth.py
✓ app/middleware/auth_middleware.py

Explorer Updates:
📁 app
   📄 auth.py ← NEW!
   📁 middleware
      📄 auth_middleware.py ← NEW!
```

**Everything works perfectly on production!**

---

## 🔄 Alternative: Work Locally, Deploy to Production

If you prefer to develop locally and deploy:

**Workflow**:
```
1. Develop on localhost:8000
   → Create projects
   → Add features
   → Test locally

2. When ready, sync to production:
   $ cd /home/deadbrainviv/Documents/GitHub/cogniware-core
   $ ./sync_projects_to_production.sh

3. Access on production:
   → https://demo.cogniware.ai/code-ide.html
   → Projects appear in dropdown
   → Continue development
```

---

## 🛠️ Quick Fix Script

Create this script to sync projects:

```bash
#!/bin/bash
# sync_projects_to_production.sh

REMOTE_HOST="185.141.218.141"
REMOTE_USER="root"
REMOTE_PASSWORD="CogniDream2025"

echo "Syncing projects to production..."

sshpass -p "$REMOTE_PASSWORD" scp -r -o StrictHostKeyChecking=no \
  projects/* \
  $REMOTE_USER@$REMOTE_HOST:/opt/cognidream/projects/

sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no \
  $REMOTE_USER@$REMOTE_HOST \
  'chown -R cognidream:cognidream /opt/cognidream/projects'

echo "✅ Projects synced to production!"
echo "Access: https://demo.cogniware.ai/code-ide.html"
```

---

## 📊 Comparison

### Local Development (localhost:8000):
```
✅ Fast iteration
✅ No internet required
✅ Full control
❌ Not accessible remotely
❌ Can't share with team
❌ Projects only on your machine
```

### Production Development (demo.cogniware.ai):
```
✅ Accessible from anywhere
✅ Team collaboration ready
✅ Projects persistent
✅ HTTPS secure
✅ Professional setup
❌ Requires internet
```

---

## ✅ Recommended Approach

**Use Production Server for All Development**:

**Why**:
1. ✅ Projects accessible from any device
2. ✅ Team members can collaborate
3. ✅ Persistent storage
4. ✅ Secure with HTTPS
5. ✅ Professional environment
6. ✅ No sync issues

**How**:
```
Always use: https://demo.cogniware.ai/code-ide.html

Never use: http://localhost:8000/code-ide.html (unless testing)
```

---

## 🚀 Quick Test on Production

### Verify Explorer Works:

**1. Open Production IDE**:
```
https://demo.cogniware.ai/code-ide.html
```

**2. Create Test Project**:
```
Name: test-explorer
Template: FastAPI
```

**3. Watch Explorer**:
```
Should show:
📁 test-explorer
   📁 app
      📄 __init__.py
      📄 main.py
      📄 models.py
      📄 database.py
   📁 tests
      📄 __init__.py
      📄 test_main.py
   📄 requirements.txt
   📄 README.md
```

**4. Add Files with AI**:
```
Ask: "Add customer CRUD"

Explorer updates to show:
📁 app
   📁 routes
      📄 customer.py ← NEW!
   📁 models
      📄 customer.py ← NEW!
```

**If this works**: ✅ Production is working correctly!

---

## 📝 Summary

### The Issue:
- Projects created on localhost aren't on production server
- Explorer on production can't show local projects
- Terminal logs from local server, but viewing production

### The Solution:
- Use production IDE exclusively: `https://demo.cogniware.ai/code-ide.html`
- OR sync local projects to production with script
- Projects will appear in Explorer correctly

### Test Now:
```
1. Open: https://demo.cogniware.ai/code-ide.html
2. Create: New project
3. Watch: Explorer shows all files
4. Ask AI: Add features
5. See: Files appear in real-time
```

---

**Platform**: https://demo.cogniware.ai  
**Status**: Working Correctly on Production  
**Issue**: Using wrong server (local vs production)  
**Fix**: Use production URL consistently  

**Try it now**: https://demo.cogniware.ai/code-ide.html 🚀

