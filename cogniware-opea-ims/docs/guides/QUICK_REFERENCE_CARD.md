# 🚀 COGNIWARE CORE - QUICK REFERENCE CARD

**Version**: 2.0.0 | **Date**: October 19, 2025 | **Status**: ✅ OPERATIONAL

---

## 🌐 ACCESS

**Web Portal**: http://localhost:8000/login.html

**Credentials**:
- Super Admin: `superadmin` / `Cogniware@2025`
- User: `demousercgw` / `Cogniware@2025`

⚠️ **CHANGE PASSWORDS IMMEDIATELY!**

---

## 🖥️ SERVICES

| Service | Port | URL |
|---------|------|-----|
| Admin | 8099 | http://localhost:8099 |
| Business Protected | 8096 | http://localhost:8096 |
| Production | 8090 | http://localhost:8090 |
| Business | 8095 | http://localhost:8095 |
| Demo | 8080 | http://localhost:8080 |
| Web Server | 8000 | http://localhost:8000 |

---

## 🤖 LLMs AVAILABLE

**Total**: 12 Cogniware models (43.7 GB)

**Interface** (7): Chat, Code, SQL, Summarization, Translation  
**Knowledge** (2): Q&A, RAG  
**Embedding** (2): Semantic search  
**Specialized** (1): Sentiment analysis  

---

## ⚡ PARALLEL EXECUTION

**Patent**: Multi-Context Processing (MCP)

**API**:
```bash
POST /api/nl/process
{
  "instruction": "Your request",
  "strategy": "parallel",
  "num_interface_llms": 2,
  "num_knowledge_llms": 1
}
```

**Strategies**: parallel, interface_only, knowledge_only, sequential, consensus

---

## 📚 DOCUMENTATION

- `README.md` - Main guide
- `QUICK_START_GUIDE.md` - Quick start
- `USER_PERSONAS_GUIDE.md` - 7 user roles
- `COGNIWARE_LLMS_GUIDE.md` - LLM reference
- `PARALLEL_LLM_EXECUTION_GUIDE.md` - Patent system
- `COMPLETE_DELIVERY_SUMMARY.md` - Full delivery

---

## 🛠️ MANAGEMENT

**Start**: `./start_all_services.sh`  
**Stop**: `pkill -f api_server && pkill -f http.server`  
**Logs**: `tail -f logs/*.log`  
**Deploy**: `sudo bash deploy.sh`

---

## 🧪 QUICK TEST

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8099/auth/login \
  -d '{"username":"superadmin","password":"Cogniware@2025"}' \
  | jq -r '.token')

# Test parallel execution
curl -X POST http://localhost:8090/api/nl/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instruction":"test","strategy":"parallel"}' \
  | jq
```

---

## 📞 SUPPORT

**Email**: support@cogniware.com  
**Enterprise**: enterprise@cogniware.com  
**Docs**: See guides in repository

---

**© 2025 Cogniware Incorporated**  
**Patent Pending**: Multi-Context Processing (MCP)

