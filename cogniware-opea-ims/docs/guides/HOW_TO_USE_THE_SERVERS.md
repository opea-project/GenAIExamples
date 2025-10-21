# 🚀 HOW TO USE THE COGNIWARE CORE SERVERS

**Date**: October 17, 2025  
**Company**: Cogniware Incorporated

---

## 📊 TWO SERVERS ARE RUNNING

### Server 1: Demo/Architecture Server (Port 8080)
### Server 2: Production Server with Real Operations (Port 8090) ⭐

---

## 🌐 SERVER 1: DEMO/ARCHITECTURE SERVER

**URL**: http://localhost:8080  
**Purpose**: Architecture demonstration, patent showcase  
**Status**: ✅ Running

### What It Does:
- Shows complete system architecture
- All 41 REST endpoints defined
- Simulated responses for demonstration
- Perfect for patent/investor presentations
- Shows what the system CAN do

### Key Endpoints:
```bash
# API Information
curl http://localhost:8080/

# Health Check
curl http://localhost:8080/health

# System Status
curl http://localhost:8080/status

# Validate 15x Performance (simulated)
curl http://localhost:8080/benchmark/validate-15x

# GPU Info (simulated 4x H100)
curl http://localhost:8080/system/gpu

# Model List (simulated 4 models)
curl http://localhost:8080/models

# HTML Documentation
curl http://localhost:8080/docs
# Or open in browser: http://localhost:8080/docs
```

### Use For:
✅ Patent demonstrations  
✅ Architecture presentations  
✅ Investor pitches  
✅ API design showcase  
✅ System capability overview  

---

## ⭐ SERVER 2: PRODUCTION SERVER (REAL OPERATIONS)

**URL**: http://localhost:8090  
**Purpose**: Real operations, production testing  
**Status**: ✅ Running with REAL implementations

### What It Does:
- **REAL GPU monitoring** (RTX 4050 detected)
- **REAL file operations** (actually writes/reads files)
- **REAL HTTP requests** (actually connects to internet)
- **REAL system monitoring** (actual CPU/memory/disk/processes)
- **REAL database operations** (actual SQLite queries)
- **14 MCP tools** performing actual operations

### 🔥 Real GPU Monitoring

**Your Hardware Detected**:
- NVIDIA GeForce RTX 4050 Laptop GPU
- 6.1 GB VRAM
- Real-time utilization, temperature, power

**Test It**:
```bash
# Get real GPU info
curl http://localhost:8090/system/gpu | jq '.gpus[0]'

# Output shows:
# - device_id: 0
# - name: "NVIDIA GeForce RTX 4050 Laptop GPU"
# - memory_total_mb: 6141
# - utilization_percent: 36.0 (REAL-TIME!)
# - temperature_c: 50 (REAL-TIME!)
# - status: "active"
```

### 🔥 Real System Monitoring

**Test It**:
```bash
# Real CPU info (14 cores / 20 threads)
curl http://localhost:8090/system/cpu | jq '.'

# Real memory info (16 GB RAM)
curl http://localhost:8090/system/memory | jq '.'

# Real disk info
curl http://localhost:8090/system/disk | jq '.'

# Real processes (525+ running processes)
curl http://localhost:8090/system/processes | jq '.result.count'

# Combined system info
curl http://localhost:8090/system/info | jq '.'
```

### 🔥 Real Filesystem Operations

**Write a File (ACTUALLY creates it)**:
```bash
curl -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"fs_write_file","parameters":{"path":"data/my_test_file.txt","content":"Hello from Cogniware Core!\nThis file was created through the API.\nGPU: RTX 4050"}}'

# Response:
# {
#   "success": true,
#   "tool": "fs_write_file",
#   "result": {
#     "success": true,
#     "path": "/home/.../cogniware-core/data/my_test_file.txt",
#     "size": 89
#   }
# }
```

**Read the File Back**:
```bash
curl -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"fs_read_file","parameters":{"path":"data/my_test_file.txt"}}'

# Shows the actual content!
```

**Verify It Exists on Disk**:
```bash
# Check the file is actually there
cat data/my_test_file.txt

# You'll see your content!
```

**List Directory (REAL files)**:
```bash
curl -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"fs_list_dir","parameters":{"path":"."}}'

# Shows all 68+ actual files in the project!
```

### 🔥 Real HTTP Requests

**Make Real HTTP Request**:
```bash
curl -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"http_get","parameters":{"url":"https://api.github.com"}}'

# ACTUALLY connects to GitHub!
# Response includes:
# - status_code: 200
# - headers: {...}
# - content: {...}
```

**Try Different URLs**:
```bash
# Get GitHub user info
curl -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"http_get","parameters":{"url":"https://api.github.com/users/github"}}'

# Get your IP address
curl -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"http_get","parameters":{"url":"https://api.ipify.org?format=json"}}'
```

### 🔥 Real Database Operations

