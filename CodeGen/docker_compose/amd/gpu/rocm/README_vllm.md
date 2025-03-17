# Build and Deploy CodeGen Application on AMD GPU (ROCm)

## Prerequisites

Before starting, ensure the following are installed on your system:

- **Docker**
- **ROCm** (for AMD GPU support)
- **Git**

---

## Build Docker Images

### 1. Build the LLM Docker Image

```bash
# Clone the repository
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps

# Build the Docker image
docker build -t opea/llm-textgen:latest \
  --build-arg https_proxy=$https_proxy \
  --build-arg http_proxy=$http_proxy \
  -f comps/llms/src/text-generation/Dockerfile .
```

### 2. Build the vLLM ROCm Docker Image

```bash
# Build the vLLM Docker image with ROCm support
docker build -t opea/vllm-rocm:latest \
  -f comps/third_parties/vllm/src/Dockerfile.amd_gpu .
```

### 3. Build the MegaService Docker Image

```bash
# Clone the examples repository
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/CodeGen

# Build the MegaService Docker image
docker build -t opea/codegen:latest \
  --build-arg https_proxy=$https_proxy \
  --build-arg http_proxy=$http_proxy \
  -f Dockerfile .
```

### 4. Build the UI Docker Images

```bash
# Navigate to the UI directory
cd GenAIExamples/CodeGen/ui

# Build the base UI Docker image
docker build -t opea/codegen-ui:latest \
  --build-arg https_proxy=$https_proxy \
  --build-arg http_proxy=$http_proxy \
  -f ./docker/Dockerfile .

# Build the React UI Docker image (recommended for file uploads)
docker build --no-cache -t opea/codegen-react-ui:latest \
  --build-arg https_proxy=$https_proxy \
  --build-arg http_proxy=$http_proxy \
  -f ./docker/Dockerfile.react .
```

**Note:** The React UI is recommended as it supports file uploads. Its usage is configured in the Docker Compose file.

---

## Deploy the CodeGen Application

### Docker Compose Configuration for AMD GPUs

To enable GPU support for AMD GPUs, the following configuration is added to the Docker Compose file:

```yaml
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri/:/dev/dri/
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

This configuration forwards all available GPUs to the container. To use a specific GPU, specify its `cardN` and `renderN` device IDs. For example:

```yaml
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri/card0:/dev/dri/card0
  - /dev/dri/render128:/dev/dri/render128
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

**How to Identify GPU Device IDs:**
Use AMD GPU driver utilities to determine the correct `cardN` and `renderN` IDs for your GPU.

---

### Launch the Application

1. Navigate to the Docker Compose directory:

   ```bash
   cd GenAIExamples/CodeGen/docker_compose/amd/gpu/rocm
   ```

2. Configure environment variables:

   - Edit the `set_env_vllm.sh` file to set the required values. Comments in the file provide guidance for each variable.
   - Make the script executable and apply the environment variables:

     ```bash
     chmod +x set_env_vllm.sh
     . set_env_vllm.sh
     ```

3. Start the services:

   ```bash
   docker compose -f compose_vllm.yaml up -d --force-recreate
   ```

---

## Validate the Services

### 1. Validate the vLLM Service

```bash
curl http://${HOST_IP}:${CODEGEN_VLLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 17}' \
  -H 'Content-Type: application/json'
```

### 2. Validate the LLM Service

```bash
curl http://${HOST_IP}:${CODEGEN_LLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d '{"query":"Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception.","max_tokens":256,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"stream":true}' \
  -H 'Content-Type: application/json'
```

### 3. Validate the MegaService

```bash
curl http://${HOST_IP}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codegen \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."
  }'
```

---

## Conclusion

After completing these steps, the CodeGen application will be deployed and ready for use. Ensure all services are functioning correctly by running the validation commands. If issues arise, check container logs using `docker logs <container_id>` for troubleshooting.

---

This version of the instructions is more structured, includes clear explanations, and provides better readability for users.
