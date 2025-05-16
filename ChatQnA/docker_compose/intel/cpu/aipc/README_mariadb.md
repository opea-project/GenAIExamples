# Build Mega Service of ChatQnA on AIPC

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AIPC. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank`, and `llm`.

## Quick Start:

1. Set up the environment variables.
2. Run Docker Compose.
3. Consume the ChatQnA Service.

### Quick Start: 1. Set up environment variables

1. Set the default environment:

   ```bash
   source ./set_env_mariadb.sh
   ```

2. You need to set a Hugging Face access token for your account:

   ```bash
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   ```

3. _Set up the model (optional)_

   _By default, **llama3.2** is used for LLM serving, the default model can be changed to other LLM models. Please pick a [validated llm models](https://github.com/opea-project/GenAIComps/tree/main/comps/llms/src/text-generation#validated-llm-models) from the table._
   \*To change the default model defined in `set_env_mariadb.sh`, overwrite it by exporting `OLLAMA_MODEL` to the new model or by modifying `set_env_mariadb.sh`.

   _Example, in order to use [DeepSeek-R1-Distill-Llama-8B model](https://ollama.com/library/deepseek-r1:8b), set:_

   ```bash
   export OLLAMA_MODEL="deepseek-r1:8b"
   ```

### Quick Start: 2. Run Docker Compose

```bash
docker compose -f compose_mariadb.yaml up -d
```

---

_You should build docker image from source by yourself if_:

- _You are developing off the git main branch (as the container's ports in the repo may be different from the published docker image)._
- _You can't download the docker image._
- _You want to use a specific docker image version_

Please refer to ['Build Docker Images'](#🚀-build-docker-images) in below.

---

### Quick Start:3. Consume the ChatQnA Service

Once the services are up, open the following URL from your browser: `http://localhost` and fiddle around with prompts.

## 🚀 Build Docker Images

```bash
# Clone the AI components repository
mkdir ~/OPEA -p
cd ~/OPEA
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

If you are in a proxy environment, set the proxy-related environment variables:

```bash
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
```

### 1. Build Retriever Image

```bash
docker build --no-cache -t opea/retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
```

### 2. Build Dataprep Image

```bash
docker build --no-cache -t opea/dataprep:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/src/Dockerfile .
cd ..
```

### 3. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna.py` Python script. Build MegaService Docker image via below command:

```bash
cd ~/OPEA
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA
docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f Dockerfile .
```

### 4. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd ~/OPEA/GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

### 5. Build Nginx Docker Image

```bash
cd GenAIComps
docker build -t opea/nginx:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/third_parties/nginx/src/Dockerfile .
```

Finally, `docker image ls` would return:

```
opea/dataprep:latest
opea/retriever:latest
opea/chatqna:latest
opea/chatqna-ui:latest
opea/nginx:latest
```

After starting the services, if you want to check each service individually, please refer to the section below.

### Validate Microservices

You can validate each microservice by making individual requests.  
For details on how to verify the correctness of the response, refer to [how-to-validate_service](../../hpu/gaudi/how_to_validate_service.md).

1. TEI Embedding Service

   ```bash
   curl ${host_ip}:6006/embed \
       -X POST \
       -d '{"inputs":"What is Deep Learning?"}' \
       -H 'Content-Type: application/json'
   ```

2. Retriever Microservice

   ```bash
   # Mock the embedding vector
   export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
   ```

   ```bash
   # Perform a similarity search
   curl http://${host_ip}:7000/v1/retrieval \
     -X POST \
     -d '{"text":"What is the revenue of Nike in 2023?","embedding":"'"${your_embedding}"'"}' \
     -H 'Content-Type: application/json'
   ```

3. TEI Reranking Service

   ```bash
   curl http://${host_ip}:8808/rerank \
       -X POST \
       -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
       -H 'Content-Type: application/json'
   ```

4. Ollama Service

   ```bash
   curl http://${host_ip}:11434/api/generate -d '{"model": "llama3.2", "prompt":"What is Deep Learning?"}'
   ```

5. MegaService

   ```bash
   curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
        "messages": "What is the revenue of Nike in 2023?"
        }'
   ```

6. DataPrep Service

   Try the `ingest - get - delete` endpoints:

   ```bash
   # Get a sample file to ingest
   wget https://raw.githubusercontent.com/opea-project/GenAIComps/v1.1/comps/retrievers/redis/data/nke-10k-2023.pdf
   ```

   ```bash
   # Ingest
   curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
      -H "Content-Type: multipart/form-data" \
      -F "files=@./nke-10k-2023.pdf"
   ```

   ```bash
   # Get
   curl -X POST "http://${host_ip}:6007/v1/dataprep/get" \
      -H "Content-Type: application/json"
   ```

   ```bash
   # Delete all
   curl -X POST "http://${host_ip}:6007/v1/dataprep/delete" \
      -H "Content-Type: application/json" \
      -d '{"file_path": "all"}'
   ```
