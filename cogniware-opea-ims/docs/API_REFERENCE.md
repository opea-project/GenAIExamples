# Cogniware Core - API Reference

## Python API

### CogniwareAPI

Main entry point for Python integration.

```python
from cogniware_api import CogniwareAPI

api = CogniwareAPI(library_path="./libcore_inference_engine.so")
```

#### Methods

##### initialize()
Initialize the core engine.

**Returns**: `bool` - Success status

```python
if api.initialize():
    print("Initialized successfully")
```

##### shutdown()
Shutdown the core engine.

**Returns**: `bool` - Success status

##### Core Operations

**load_model(config: ModelConfig) -> bool**
```python
config = ModelConfig(
    model_id="llama-7b",
    model_path="/models/llama-7b.bin",
    device_id=0
)
api.core.load_model(config)
```

**run_inference(request: InferenceRequest) -> InferenceResponse**
```python
request = InferenceRequest(
    request_id="test_001",
    model_id="llama-7b",
    prompt="What is AI?",
    max_tokens=100
)
response = api.core.run_inference(request)
```

---

## REST API

### Base URL
```
http://localhost:8080/api/v1
```

### Authentication
```http
Authorization: Bearer <token>
```

### Endpoints

#### Health & Status

**GET /health**
```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": 1697548800
}
```

**GET /status**
```bash
curl http://localhost:8080/status
```

Response:
```json
{
  "server": "running",
  "models_loaded": 4,
  "active_requests": 12
}
```

#### Model Management

**GET /models**
List all loaded models.

```bash
curl http://localhost:8080/models
```

**POST /models**
Load a new model.

```bash
curl -X POST http://localhost:8080/models \
  -H "Content-Type: application/json" \
  -d '{
    "model_path": "/models/llama-7b.bin",
    "device_id": 0
  }'
```

**DELETE /models/:id**
Unload a model.

```bash
curl -X DELETE http://localhost:8080/models/llama-7b
```

#### Inference

**POST /inference**
Run single inference.

```bash
curl -X POST http://localhost:8080/inference \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "llama-7b",
    "prompt": "What is AI?",
    "max_tokens": 100
  }'
```

Response:
```json
{
  "generated_text": "Artificial intelligence is...",
  "tokens_generated": 42,
  "execution_time_ms": 8.5,
  "success": true
}
```

**POST /inference/batch**
Batch inference.

**POST /inference/async**
Async inference (returns job ID).

#### System Monitoring

**GET /system/cpu**
```json
{
  "cores": 96,
  "usage_percent": 45.2
}
```

**GET /system/gpu**
```json
{
  "gpus": [
    {
      "device_id": 0,
      "name": "NVIDIA H100",
      "memory_used_mb": 45000,
      "utilization_percent": 92.5
    }
  ]
}
```

---

## MCP Tools

### Filesystem Tools
- `read_file` - Read file contents
- `write_file` - Write to file
- `list_directory` - List directory contents
- `search_files` - Search for files

### Database Tools
- `db_connect` - Connect to database
- `db_query` - Execute SQL query
- `db_select` - Select data

### Application Tools
- `launch_process` - Launch application
- `kill_process` - Kill process
- `list_processes` - List running processes

---

## Data Structures

### ModelConfig
```python
@dataclass
class ModelConfig:
    model_id: str
    model_type: ModelType
    model_path: str
    device_id: int = 0
    precision: str = "fp16"
    max_batch_size: int = 32
```

### InferenceRequest
```python
@dataclass
class InferenceRequest:
    request_id: str
    model_id: str
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
```

### InferenceResponse
```python
@dataclass
class InferenceResponse:
    request_id: str
    generated_text: str
    tokens_generated: int
    execution_time_ms: float
    success: bool
```

---

*Complete API Reference - Version 1.0*

