# LLM Microservice

This microservice, designed for Language Model Inference (LLM), processes input consisting of a query string and associated reranked documents. It constructs a prompt based on the query and documents, which is then used to perform inference with a large language model. The service delivers the inference results as output.

A prerequisite for using this microservice is that users must have a LLM text generation service (etc., TGI, vLLM and Ray) already running. Users need to set the LLM service's endpoint into an environment variable. The microservice utilizes this endpoint to create an LLM object, enabling it to communicate with the LLM service for executing language model operations.

Overall, this microservice offers a streamlined way to integrate large language model inference into applications, requiring minimal setup from the user beyond initiating a TGI/vLLM/Ray service and configuring the necessary environment variables. This allows for the seamless processing of queries and documents to generate intelligent, context-aware responses.

## Validated LLM Models

| Model                       | TGI-Gaudi | vLLM-CPU | vLLM-Gaudi | Ray |
| --------------------------- | --------- | -------- | ---------- | --- |
| [Intel/neural-chat-7b-v3-3] | ✓         | ✓        | ✓          | ✓   |
| [Llama-2-7b-chat-hf]        | ✓         | ✓        | ✓          | ✓   |
| [Llama-2-70b-chat-hf]       | ✓         | -        | ✓          | x   |
| [Meta-Llama-3-8B-Instruct]  | ✓         | ✓        | ✓          | ✓   |
| [Meta-Llama-3-70B-Instruct] | ✓         | -        | ✓          | x   |
| [Phi-3]                     | x         | Limit 4K | Limit 4K   | ✓   |

## Clone OPEA GenAIComps

Clone this repository at your desired location and set an environment variable for easy setup and usage throughout the instructions.

```bash
git clone https://github.com/opea-project/GenAIComps.git

export OPEA_GENAICOMPS_ROOT=$(pwd)/GenAIComps
```

## 🚀1. Start Microservice with Python (Option 1)

To start the LLM microservice, you need to install python packages first.

### 1.1 Install Requirements

```bash
pip install opea-comps
pip install -r ${OPEA_GENAICOMPS_ROOT}/comps/llms/requirements.txt

# Install requirements of your choice of microservice in the text-generation folder (tgi, vllm, vllm-ray, etc.)
export MICROSERVICE_DIR=your_chosen_microservice

pip install -r ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/${MICROSERVICE_DIR}/requirements.txt
```

Set an environment variable `your_ip` to the IP address of the machine where you would like to consume the microservice.

```bash
# For example, this command would set the IP address of your currently logged-in machine.
export your_ip=$(hostname -I | awk '{print $1}')
```

### 1.2 Start LLM Service with Python Script

#### 1.2.1 Start the TGI Service

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
python ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/tgi/llm.py
python ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/tgi/llm.py
```

#### 1.2.2 Start the vLLM Service

```bash
export vLLM_LLM_ENDPOINT="http://${your_ip}:8008"
python ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/vllm/llm.py
python ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/vllm/llm.py
```

#### 1.2.3 Start the Ray Service

```bash
export RAY_Serve_ENDPOINT="http://${your_ip}:8008"
python ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/ray_serve/llm.py
python ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/ray_serve/llm.py
```

## 🚀2. Start Microservice with Docker (Option 2)

You can use either a published docker image or build your own docker image with the respective microservice Dockerfile of your choice. You must create a user account with [HuggingFace] and obtain permission to use the restricted LLM models by adhering to the guidelines provided on the respective model's webpage.

### 2.1 Start LLM Service with published image

#### 2.1.1 Start TGI Service

```bash
export HF_LLM_MODEL=${your_hf_llm_model}
export HF_TOKEN=${your_hf_api_token}

docker run \
  -p 8008:80 \
  -e HF_TOKEN=${HF_TOKEN} \
  -v ./data:/data \
  --name tgi_service \
  --shm-size 1g \
  ghcr.io/huggingface/text-generation-inference:1.4 \
  --model-id ${HF_LLM_MODEL}
