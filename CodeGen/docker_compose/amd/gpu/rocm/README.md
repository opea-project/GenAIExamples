###### Copyright (C) 2024 Advanced Micro Devices, Inc.

# Build and deploy CodeGen Application on AMD GPU (ROCm)

## Build images
### Build the LLM Docker Image

```bash
### Cloning repo
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps

### Build Docker image
docker build -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

### Build the MegaService Docker Image

```bash
### Cloning repo
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/CodeGen

### Build Docker image
docker build -t opea/codegen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### Build the UI Docker Image

```bash
cd GenAIExamples/CodeGen/ui
### Build UI Docker image
docker build -t opea/codegen-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .

### Build React UI Docker image (React UI allows you to use file uploads)
docker build --no-cache -t opea/codegen-react-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile.react .
```
It is recommended to use the React UI as it works for downloading files. The use of React UI is set in the Docker Compose file
## Deploy CodeGen Application

```bash
cd GenAIExamples/CodeGen/docker_compose/amd/gpu/rocm
```
In the file "GenAIExamples/CodeGen/docker_compose/amd/gpu/rocm/set_env.sh " it is necessary to set the required values. Parameter assignments are specified in the comments for each variable setting command

```bash
### Set environments
chmod +x set_env.sh
. set_env.sh

### Run application services using Docker Compose
docker compose up -d
```



