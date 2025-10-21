# 🚀 START ALL SERVERS - QUICK GUIDE

**Issue**: Protected Business server (8096) keeps reloading  
**Solution**: Start fresh without debug mode

---

## ⚡ QUICK FIX (30 seconds)

### Step 1: Stop All Servers
```bash
pkill -f "python.*api_server"
sleep 2
```

### Step 2: Start All Servers (Production Mode)
```bash
cd /home/deadbrainviv/Documents/GitHub/cogniware-core
source venv/bin/activate

# Start each server in production mode (no auto-reload)
cd python

# Admin API
FLASK_ENV=production python3 api_server_admin.py > ../logs/admin.log 2>&1 &

# Protected Business (with NLP & Document Upload)
FLASK_ENV=production python3 api_server_business_protected.py > ../logs/protected.log 2>&1 &

# Production
FLASK_ENV=production python3 api_server_production.py > ../logs/production.log 2>&1 &

# Business
FLASK_ENV=production python3 api_server_business.py > ../logs/business.log 2>&1 &

# Demo
FLASK_ENV=production python3 api_server.py > ../logs/demo.log 2>&1 &

cd ..
sleep 10
```

### Step 3: Test All Servers
```bash
for port in 8099 8096 8090 8095 8080; do
    curl -s http://localhost:$port/health | jq -r '.status' && echo "Port $port: ✅"
done
```

---

## ✅ OR USE THIS ONE COMMAND:

```bash
cd /home/deadbrainviv/Documents/GitHub/cogniware-core && \
pkill -f "python.*api_server" && sleep 2 && \
source venv/bin/activate && cd python && \
FLASK_ENV=production python3 api_server_admin.py >> ../logs/admin.log 2>&1 & \
FLASK_ENV=production python3 api_server_business_protected.py >> ../logs/protected.log 2>&1 & \
FLASK_ENV=production python3 api_server_production.py >> ../logs/production.log 2>&1 & \
FLASK_ENV=production python3 api_server_business.py >> ../logs/business.log 2>&1 & \
FLASK_ENV=production python3 api_server.py >> ../logs/demo.log 2>&1 & \
cd .. && sleep 10 && \
echo "Testing servers..." && \
for port in 8099 8096 8090 8095 8080; do
    curl -s http://localhost:$port/health >/dev/null 2>&1 && echo "✅ Port $port" || echo "⏳ Port $port"
done
```

---

## 🎯 THEN TRY AGAIN

After servers start:

1. **Refresh** browser (F5)
2. **Logout** and **login** again
3. **Try natural language**:
   ```
   "Take a screenshot of github.com"
   ```
4. **Click** "✨ Process with AI"
5. **Should work!** ✅

---

## 📊 WHAT YOU'LL GET

**Natural Language Input** working in:
- ✅ Code Generation
- ✅ Browser Automation
- ✅ Database (when you add the bar)
- ✅ Documents (when you add the bar)

**Features**:
- Parallel LLM processing (if LLMs installed)
- Intelligent intent recognition
- Automatic parameter extraction
- Visual result displays
- Screenshot inline display

---

## 🎊 ALL FEATURES READY

Once servers are stable:
- ✅ Natural language processing
- ✅ Parallel LLM execution
- ✅ Document upload (PDF, DOCX, XLSX, PPTX)
- ✅ Visual displays
- ✅ Screenshot rendering
- ✅ MCP demonstration

**Run the one-command startup above to fix the issue!** 🚀

*© 2025 Cogniware Incorporated*