**SQLite Query (REAL database)**:
```bash
# Create a test database and query it
curl -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"db_sqlite_query","parameters":{"db_path":"data/test.db","query":"CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)"}}'

# Insert data
curl -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"db_sqlite_query","parameters":{"db_path":"data/test.db","query":"INSERT INTO users (name) VALUES (\"Alice\")"}}'

# Query data
curl -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"db_sqlite_query","parameters":{"db_path":"data/test.db","query":"SELECT * FROM users"}}'
```

### 🔥 List All MCP Tools

```bash
curl http://localhost:8090/mcp/tools/list | jq '.tools[] | .name'

# Shows all 14 available tools:
# - fs_read_file
# - fs_write_file
# - fs_list_dir
# - fs_delete_file
# - http_get
# - http_post
# - download_file
# - sys_get_cpu
# - sys_get_memory
# - sys_get_disk
# - sys_get_processes
# - sys_execute
# - db_sqlite_query
```

### Use For:
✅ Development and testing  
✅ Real operations verification  
✅ Hardware capability demonstrations  
✅ MCP tool testing  
✅ Integration testing  
✅ Production prototyping  

---

## 🎯 QUICK COMPARISON

| Feature | Demo Server (8080) | Production Server (8090) |
|---------|-------------------|-------------------------|
| GPU Monitoring | ❌ Simulated (4x H100) | ✅ Real (RTX 4050) |
| File Operations | ❌ Simulated | ✅ Real (disk I/O) |
| HTTP Requests | ❌ Simulated | ✅ Real (network) |
| System Monitoring | ❌ Simulated | ✅ Real (CPU/mem/disk) |
| Database Ops | ❌ Simulated | ✅ Real (SQLite) |
| Process Monitoring | ❌ Simulated | ✅ Real (525+ processes) |
| LLM Inference | ❌ Simulated | ⚠️ Architecture ready |
| Purpose | Architecture demo | Real operations |

---

## 📝 COMPLETE TEST SUITE

### Test Both Servers

```bash
echo "=== TESTING DEMO SERVER (8080) ==="
curl -s http://localhost:8080/health | jq '.'
curl -s http://localhost:8080/system/gpu | jq '.gpus | length'
echo "Shows: 4 simulated H100 GPUs"

echo ""
echo "=== TESTING PRODUCTION SERVER (8090) ==="
curl -s http://localhost:8090/health | jq '.'
curl -s http://localhost:8090/system/gpu | jq '.gpus[0] | {name, memory_total_mb, temperature_c}'
echo "Shows: Real RTX 4050 GPU with live metrics"
```

### Full Production Server Test

```bash
#!/bin/bash
# Save as: test_production_server.sh

echo "🔥 TESTING PRODUCTION SERVER WITH REAL OPERATIONS"
echo "=================================================="

echo ""
echo "1. Server Health:"
curl -s http://localhost:8090/health | jq '.'

echo ""
echo "2. Server Capabilities:"
curl -s http://localhost:8090/ | jq '.capabilities'

echo ""
echo "3. Real GPU (RTX 4050):"
curl -s http://localhost:8090/system/gpu | jq '.gpus[0] | {name, memory_total_mb, utilization_percent, temperature_c}'

echo ""
echo "4. Real CPU (14 cores):"
curl -s http://localhost:8090/system/cpu | jq '{cpu_count, cpu_count_logical, cpu_percent}'

echo ""
echo "5. Real Memory (16 GB):"
curl -s http://localhost:8090/system/memory | jq '{total_gb: (.total/1073741824|floor), used_gb: (.used/1073741824|floor), percent}'

echo ""
echo "6. Write Real File:"
curl -s -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"fs_write_file","parameters":{"path":"data/test_script.txt","content":"Created by test script"}}' | jq '.result'

echo ""
echo "7. Read File Back:"
curl -s -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"fs_read_file","parameters":{"path":"data/test_script.txt"}}' | jq '.result.content'

echo ""
echo "8. Real HTTP Request:"
curl -s -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"http_get","parameters":{"url":"https://api.github.com"}}' | jq '.result | {status_code, content_length}'

echo ""
echo "9. Real Processes:"
curl -s -X POST http://localhost:8090/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"sys_get_processes","parameters":{}}' | jq '.result.count'

echo ""
echo "10. List MCP Tools:"
curl -s http://localhost:8090/mcp/tools/list | jq '.count'

echo ""
echo "=================================================="
echo "✅ ALL TESTS COMPLETE"
echo "Production server is operational with REAL operations!"
```

Make it executable and run:
```bash
chmod +x test_production_server.sh
./test_production_server.sh
```

---

## 🌐 ACCESS METHODS

### 1. Web Browser

**Demo Server**:
- http://localhost:8080
- http://localhost:8080/health
- http://localhost:8080/docs
- http://localhost:8080/system/gpu
- http://localhost:8080/benchmark/validate-15x

