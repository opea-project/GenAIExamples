# Build and deploy Translation Application on AMD GPU (ROCm)

## Build images

### Build the LLM Docker Image

```bash
### Cloning repo
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps

### Build Docker image
docker build -t opea/llm-textgen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/text-generation/Dockerfile .
```

### Build the MegaService Docker Image

```bash
### Cloning repo
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/Translation/

### Build Docker image
docker build -t opea/translation:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### Build the UI Docker Image

```bash
cd GenAIExamples/Translation/ui
### Build UI Docker image
docker build -t opea/translation-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .
```

## Deploy Translation Application

### Features of Docker compose for AMD GPUs

1. Added forwarding of GPU devices to the container TGI service with instructions:

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

In this case, all GPUs are thrown. To reset a specific GPU, you need to use specific device names cardN and renderN.

For example:

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

To find out which GPU device IDs cardN and renderN correspond to the same GPU, use the GPU driver utility

### Go to the directory with the Docker compose file

```bash
cd GenAIExamples/Translation/docker_compose/amd/gpu/rocm
```

### Set environments

In the file "GenAIExamples/Translation/docker_compose/amd/gpu/rocm/set_env.sh " it is necessary to set the required values. Parameter assignments are specified in the comments for each variable setting command

```bash
chmod +x set_env.sh
. set_env.sh
```

### Run services

```
docker compose up -d
```

# Validate the MicroServices and MegaService

## Validate TGI service

```bash
curl http://${TRANSLATION_HOST_IP}:${TRANSLATIONS_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

## Validate LLM service

```bash
curl http://${TRANSLATION_HOST_IP}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"Translate this from Chinese to English:\nChinese: 我爱机器翻译。\nEnglish:"}' \
  -H 'Content-Type: application/json'
```

## Validate MegaService

```bash
curl http://${TRANSLATION_HOST_IP}:${TRANSLATION_BACKEND_SERVICE_PORT}/v1/translation -H "Content-Type: application/json" -d '{
     "language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。"}'
```

## Validate Nginx service

```bash
curl http://${TRANSLATION_HOST_IP}:${TRANSLATION_NGINX_PORT}/v1/translation \
    -H "Content-Type: application/json" \
    -d '{"language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。"}'
```
