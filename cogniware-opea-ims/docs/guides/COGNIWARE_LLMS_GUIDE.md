# 🤖 COGNIWARE BUILT-IN LLMs GUIDE

**Status**: ✅ **OPERATIONAL**  
**Total Models**: 12 Built-in LLMs  
**Date**: October 19, 2025

---

## 📋 OVERVIEW

Cogniware Core includes **12 pre-configured, production-ready LLM models** built into the platform's inference engine. These models are optimized for various tasks and ready to use immediately.

### Key Clarifications:

✅ **Built-in Cogniware LLMs** - These 12 models are available in Cogniware's inference engine  
✅ **External Sources** - Ollama and HuggingFace are **sources to download/import** additional models from  
✅ **No Local Ollama Required** - Cogniware uses its own C++ CUDA-accelerated inference engine  

---

## 🎯 AVAILABLE LLM MODELS

### Summary Statistics

| Category | Count | Total Size |
|----------|-------|------------|
| **Interface Models** | 7 | 30.7 GB |
| **Knowledge Models** | 2 | 9.4 GB |
| **Embedding Models** | 2 | 1.6 GB |
| **Specialized Models** | 1 | 0.5 GB |
| **TOTAL** | **12** | **43.7 GB** |

**Total Parameters**: 81.57B

---

## 💬 INTERFACE MODELS (7)

Models for chat, dialogue, and interactive tasks.

### 1. Cogniware Chat 7B
**Model ID**: `cogniware-chat-7b`

- **Parameters**: 7B
- **Size**: 3.5 GB
- **Context Length**: 4,096 tokens
- **Status**: ✅ Ready

**Capabilities**:
- Conversational AI
- General Q&A
- Creative writing
- Code explanation
- Text summarization

**Use Cases**:
- Customer support chatbots
- Virtual assistants
- Interactive dialogues
- Help desk automation

---

### 2. Cogniware Chat 13B
**Model ID**: `cogniware-chat-13b`

- **Parameters**: 13B
- **Size**: 6.5 GB
- **Context Length**: 8,192 tokens
- **Status**: ✅ Ready

**Capabilities**:
- Complex conversations
- Multi-turn dialogues
- Reasoning tasks
- Problem solving
- Educational tutoring

**Use Cases**:
- Enterprise chatbots
- Technical support
- Educational platforms
- Complex query handling

---

### 3. Cogniware Code 7B
**Model ID**: `cogniware-code-7b`

- **Parameters**: 7B
- **Size**: 3.8 GB
- **Context Length**: 16,384 tokens
- **Status**: ✅ Ready

**Supported Languages**: Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, SQL, Shell

**Capabilities**:
- Code generation
- Code completion
- Bug fixing
- Code review
- Documentation generation

**Use Cases**:
- IDE integration
- Code review automation
- Developer productivity
- Programming education

---

### 4. Cogniware Code 13B
**Model ID**: `cogniware-code-13b`

- **Parameters**: 13B
- **Size**: 7.0 GB
- **Context Length**: 16,384 tokens
- **Status**: ✅ Ready

**Supported Languages**: Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, SQL, Shell, Kotlin, Swift

**Capabilities**:
- Complex code generation
- Architecture design
- Algorithm implementation
- Performance optimization
- Security analysis

**Use Cases**:
- Enterprise development
- Complex system design
- Code refactoring
- Technical interviews

---

### 5. Cogniware SQL 7B
**Model ID**: `cogniware-sql-7b`

- **Parameters**: 7B
- **Size**: 3.5 GB
- **Context Length**: 4,096 tokens
- **Status**: ✅ Ready

**Supported Databases**: PostgreSQL, MySQL, SQLite, SQL Server, Oracle, MongoDB, Redis

**Capabilities**:
- Natural language to SQL
- Query optimization
- Schema design
- Database migration
- Query explanation

**Use Cases**:
- Business intelligence
- Database Q&A
- Report generation
- Data analysis

---

### 6. Cogniware Summarization 7B
**Model ID**: `cogniware-summarize-7b`

- **Parameters**: 7B
- **Size**: 3.4 GB
- **Context Length**: 16,384 tokens
- **Status**: ✅ Ready