```

#### 2.1.2 Start vLLM Service

```bash
# Use the script to build the docker image as opea/vllm:cpu
bash ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/vllm/build_docker_vllm.sh cpu

export HF_LLM_MODEL=${your_hf_llm_model}
export HF_TOKEN=${your_hf_api_token}

docker run -it \
  --name vllm_service \
  -p 8008:80 \
  -e HF_TOKEN=${HF_TOKEN} \
  -e VLLM_CPU_KVCACHE_SPACE=40 \
  -v ./data:/data \
  opea/vllm:cpu \
  --model ${HF_LLM_MODEL}
  --port 80
```

#### 2.1.3 Start Ray Service

```bash
export HF_LLM_MODEL=${your_hf_llm_model}
export HF_CHAT_PROCESSOR=${your_hf_chatprocessor}
export HF_TOKEN=${your_hf_api_token}
export TRUST_REMOTE_CODE=True

docker run -it \
  --runtime=habana \
  --name ray_serve_service \
  -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
  --cap-add=sys_nice \
  --ipc=host \
  -p 8008:80 \
  -e HF_TOKEN=$HF_TOKEN \
  -e TRUST_REMOTE_CODE=$TRUST_REMOTE_CODE \
  opea/llm-ray:latest \
  /bin/bash -c " \
    ray start --head && \
    python api_server_openai.py \
      --port_number 80 \
      --model_id_or_path ${HF_LLM_MODEL} \
      --chat_processor ${HF_CHAT_PROCESSOR}"
```

### 2.2 Start LLM Service with image built from source

If you start an LLM microservice with docker, the `docker_compose_llm.yaml` file will automatically start a TGI/vLLM service with docker.

#### 2.2.1 Setup Environment Variables

In order to start TGI and LLM services, you need to setup the following environment variables first.

```bash
export HF_TOKEN=${your_hf_api_token}
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL_ID=${your_hf_llm_model}
```

In order to start vLLM and LLM services, you need to setup the following environment variables first.

```bash
export HF_TOKEN=${your_hf_api_token}
export vLLM_LLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL_ID=${your_hf_llm_model}
```

In order to start Ray serve and LLM services, you need to setup the following environment variables first.

```bash
export HF_TOKEN=${your_hf_api_token}
export RAY_Serve_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL=${your_hf_llm_model}
export CHAT_PROCESSOR="ChatModelLlama"
```

### 2.2 Build Docker Image

#### 2.2.1 TGI

```bash
cd ${OPEA_GENAICOMPS_ROOT}

docker build \
  -t opea/llm-tgi:latest \
  --build-arg https_proxy=$https_proxy \
  --build-arg http_proxy=$http_proxy \
  -f comps/llms/text-generation/tgi/Dockerfile .
```

#### 2.2.2 vLLM

Build vllm docker.

```bash
bash ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/vllm/langchain/dependency/build_docker_vllm.sh
```

Build microservice docker.

```bash
cd ${OPEA_GENAICOMPS_ROOT}

docker build \
  -t opea/llm-vllm:latest \
  --build-arg https_proxy=$https_proxy \
  --build-arg http_proxy=$http_proxy \
  -f comps/llms/text-generation/vllm/langchain/Dockerfile .
```

#### 2.2.3 Ray Serve

Build Ray Serve docker.

```bash
bash ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/vllm/ray/dependency/build_docker_vllmray.sh
```

Build microservice docker.

```bash
cd ${OPEA_GENAICOMPS_ROOT}

docker build \
  -t opea/llm-ray:latest \
  --build-arg https_proxy=$https_proxy \
  --build-arg http_proxy=$http_proxy \
  -f comps/llms/text-generation/vllm/ray/Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

### 2.3 Run Docker with CLI (Option A)

#### 2.3.1 TGI

```bash
docker run -d \
  --name="llm-tgi-server" \
  -p 9000:9000 \
  --ipc=host \
  -e http_proxy=$http_proxy \
  -e https_proxy=$https_proxy \
  -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT \
  -e HF_TOKEN=$HF_TOKEN \
  opea/llm-tgi:latest
```

#### 2.3.2 vLLM

