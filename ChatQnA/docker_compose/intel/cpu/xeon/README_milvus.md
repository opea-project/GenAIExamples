# Build Mega Service of ChatQnA on Xeon

Quick Start:

1. Set up the environment variables.
2. Run Docker Compose.
3. Consume the ChatQnA Service.

## Quick Start: 1.Setup Environment Variable

```bash
mkdir ~/OPEA -p
mkdir ~/OPEA/tmp -p
cd ~/OPEA
git clone https://github.com/opea-project/GenAIExamples.git
# If you want to build code, download GenAIComps
git clone https://github.com/opea-project/GenAIComps.git
```

To set up environment variables for deploying ChatQnA services, follow these steps:

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPs_Proxy"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   ```

3. Set up other environment variables:
   ```bash
   export host_ip="External_Public_IP"
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   source ./set_env_milvus.sh
   ```

## Quick Start: 2.Run Docker Compose

```bash
cd ~/OPEA/GenAIExample/ChatQnA/docker_compose/intel/cpu/xeon
docker compose -f ./compose_milvus.yaml up -d
```

It will automatically download the docker images on `docker hub`.


In following cases, you could build docker image from source by yourself.

- Failed to download the docker image.

- If you want to use a specific version of Docker image.

Please refer to 'Build Docker Images' in below.


## QuickStart: 3.Consume the ChatQnA Service

```bash
curl http://${host_ip}:8888/v1/chatqna \
    -H "Content-Type: application/json" \
    -d '{
        "messages": "What is the revenue of Nike in 2023?"
    }'
```

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
cd ~/OPEA/GenAIExample/ChatQnA/docker_compose/intel/cpu/xeon
docker compose -f ./compose_milvus.yaml build
```

Then run the command `docker images`, you will have the following 5 Docker Images:

1. `opea/dataprep-milvus:latest`
2. `opea/retriever-milvus:latest`
3. `opea/chatqna:latest`
4. `opea/chatqna-ui:latest`
5. `opea/nginx:latest`

## 🚀 Start Microservices

```
cd ~/OPEA/GenAIExample/ChatQnA/docker_compose/intel/cpu/xeon
docker compose -f up -d
```

### Valid the Microservices and Launch the UI

To valid the Microservices, change models as well as Launch the UI, Pleser refer to ./README.md
