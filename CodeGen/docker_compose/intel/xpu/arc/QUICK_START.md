# CodeGen on Intel Arc XPU - Quick Start Guide

## 🚀 Quick Deployment (3 Steps)

### Step 1: Setup Environment (1 minute)

```bash
cd GenAIExamples/CodeGen/docker_compose/intel/xpu/arc

# Set your host IP and HuggingFace token
export HOST_IP=$(hostname -I | awk '{print $1}')
export HF_TOKEN="your_huggingface_token"

# Optional: Configure proxy if needed
export no_proxy="localhost,127.0.0.1,${HOST_IP}"
export NO_PROXY="localhost,127.0.0.1,${HOST_IP}"

source ./set_env.sh
```

### Step 2: Deploy Services (5-10 minutes)

```bash
docker compose up -d
```

### Step 3: Wait for Model to Load (3-5 minutes)

```bash
docker compose logs -f codegen-vllm-service
```

Wait for: `Application startup complete`

---

## 🧪 Quick Test

### Test 1: Health Check

```bash
curl http://${HOST_IP}:8028/health
```

Expected: `{"status":"ok"}`

### Test 2: Code Generation

```bash
curl http://${HOST_IP}:8028/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
    "prompt": "def fibonacci(n):",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### Test 3: Access UI

Open browser: http://${HOST_IP}:5173

---

## 📊 Service Ports

| Service     | Port | URL                    |
| ----------- | ---- | ---------------------- |
| vLLM        | 8028 | http://${HOST_IP}:8028 |
| LLM Service | 9000 | http://${HOST_IP}:9000 |
| Backend     | 7778 | http://${HOST_IP}:7778 |
| UI          | 5173 | http://${HOST_IP}:5173 |

---

## 🛠️ Useful Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f codegen-vllm-service
```

### Check Status

```bash
docker compose ps
```

### Stop Services

```bash
docker compose down
```

### Restart Services

```bash
docker compose restart
```

### Remove Everything

```bash
docker compose down -v
```

---

## 🔧 Troubleshooting

### GPU Not Detected?

```bash
ls -la /dev/dri/
sudo usermod -aG video,render $USER
# Logout and login
```

### Service Won't Start?

```bash
docker compose logs codegen-vllm-service
docker compose ps
```

### Out of Memory?

Edit `compose.yaml`:

```yaml
shm_size: 16g # Increase from 10g
```

---

## 📝 Configuration

### Change Model

Edit `set_env.sh`:

```bash
export CODEGEN_LLM_MODEL_ID="your-model-id"
```

### Change Ports

Edit `set_env.sh`:

```bash
export CODEGEN_VLLM_SERVICE_PORT=8029
export CODEGEN_UI_SERVICE_PORT=5174
```

---

## ✅ Validation Checklist

- [ ] Docker daemon running
- [ ] Intel GPU detected at `/dev/dri`
- [ ] Environment variables set
- [ ] Services deployed
- [ ] Health endpoint responds
- [ ] Code generation works
- [ ] UI accessible

---

## 📚 More Information

- Full documentation: [README.md](./README.md)
- Main CodeGen docs: [../../README.md](../../../README.md)

---

## 🎯 Expected Timeline

| Phase             | Duration      | Status |
| ----------------- | ------------- | ------ |
| Environment setup | 1 min         | ✅     |
| Pull images       | 10-15 min     | ⏳     |
| Start services    | 2 min         | ⏳     |
| Model loading     | 3-5 min       | ⏳     |
| **Total**         | **15-20 min** |        |

---

**Hardware**: Intel Arc Pro B-series GPU  
**Model**: Qwen/Qwen2.5-Coder-7B-Instruct  
**Backend**: Intel vLLM 0.14.1-xpu