Start vllm endpoint.

```bash
bash ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/vllm/langchain/dependency/launch_vllm_service.sh
```

Start vllm microservice.

```bash
docker run \
  --name="llm-vllm-server" \
  -p 9000:9000 \
  --ipc=host \
  -e http_proxy=$http_proxy \
  -e https_proxy=$https_proxy \
  -e no_proxy=${no_proxy} \
  -e vLLM_LLM_ENDPOINT=$vLLM_LLM_ENDPOINT \
  -e HF_TOKEN=$HF_TOKEN \
  -e LLM_MODEL_ID=$LLM_MODEL_ID \
  opea/llm-vllm:latest
```

#### 2.3.3 Ray Serve

Start Ray Serve endpoint.

```bash
bash ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/vllm/ray/dependency/launch_vllmray.sh
```

Start Ray Serve microservice.

```bash
docker run -d \
  --name="llm-ray-server" \
  -p 9000:9000 \
  --ipc=host \
  -e http_proxy=$http_proxy \
  -e https_proxy=$https_proxy \
  -e RAY_Serve_ENDPOINT=$RAY_Serve_ENDPOINT \
  -e HF_TOKEN=$HF_TOKEN \
  -e LLM_MODEL=$LLM_MODEL \
  opea/llm-ray:latest
```

### 2.4 Run Docker with Docker Compose (Option B)

#### 2.4.1 TGI

```bash
cd ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/tgi
docker compose -f docker_compose_llm.yaml up -d
```

#### 2.4.2 vLLM

```bash
cd ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/vllm/langchain
docker compose -f docker_compose_llm.yaml up -d
```

#### 2.4.3 Ray Serve

```bash
cd ${OPEA_GENAICOMPS_ROOT}/comps/llms/text-generation/vllm/ray
docker compose -f docker_compose_llm.yaml up -d
```

## 🚀3. Consume LLM Service

### 3.1 Check Service Status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Verify the LLM Service

#### 3.2.1 Verify the TGI Service

```bash
curl http://${your_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

#### 3.2.2 Verify the vLLM Service

```bash
curl http://${your_ip}:8008/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": ${your_hf_llm_model},
  "prompt": "What is Deep Learning?",
  "max_tokens": 32,
  "temperature": 0
  }'
```

#### 3.2.3 Verify the Ray Service

```bash
curl http://${your_ip}:8008/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": ${your_hf_llm_model},
  "messages": [
        {"role": "assistant", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Deep Learning?"},
    ],
  "max_tokens": 32,
  "stream": True
  }'
```

### 3.3 Consume LLM Service

You can set the following model parameters according to your actual needs, such as `max_new_tokens`, `streaming`.

The `streaming` parameter determines the format of the data returned by the API. It will return text string with `streaming=false`, return text streaming flow with `streaming=true`.

```bash
# non-streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
  "query":"What is Deep Learning?",
  "max_new_tokens":17,
  "top_k":10,
  "top_p":0.95,
  "typical_p":0.95,
  "temperature":0.01,
  "repetition_penalty":1.03,
  "streaming":false
  }'


# streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
  "query":"What is Deep Learning?",
  "max_new_tokens":17,
  "top_k":10,
  "top_p":0.95,
  "typical_p":0.95,
  "temperature":0.01,
  "repetition_penalty":1.03,
  "streaming":true
  }'

```

<!--Below are links used in these document. They are not rendered: -->

[Intel/neural-chat-7b-v3-3]: https://huggingface.co/Intel/neural-chat-7b-v3-3
[Llama-2-7b-chat-hf]: https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
[Llama-2-70b-chat-hf]: https://huggingface.co/meta-llama/Llama-2-70b-chat-hf
[Meta-Llama-3-8B-Instruct]: https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct
[Meta-Llama-3-70B-Instruct]: https://huggingface.co/meta-llama/Meta-Llama-3-70B-Instruct
[Phi-3]: https://huggingface.co/collections/microsoft/phi-3-6626e15e9585a200d2d761e3
[HuggingFace]: https://huggingface.co/