**Capabilities**:
- Document summarization
- Meeting notes
- Article condensation
- Key points extraction
- Executive summaries

**Use Cases**:
- Document management
- Meeting automation
- News aggregation
- Research paper summaries

---

### 7. Cogniware Translation 7B
**Model ID**: `cogniware-translate-7b`

- **Parameters**: 7B
- **Size**: 4.5 GB
- **Context Length**: 2,048 tokens
- **Status**: ✅ Ready

**Supported Languages**: English, Spanish, French, German, Chinese, Japanese, Korean, Arabic, Portuguese, Russian, Italian, Dutch, Polish, Turkish, Vietnamese, Thai, Hindi, Indonesian (and 100+ more)

**Capabilities**:
- Text translation
- Document translation
- Real-time translation
- Language detection
- Multilingual chat

**Use Cases**:
- International business
- Content localization
- Customer support
- Document translation

---

## 📚 KNOWLEDGE MODELS (2)

Models optimized for Q&A, information retrieval, and RAG.

### 1. Cogniware Knowledge 7B
**Model ID**: `cogniware-knowledge-7b`

- **Parameters**: 7B
- **Size**: 3.2 GB
- **Context Length**: 8,192 tokens
- **Status**: ✅ Ready

**Capabilities**:
- Document Q&A
- Knowledge retrieval
- Fact extraction
- Research assistance
- Information synthesis

**Use Cases**:
- Knowledge bases
- Document search
- Research tools
- FAQ systems

---

### 2. Cogniware Knowledge 13B
**Model ID**: `cogniware-knowledge-13b`

- **Parameters**: 13B
- **Size**: 6.2 GB
- **Context Length**: 16,384 tokens
- **Status**: ✅ Ready

**Capabilities**:
- Advanced RAG (Retrieval-Augmented Generation)
- Multi-document analysis
- Complex queries
- Cross-reference lookup
- Contextual search

**Use Cases**:
- Enterprise knowledge management
- Legal document analysis
- Scientific research
- Compliance documentation

---

## 🔍 EMBEDDING MODELS (2)

Models for semantic search and similarity.

### 1. Cogniware Embeddings Base
**Model ID**: `cogniware-embed-base`

- **Parameters**: 110M
- **Size**: 0.4 GB
- **Dimensions**: 768
- **Context Length**: 512 tokens
- **Status**: ✅ Ready

**Capabilities**:
- Semantic search
- Document similarity
- Clustering
- Recommendation systems
- Duplicate detection

**Use Cases**:
- Search engines
- Content recommendations
- Document clustering
- Plagiarism detection

---

### 2. Cogniware Embeddings Large
**Model ID**: `cogniware-embed-large`

- **Parameters**: 335M
- **Size**: 1.2 GB
- **Dimensions**: 1024
- **Context Length**: 512 tokens
- **Status**: ✅ Ready

**Capabilities**:
- Advanced semantic search
- Multi-lingual similarity
- Fine-grained clustering
- Complex recommendations
- Cross-language search

**Use Cases**:
- Multi-lingual search
- Enterprise knowledge graphs
- Advanced recommendation systems
- Cross-lingual information retrieval

---

## 🎯 SPECIALIZED MODELS (1)

Models for specific tasks.

### 1. Cogniware Sentiment Analysis
**Model ID**: `cogniware-sentiment-base`

- **Parameters**: 125M
- **Size**: 0.5 GB
- **Context Length**: 512 tokens
- **Status**: ✅ Ready

**Sentiment Classes**: Positive, Negative, Neutral  
**Emotion Classes**: Joy, Sadness, Anger, Fear, Surprise, Disgust

**Capabilities**:
- Sentiment classification
- Emotion detection
- Opinion mining
- Review analysis
- Social media monitoring

**Use Cases**:
- Customer feedback analysis
- Social media monitoring
- Brand reputation
- Product reviews

---

## 🔌 API ENDPOINTS

### Get All Cogniware LLMs

```bash
GET /admin/llm/cogniware/all
Authorization: Bearer {token}
```

**Response**:
```json
{
  "success": true,
  "llms": [...],
  "count": 12,
  "summary": {
    "total": 12,
    "interface": 7,
    "knowledge": 2,
    "embedding": 2,
    "specialized": 1,
    "total_size_gb": 43.7,
    "total_parameters": 81.57
  }
}
```

