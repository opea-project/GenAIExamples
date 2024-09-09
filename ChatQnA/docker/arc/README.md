# Run ChatQnA on Intel ArC GPU

## 🚀 Build Docker Images

Docker images for Intel Arc GPU are almost same as Nvidia GPU, except for the "LLM image".
* Follow below steps to build "LLM images".
* For other images, please follow [Nvidia GPU](../gpu/README.md) to build.

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```
### 2. Build LLM Image

vLLM backend
```bash
docker build --no-cache -t opea/vllm:arc --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/vllm/docker/Dockerfile.arc .
```
Microservice
```bash
docker build --no-cache -t opea/llm-vllm:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/vllm/docker/Dockerfile.microservice .
```
### Start all the services Docker Containers

```bash
cd GenAIExamples/ChatQnA/docker/arc/
export host_ip="your_host_ip"
export your_hf_api_token="your hf api token"
#edit set_env.sh to apply required setups
source set_env.sh
docker compose -f compose_vllm_arc.yaml up -d
```

Please note that if you don't need proxy, delete all the proxy ENV in compose_vllm_arc.yaml.
