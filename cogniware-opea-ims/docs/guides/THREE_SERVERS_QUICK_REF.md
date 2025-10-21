# 🚀 THREE SERVERS - QUICK REFERENCE

## 🌐 SERVERS

| Server | Port | URL | Purpose |
|--------|------|-----|---------|
| **Demo** | 8080 | http://localhost:8080 | Architecture showcase |
| **Production** | 8090 | http://localhost:8090 | Real hardware ops |
| **Business** | 8095 | http://localhost:8095 | Business use cases |

## ⚡ QUICK TESTS

```bash
# Demo - Show architecture
curl http://localhost:8080/benchmark/validate-15x

# Production - Show real GPU
curl http://localhost:8090/system/gpu | jq '.gpus[0].name'

# Business - Create database
curl -X POST http://localhost:8095/api/database/create \
  -H "Content-Type: application/json" \
  -d '{"name":"test","schema":{"users":[{"name":"id","type":"INTEGER PRIMARY KEY"}]}}'
```

## 📚 DOCUMENTATION

- **ALL_SERVERS_GUIDE.md** - Complete guide for all three
- **BUSINESS_API_GUIDE.md** - Business API details  
- **PRODUCTION_SERVER_LIVE.md** - Production server details

## 📦 POSTMAN

- `api/Cogniware-Core-API.postman_collection.json` - 100+ requests
- `api/Cogniware-Business-API.postman_collection.json` - 30+ requests

## ✅ STATUS

**All three servers**: ✅ Operational  
**Total endpoints**: 70+  
**Real operations**: GPU, files, HTTP, databases, code gen, documents  

**🎉 Cogniware Incorporated - Ready for Business!**
