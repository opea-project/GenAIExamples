# MSmartCompute Platform API Documentation

## Overview

The MSmartCompute Platform provides a comprehensive REST API for high-performance machine learning operations, including enhanced CUDA kernels, virtualization, and CogniDream integration.

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

The API supports API key authentication. Include your API key in the request headers:

```
Authorization: Bearer YOUR_API_KEY
```

## Response Format

All API responses follow this standard format:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Server Error |

## Endpoints

### Health Check

#### GET /health

Check the health status of the platform.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "uptime": 3600,
  "gpu_status": "available",
  "memory_usage": 0.65
}
```

### Model Management

#### POST /models

Load a model into the platform.

**Request Body:**
```json
{
  "model_id": "gpt-3.5-turbo",
  "model_type": "transformer",
  "model_path": "/path/to/model.bin",
  "max_batch_size": 32,
  "max_sequence_length": 512,
  "enable_quantization": false,
  "enable_tensor_cores": true,
  "enable_mixed_precision": true,
  "parameters": {
    "vocab_size": 50257,
    "hidden_size": 768,
    "num_layers": 12,
    "num_heads": 12
  }
}
```

**Response:**
```json
{
  "success": true,
  "model_id": "gpt-3.5-turbo",
  "message": "Model loaded successfully",
  "memory_allocated": 1073741824,
  "load_time": 2.5
}
```

#### GET /models

List all loaded models.

**Response:**
```json
{
  "success": true,
  "models": [
    {
      "model_id": "gpt-3.5-turbo",
      "model_type": "transformer",
      "status": "loaded",
      "memory_usage": 1073741824,
      "load_time": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### DELETE /models/{model_id}

Unload a model from the platform.

**Response:**
```json
{
  "success": true,
  "model_id": "gpt-3.5-turbo",
  "message": "Model unloaded successfully"
}
```

### Inference

#### POST /inference

Execute synchronous inference.

**Request Body:**
```json
{
  "model_id": "gpt-3.5-turbo",
  "input_data": [
    [0.1, 0.2, 0.3, ...],
    [0.4, 0.5, 0.6, ...]
  ],
  "batch_size": 2,
  "sequence_length": 512,
  "data_type": "float32",
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 100
  }
}
```

**Response:**
```json
{
  "success": true,
  "request_id": "req_1704067200_1",
  "output_data": [
    [0.8, 0.9, 0.1, ...],
    [0.2, 0.3, 0.7, ...]
  ],
  "inference_time": 0.125,
  "tokens_generated": 100,
  "memory_used": 536870912
}
```

#### POST /inference/async

Queue asynchronous inference.

**Request Body:** Same as synchronous inference.

**Response:**
```json
{
  "success": true,
  "request_id": "req_1704067200_2",
  "status": "queued",
  "estimated_completion": "2024-01-01T00:00:30Z"
}
```

#### GET /inference/{request_id}

Get the result of an asynchronous inference request.

**Response:**
```json
{
  "success": true,
  "request_id": "req_1704067200_2",
  "status": "completed",
  "output_data": [
    [0.8, 0.9, 0.1, ...],
    [0.2, 0.3, 0.7, ...]
  ],
  "inference_time": 0.125,
  "completion_time": "2024-01-01T00:00:30Z"
}
```

### Training

#### POST /training

Execute synchronous training.

**Request Body:**
```json
{
  "model_id": "gpt-3.5-turbo",
  "training_data": [
    [0.1, 0.2, 0.3, ...],
    [0.4, 0.5, 0.6, ...]
  ],
  "labels": [
    [1, 0, 0, ...],
    [0, 1, 0, ...]
  ],
  "epochs": 10,
  "learning_rate": 0.001,
  "optimizer": "adam",
  "loss_function": "cross_entropy",
  "hyperparameters": {
    "batch_size": 32,
    "gradient_clip_norm": 1.0,
    "weight_decay": 0.01
  }
}
```

**Response:**
```json
{
  "success": true,
  "request_id": "req_1704067200_3",
  "final_loss": 0.123,
  "loss_history": [0.5, 0.3, 0.2, 0.15, 0.13, ...],
  "training_time": 120.5,
  "epochs_completed": 10,
  "model_updated": true
}
```

#### POST /training/async

Queue asynchronous training.

**Request Body:** Same as synchronous training.

**Response:**
```json
{
  "success": true,
  "request_id": "req_1704067200_4",
  "status": "queued",
  "estimated_completion": "2024-01-01T00:02:00Z"
}
```

#### GET /training/{request_id}

Get the result of an asynchronous training request.

**Response:**
```json
{
  "success": true,
  "request_id": "req_1704067200_4",
  "status": "completed",
  "final_loss": 0.123,
  "loss_history": [0.5, 0.3, 0.2, 0.15, 0.13, ...],
  "training_time": 120.5,
  "completion_time": "2024-01-01T00:02:00Z"
}
```

### Session Management

#### POST /sessions

Create a new session.

**Request Body:**
```json
{
  "user_id": "user123",
  "model_id": "gpt-3.5-turbo"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "user123_123456",
  "user_id": "user123",
  "model_id": "gpt-3.5-turbo",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-01T01:00:00Z"
}
```

#### DELETE /sessions/{session_id}

End a session.

**Response:**
```json
{
  "success": true,
  "session_id": "user123_123456",
  "message": "Session ended successfully"
}
```

### Performance Monitoring

#### GET /metrics

Get current performance metrics.

**Response:**
```json
{
  "success": true,
  "metrics": {
    "gpu_utilization": 0.75,
    "memory_utilization": 0.65,
    "temperature": 65.0,
    "power_usage": 180.5,
    "throughput": 1250.0,
    "latency": 0.008,
    "active_requests": 5,
    "queued_requests": 2,
    "total_requests": 10000,
    "successful_requests": 9950,
    "failed_requests": 50
  }
}
```

#### GET /metrics/history

Get historical performance metrics.

**Query Parameters:**
- `start_time`: Start timestamp (ISO 8601)
- `end_time`: End timestamp (ISO 8601)
- `interval`: Aggregation interval in seconds (default: 60)

**Response:**
```json
{
  "success": true,
  "history": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "gpu_utilization": 0.75,
      "memory_utilization": 0.65,
      "temperature": 65.0,
      "power_usage": 180.5,
      "throughput": 1250.0,
      "latency": 0.008
    }
  ]
}
```

### Resource Management

#### POST /resources

Allocate compute resources.

**Request Body:**
```json
{
  "user_id": "user123",
  "memory_size": 1073741824,
  "compute_units": 4,
  "duration": 3600
}
```

**Response:**
```json
{
  "success": true,
  "allocation_id": "alloc_1704067200_1",
  "user_id": "user123",
  "gpu_id": 0,
  "memory_size": 1073741824,
  "compute_units": 4,
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-01T01:00:00Z"
}
```

#### DELETE /resources/{allocation_id}

Deallocate compute resources.

**Response:**
```json
{
  "success": true,
  "allocation_id": "alloc_1704067200_1",
  "message": "Resources deallocated successfully"
}
```

## Advanced Features

### Batch Operations

#### POST /inference/batch

Execute multiple inference requests in a single call.

**Request Body:**
```json
{
  "requests": [
    {
      "model_id": "gpt-3.5-turbo",
      "input_data": [[0.1, 0.2, 0.3]],
      "options": {"temperature": 0.7}
    },
    {
      "model_id": "gpt-3.5-turbo",
      "input_data": [[0.4, 0.5, 0.6]],
      "options": {"temperature": 0.8}
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "request_id": "req_1",
      "output_data": [[0.8, 0.9, 0.1]],
      "inference_time": 0.125
    },
    {
      "request_id": "req_2",
      "output_data": [[0.2, 0.3, 0.7]],
      "inference_time": 0.130
    }
  ],
  "total_time": 0.255
}
```

### Model Optimization

#### POST /models/{model_id}/optimize

Optimize a loaded model.

**Request Body:**
```json
{
  "optimization_type": "quantization",
  "target_precision": "int8",
  "calibration_data": [
    [0.1, 0.2, 0.3, ...],
    [0.4, 0.5, 0.6, ...]
  ],
  "options": {
    "preserve_accuracy": true,
    "compression_ratio": 0.5
  }
}
```

**Response:**
```json
{
  "success": true,
  "model_id": "gpt-3.5-turbo",
  "optimization_type": "quantization",
  "original_size": 2147483648,
  "optimized_size": 1073741824,
  "compression_ratio": 0.5,
  "accuracy_loss": 0.02,
  "optimization_time": 45.2
}
```

### Virtualization

#### POST /virtualization/gpus

Create a virtual GPU.

**Request Body:**
```json
{
  "virtual_gpu_id": "vgpu_1",
  "memory_size": 268435456,
  "compute_units": 2,
  "scheduling_policy": "round_robin"
}
```

**Response:**
```json
{
  "success": true,
  "virtual_gpu_id": "vgpu_1",
  "physical_gpu_id": 0,
  "memory_size": 268435456,
  "compute_units": 2,
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### DELETE /virtualization/gpus/{virtual_gpu_id}

Destroy a virtual GPU.

**Response:**
```json
{
  "success": true,
  "virtual_gpu_id": "vgpu_1",
  "message": "Virtual GPU destroyed successfully"
}
```

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_MODEL_ID",
    "message": "Model ID 'invalid-model' not found",
    "details": {
      "model_id": "invalid-model",
      "available_models": ["gpt-3.5-turbo", "bert-base"]
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_MODEL_ID` | Model ID not found or invalid |
| `MODEL_ALREADY_LOADED` | Model is already loaded |
| `INSUFFICIENT_MEMORY` | Not enough GPU memory |
| `INVALID_INPUT_DATA` | Input data format is invalid |
| `REQUEST_TIMEOUT` | Request timed out |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Access denied |

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Default**: 1000 requests per minute per API key
- **Burst**: 100 requests per second
- **Headers**: Rate limit information is included in response headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1704067260
```

## SDK Examples

### Python SDK

```python
import requests

class MSmartComputeClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def load_model(self, model_config):
        response = requests.post(
            f"{self.base_url}/models",
            json=model_config,
            headers=self.headers
        )
        return response.json()
    
    def inference(self, model_id, input_data, options=None):
        request_data = {
            "model_id": model_id,
            "input_data": input_data,
            "options": options or {}
        }
        response = requests.post(
            f"{self.base_url}/inference",
            json=request_data,
            headers=self.headers
        )
        return response.json()

# Usage
client = MSmartComputeClient("http://localhost:8080/api/v1", "your-api-key")
result = client.inference("gpt-3.5-turbo", [[0.1, 0.2, 0.3]])
```

### JavaScript SDK

```javascript
class MSmartComputeClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async loadModel(modelConfig) {
        const response = await fetch(`${this.baseUrl}/models`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(modelConfig)
        });
        return response.json();
    }
    
    async inference(modelId, inputData, options = {}) {
        const requestData = {
            model_id: modelId,
            input_data: inputData,
            options: options
        };
        const response = await fetch(`${this.baseUrl}/inference`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(requestData)
        });
        return response.json();
    }
}

// Usage
const client = new MSmartComputeClient('http://localhost:8080/api/v1', 'your-api-key');
const result = await client.inference('gpt-3.5-turbo', [[0.1, 0.2, 0.3]]);
```

## Testing

### Health Check

```bash
curl http://localhost:8080/health
```

### Load Model

```bash
curl -X POST http://localhost:8080/api/v1/models \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model_id": "test-model",
    "model_type": "transformer",
    "model_path": "/path/to/model.bin",
    "max_batch_size": 32
  }'
```

### Inference

```bash
curl -X POST http://localhost:8080/api/v1/inference \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model_id": "test-model",
    "input_data": [[0.1, 0.2, 0.3]],
    "batch_size": 1,
    "sequence_length": 3
  }'
```

## Support

For API support and questions:

- **Documentation**: [docs.cogniware.com](https://docs.cogniware.com)
- **GitHub Issues**: [Repository Issues](https://github.com/your-org/cogniware-engine/issues)
- **Email**: api-support@cogniware.com
- **Discord**: [MSmartCompute Community](https://discord.gg/cogniware)

---

**Version**: 1.0.0  
**Last Updated**: January 1, 2024 