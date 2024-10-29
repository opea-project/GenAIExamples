# Build Mega Service of Productivity Suite

This document outlines the deployment process for OPEA Productivity Suite utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server and [GenAIExamples](https://github.com/opea-project/GenAIExamples.git) solutions. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank`, and `llm`. 

## 🚀 Build Docker Images

Create a directory and clone the GenAIComps repository

```bash
mkdir genai
git clone --branch v1.0 https://github.com/opea-project/GenAIComps.git
```
Copy patch files related to GenAIComps inside GenAIComps folder and apply the patch

```bash
cd GenAIComps
git am *.patch
```

### 1. Build Embedding Image

```bash
docker build --no-cache -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/tei/langchain/Dockerfile .
```

### 2. Build Rerank Image

```bash
docker build --no-cache -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/tei/Dockerfile .
```

### 3. Build LLM Images

#### Use TGI as backend to build FAQ Generation

```bash
docker build -t opea/llm-faqgen-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/faq-generation/tgi/langchain/Dockerfile .
```

#### Use TGI as backend to build Doc Summarization

```bash
docker build -t opea/llm-docsum-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/summarization/tgi/langchain/Dockerfile .
```

#### Use TGI as backend to build Text Generation

```bash
docker build --no-cache -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

### 4. Build Prompt Registry Image

```bash
docker build -t opea/promptregistry-mongo-server:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/prompt_registry/mongo/Dockerfile .
```

### 5. Build Productivity Suite Docker Images

The Productivity Suite is composed of multiple GenAIExample reference solutions composed together.

```bash
cd ..
git clone --branch v1.0 https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples
```

Copy the patch files related to GenAIExamples into above cloned GenAIExamples folder

Apply the patches
```bash
git am *.patch
```

#### 5.1 Build ChatQnA MegaService Docker Images

```bash
cd ..
docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f GenAIExamples/ChatQnA/Dockerfile.wrapper .
```

### 6. Build UI Docker Image

Build frontend Docker image that enables via below command:

**Export the value of the public IP address of your server to the `host_ip` environment variable**

```bash
cd GenAIExamples/ProductivitySuite/ui
docker build --no-cache -t opea/productivity-suite-react-ui-server:latest -f docker/Dockerfile.react .
```

## 🚀 Start Microservices

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

**Export the value of the public IP address of your server to the `host_ip` environment variable**

> Change the External_Public_IP below with the actual IPV4 value

```
export host_ip="External_Public_IP"
```

**Export the value of your Huggingface API token to the `your_hf_api_token` environment variable**

> Change the Your_Huggingface_API_Token below with tyour actual Huggingface API Token value

```
export your_hf_api_token="Your_Huggingface_API_Token"
```

**Append the value of the public IP address to the no_proxy list**

```
export your_no_proxy=${your_no_proxy},"External_Public_IP"
```

**Export the value of your remote host to the `remote_host` environment variable (Only if you are using remote TGI/TEI)**

> Change the Your_Remote_Host below with your actual API Gateway Host value

```
export remote_host="Your_Remote_Host"
```

**Set ClientId, Client_Secret and Token URL only if the remote API is protected with OAuth Client Credentials Flow**

**Export the value of your Remote API ClientId to the `clientid` environment variable**

> Change the Your_API_ClientId below with your actual ClientId value

```
export clientid="Your_API_ClientId"
```

**Export the value of your Remote API client secret to the `client_secret` environment variable**

> Change the Your_API_ClientSecret below with your actual ClientSecret value

```
export client_secret="Your_API_ClientSecret"
```

**Export the value of your Remote API token url to the `token_url` environment variable**

> Change the Your_API_TokenUrl below with your actual Token URL value

```
export token_url="Your_API_TokenUrl"
```

**Export the value of your Remote Embedding Endpoint to the `embedding_endpoint` environment variable (Set this if you have tei embedding running remotely)**

> Change the Your_Remote_Embedding_Endpoint below with your actual embedding endpoint value

```
export embedding_endpoint="Your_Remote_Embedding_Endpoint"
```

**Export the value of your Remote Reranking Endpoint to the `reranking_endpoint` environment variable (Set this if you have reranking running remotely)**

> Change the Your_Remote_Reranking_Endpoint below with tyour actual reranking endpoint value

```
export reranking_endpoint="Your_Remote_Reranking_Endpoint"
```

**Export the value of your Remote TGI Endpoint to the `tgi_endpoint` environment variable (Set this if you have tgi running remotely)**

> Change the Your_Remote_TGI_Endpoint below with tyour actual tgi endpoint value

```
export tgi_endpoint="Your_Remote_TGI_Endpoint"
```

**To use multiple TGI models**
> Create the model_configs.json file under /GenAIExamples/ProductivitySuite/docker_compose/intel/hpu/gaudi folder
> Add the model details as shown in the below example


```bash
cd ..
cd docker_compose/intel/hpu/gaudi
touch model_configs.json
```

File Structure:

[
    {
        "model_name": "Your Model Name",
        "displayName": "Model Display Name for the UI",
        "endpoint": "Model Endpoint with http/https",
        "minToken": 100, //Min Token Value
        "maxToken": 2000 //Max Token Value
    },
    {
        "model_name": "Your Model Name",
        "displayName": "Model Display Name for the UI",
        "endpoint": "Model Endpoint with http/https",
        "minToken": 100, //Min Token Value
        "maxToken": 2000 //Max Token Value
    }
]

Example:

[
    {
        "model_name": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "displayName": "llama-3.1-70B",
        "endpoint": "https://<host>/<endpoint>",
        "minToken": 100,
        "maxToken": 2000
    },
    {
        "model_name": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "displayName": "llama-3.1-8B",
        "endpoint": "https://<host>/<endpoint>",
        "minToken": 100,
        "maxToken": 2000
    },
    {
        "model_name": "Intel/neural-chat-7b-v3-3",
        "displayName": "neural chat",
        "endpoint": "https://<host>/<endpoint>",
        "minToken": 100,
        "maxToken": 1000
    }
]

> After creating and adding details in the model_configs.json file. Copy the same file into the public folder of the UI

```bash
cd ../../../../
cp docker_compose/intel/hpu/gaudi/model_configs.json ui/react/public/model_configs.json
```

> Navigate to GenAIExamples/ProductivitiySuite/docker_compose/intel/hpu/gaudi and run set_env.sh

```bash
cd docker_compose/intel/hpu/gaudi
chmod +x set_env_remote.sh
source set_env_remote.sh
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

#### Run all services locally
```bash
docker compose -f compose.yaml up -d
```

#### Run TGI and TEI inference remote
```bash
docker compose -f compose_remote.yaml up -d
```

#### Run only TGI remote
```bash
docker compose -f compose_tgi_remote.yaml up -d
```

### Setup Keycloak

Please refer to [keycloak_setup_guide](keycloak_setup_guide.md) for more detail related to Keycloak configuration setup.


## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5174.