### Get Interface Models

```bash
GET /admin/llm/cogniware/interface
Authorization: Bearer {token}
```

### Get Knowledge Models

```bash
GET /admin/llm/cogniware/knowledge
Authorization: Bearer {token}
```

### Get Embedding Models

```bash
GET /admin/llm/cogniware/embedding
Authorization: Bearer {token}
```

### Get Specialized Models

```bash
GET /admin/llm/cogniware/specialized
Authorization: Bearer {token}
```

### Get Specific Model Details

```bash
GET /admin/llm/cogniware/{model_id}
Authorization: Bearer {token}
```

Example:
```bash
GET /admin/llm/cogniware/cogniware-chat-7b
```

---

## 📥 EXTERNAL SOURCES (For Importing)

Ollama and HuggingFace are **external sources** where you can **download and import** additional models into Cogniware.

### Get External Sources

```bash
GET /admin/llm/sources/external
Authorization: Bearer {token}
```

### Get Ollama Models (For Importing)

```bash
GET /admin/llm/sources/ollama
Authorization: Bearer {token}
```

**Available for Import**:
- Llama 2 (3.8GB)
- Llama 2 13B (7.3GB)
- Mistral 7B (4.1GB)
- Mixtral 8x7B (26GB)
- Code Llama (3.8GB)
- Phi-2 (1.7GB)

### Get HuggingFace Models (For Importing)

```bash
GET /admin/llm/sources/huggingface
Authorization: Bearer {token}
```

**Available for Import**:
- Meta Llama 2 Chat 7B (13GB)
- Meta Llama 2 Chat 13B (26GB)
- Mistral 7B Instruct (14GB)
- Phi-2 (5.5GB)
- FLAN-T5 XXL (11GB)
- StarCoder (15GB)

---

## 💻 USAGE EXAMPLES

### Python Example

```python
import requests

# Login
response = requests.post('http://localhost:8099/auth/login', 
                        json={'username': 'superadmin', 'password': 'Cogniware@2025'})
token = response.json()['token']

# Get all Cogniware LLMs
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8099/admin/llm/cogniware/all', headers=headers)
llms = response.json()

print(f"Total LLMs: {llms['count']}")
print(f"Total Size: {llms['summary']['total_size_gb']} GB")

# List all models
for llm in llms['llms']:
    print(f"- {llm['model_name']} ({llm['parameters']}, {llm['size_gb']}GB)")
```

### cURL Example

```bash
# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Cogniware@2025"}' \
  | jq -r '.token')

# Get all LLMs
curl -s http://localhost:8099/admin/llm/cogniware/all \
  -H "Authorization: Bearer $TOKEN" \
  | jq

# Get only interface models
curl -s http://localhost:8099/admin/llm/cogniware/interface \
  -H "Authorization: Bearer $TOKEN" \
  | jq

# Get specific model details
curl -s http://localhost:8099/admin/llm/cogniware/cogniware-code-7b \
  -H "Authorization: Bearer $TOKEN" \
  | jq
```

### JavaScript Example

```javascript
// Login
const loginResponse = await fetch('http://localhost:8099/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'superadmin', password: 'Cogniware@2025'})
});
const {token} = await loginResponse.json();

// Get all LLMs
const llmsResponse = await fetch('http://localhost:8099/admin/llm/cogniware/all', {
  headers: {'Authorization': `Bearer ${token}`}
});
const llms = await llmsResponse.json();

console.log(`Total LLMs: ${llms.count}`);
llms.llms.forEach(llm => {
  console.log(`${llm.model_name}: ${llm.description}`);
});
```

---

## 🎯 CHOOSING THE RIGHT MODEL

### For Chatbots/Conversations
- **Basic**: `cogniware-chat-7b` (3.5GB)
- **Advanced**: `cogniware-chat-13b` (6.5GB)

### For Code Generation
- **Standard**: `cogniware-code-7b` (3.8GB)
- **Enterprise**: `cogniware-code-13b` (7.0GB)