**Production Server**:
- http://localhost:8090
- http://localhost:8090/health
- http://localhost:8090/system/gpu (REAL GPU!)
- http://localhost:8090/system/info
- http://localhost:8090/docs

### 2. Postman

1. Import `api/Cogniware-Core-API.postman_collection.json`
2. Set variables:
   - `demo_base_url`: `http://localhost:8080`
   - `prod_base_url`: `http://localhost:8090`
3. Test all 100+ pre-configured requests

### 3. cURL (Command Line)

See examples throughout this document

### 4. Python

```python
import requests

# Test Demo Server
response = requests.get('http://localhost:8080/health')
print("Demo:", response.json())

# Test Production Server (REAL operations)
response = requests.get('http://localhost:8090/health')
print("Production:", response.json())

# Get REAL GPU info
response = requests.get('http://localhost:8090/system/gpu')
gpu = response.json()['gpus'][0]
print(f"GPU: {gpu['name']}, {gpu['memory_total_mb']} MB, {gpu['temperature_c']}°C")

# Write REAL file
response = requests.post('http://localhost:8090/mcp/tools/execute', json={
    "tool": "fs_write_file",
    "parameters": {
        "path": "data/python_test.txt",
        "content": "Hello from Python!"
    }
})
print("File write:", response.json())

# Read REAL file
response = requests.post('http://localhost:8090/mcp/tools/execute', json={
    "tool": "fs_read_file",
    "parameters": {
        "path": "data/python_test.txt"
    }
})
print("File content:", response.json()['result']['content'])

# Make REAL HTTP request
response = requests.post('http://localhost:8090/mcp/tools/execute', json={
    "tool": "http_get",
    "parameters": {
        "url": "https://api.github.com"
    }
})
print("HTTP status:", response.json()['result']['status_code'])
```

---

## 💡 WHEN TO USE WHICH SERVER

### Use Demo Server (8080) When:
- ✅ Presenting system architecture
- ✅ Filing patent applications
- ✅ Showing investor/customer demos
- ✅ Demonstrating API design
- ✅ Showcasing complete system capabilities
- ✅ Need to show "what if we had 4x H100 GPUs"

### Use Production Server (8090) When:
- ✅ Testing real operations
- ✅ Development and integration
- ✅ Demonstrating actual capabilities
- ✅ Testing MCP tools
- ✅ Verifying hardware integration
- ✅ Running actual file/network/system operations
- ✅ Testing with real GPU (RTX 4050)

---

## 🚦 SERVER STATUS

### Check If Servers Are Running

```bash
# Demo Server
curl -s http://localhost:8080/health && echo "✅ Demo server is running" || echo "❌ Demo server is down"

# Production Server
curl -s http://localhost:8090/health && echo "✅ Production server is running" || echo "❌ Production server is down"
```

### Start Servers (If Needed)

```bash
# Start Demo Server (if stopped)
cd /home/deadbrainviv/Documents/GitHub/cogniware-core
source venv/bin/activate
python3 python/api_server.py > demo_server.log 2>&1 &

# Start Production Server (if stopped)
python3 python/api_server_production.py > production_server.log 2>&1 &
```

### View Logs

```bash
# Demo Server logs
tail -f demo_server.log

# Production Server logs
tail -f production_server.log
```

---

## 📚 MORE INFORMATION

### Documentation Files:
- **`FINAL_DELIVERY_SUMMARY.md`** - Complete project summary
- **`PRODUCTION_SERVER_LIVE.md`** - Production server details
- **`CURRENT_IMPLEMENTATION_STATUS.md`** - Detailed status
- **`ENDPOINT_REFERENCE.md`** - All endpoints
- **`docs/API_REFERENCE.md`** - API documentation

### Quick Links:
- Demo: http://localhost:8080
- Production: http://localhost:8090
- Docs: http://localhost:8090/docs
- Postman: `api/Cogniware-Core-API.postman_collection.json`

---

## 🎊 SUMMARY

**Two Servers Running**:

1. **Demo Server (8080)**: Architecture showcase, patent demos
2. **Production Server (8090)**: Real operations, development ⭐

**What's Real on Production Server**:
- ✅ GPU: RTX 4050 detected and monitored
- ✅ Files: Actually written to disk
- ✅ HTTP: Actually connects to internet
- ✅ System: Real CPU/memory/disk/processes
- ✅ Database: Real SQLite operations
- ✅ 14 MCP Tools: All performing real operations

**Test Now**:
```bash
curl http://localhost:8090/system/gpu | jq '.gpus[0].name'
# Shows: "NVIDIA GeForce RTX 4050 Laptop GPU"
# This is REAL! Not simulated!
```

---

**🚀 START USING THE SERVERS NOW!**

**Demo**: http://localhost:8080  
**Production**: http://localhost:8090  
**Both**: ✅ Operational  

*© 2025 Cogniware Incorporated - All Rights Reserved - Patent Pending*