### For Q&A/Knowledge
- **Basic**: `cogniware-knowledge-7b` (3.2GB)
- **Advanced**: `cogniware-knowledge-13b` (6.2GB)

### For Database Queries
- `cogniware-sql-7b` (3.5GB)

### For Document Summarization
- `cogniware-summarize-7b` (3.4GB)

### For Translation
- `cogniware-translate-7b` (4.5GB)

### For Semantic Search
- **Basic**: `cogniware-embed-base` (0.4GB)
- **Advanced**: `cogniware-embed-large` (1.2GB)

### For Sentiment Analysis
- `cogniware-sentiment-base` (0.5GB)

---

## 🚀 PERFORMANCE CHARACTERISTICS

### Small Models (< 1GB)
- **Size**: 110M - 335M parameters
- **Use**: Quick inference, high throughput
- **Best for**: Embeddings, classification, sentiment

### Medium Models (3-5GB)
- **Size**: 7B parameters
- **Use**: Balanced performance and quality
- **Best for**: Most production use cases

### Large Models (6-7GB)
- **Size**: 13B parameters
- **Use**: Enhanced quality and reasoning
- **Best for**: Complex tasks, enterprise applications

---

## 🔧 TECHNICAL DETAILS

### Inference Engine
- **Engine**: Cogniware C++ CUDA-accelerated inference
- **Optimization**: FP16/INT8 quantization support
- **Hardware**: GPU (NVIDIA CUDA) / CPU fallback
- **Batching**: Dynamic batch processing
- **Streaming**: Real-time token streaming

### Context Length
- **Short**: 512 tokens (embeddings, sentiment)
- **Standard**: 2K-8K tokens (chat, translation)
- **Long**: 16K tokens (code, knowledge, summarization)

### Deployment
- **Location**: `/opt/cogniware-core/models/`
- **Format**: Optimized binary format
- **Loading**: Dynamic model loading/unloading
- **Memory**: Efficient memory management

---

## 📊 COMPARISON WITH EXTERNAL SOURCES

| Feature | Cogniware Built-in | Ollama Import | HuggingFace Import |
|---------|-------------------|---------------|-------------------|
| **Availability** | ✅ Immediate | ⏳ Download required | ⏳ Download required |
| **Optimization** | ✅ Pre-optimized | ⚠️ May need optimization | ⚠️ May need optimization |
| **Inference** | ✅ Native C++/CUDA | ⚠️ External process | ⚠️ External process |
| **Models** | 12 ready-to-use | 6+ available | 6+ available |
| **Size** | 43.7 GB total | Varies | Varies |
| **Setup Time** | 0 minutes | 5-30 minutes | 10-60 minutes |

---

## 🎓 BEST PRACTICES

### Model Selection
1. **Start small** - Begin with 7B models for testing
2. **Scale up** - Move to 13B models for production
3. **Specialize** - Use specialized models for specific tasks
4. **Monitor** - Track performance and adjust

### Performance
1. **GPU Required** - For optimal performance
2. **Batch Requests** - Combine multiple requests
3. **Cache Results** - Cache frequently used results
4. **Monitor Memory** - Watch GPU/RAM usage

### Production
1. **Load Balancing** - Distribute requests across instances
2. **Failover** - Have backup models ready
3. **Monitoring** - Track latency and errors
4. **Scaling** - Scale based on demand

---

## 📞 SUPPORT

For questions about Cogniware LLMs:
- **Documentation**: See this guide
- **API Reference**: Check API endpoints above
- **Support Email**: support@cogniware.com
- **Enterprise Support**: enterprise@cogniware.com

---

## 📝 SUMMARY

✅ **12 Built-in LLMs** ready to use in Cogniware's inference engine  
✅ **4 Categories**: Interface, Knowledge, Embedding, Specialized  
✅ **43.7 GB Total Size** with 81.57B parameters  
✅ **External Sources** (Ollama, HuggingFace) for importing additional models  
✅ **Production Ready** with C++ CUDA-accelerated inference  
✅ **Easy API Access** via REST endpoints  

**All models are ready to use immediately - no additional setup required!**

---

**© 2025 Cogniware Incorporated - All Rights Reserved**

*Last Updated: October 19, 2025*  
*Version: 1.0.0*

