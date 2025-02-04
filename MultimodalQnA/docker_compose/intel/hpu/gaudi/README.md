# Build Mega Service of MultimodalQnA on Gaudi

This document outlines the deployment process for a MultimodalQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `multimodal_embedding` that employs [BridgeTower](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) model as embedding model, `multimodal_retriever`, `lvm`, and `multimodal-data-prep`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

**Export the value of the public IP address of your Gaudi server to the `host_ip` environment variable**

> Change the External_Public_IP below with the actual IPV4 value

```
export host_ip="External_Public_IP"
```

**Append the value of the public IP address to the no_proxy list**

```bash
export your_no_proxy=${your_no_proxy},"External_Public_IP"
```

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export MM_EMBEDDING_SERVICE_HOST_IP=${host_ip}
export MM_RETRIEVER_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export MEGA_SERVICE_HOST_IP=${host_ip}
export REDIS_DB_PORT=6379
export REDIS_INSIGHTS_PORT=8001
export REDIS_URL="redis://${host_ip}:${REDIS_DB_PORT}"
export REDIS_HOST=${host_ip}
export INDEX_NAME="mm-rag-redis"
export WHISPER_PORT=7066
export WHISPER_SERVER_ENDPOINT="http://${host_ip}:${WHISPER_PORT}/v1/asr"
export MAX_IMAGES=1
export WHISPER_MODEL="base"
export DATAPREP_MMR_PORT=6007
export DATAPREP_INGEST_SERVICE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/ingest"
export DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/generate_transcripts"
export DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/generate_captions"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/get"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/delete"
export EMM_BRIDGETOWER_PORT=6006
export EMBEDDING_MODEL_ID="BridgeTower/bridgetower-large-itm-mlm-itc"
export BRIDGE_TOWER_EMBEDDING=true
export MMEI_EMBEDDING_ENDPOINT="http://${host_ip}:$EMM_BRIDGETOWER_PORT"
export MM_EMBEDDING_PORT_MICROSERVICE=6000
export REDIS_RETRIEVER_PORT=7000
export LVM_PORT=9399
export LLAVA_SERVER_PORT=8399
export TGI_GAUDI_PORT="${LLAVA_SERVER_PORT}:80"
export LVM_MODEL_ID="llava-hf/llava-v1.6-vicuna-13b-hf"
export LVM_ENDPOINT="http://${host_ip}:${LLAVA_SERVER_PORT}"
export MEGA_SERVICE_PORT=8888
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna"
export UI_PORT=5173
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

> Note: The `MAX_IMAGES` environment variable is used to specify the maximum number of images that will be sent from the LVM service to the LLaVA server.
> If an image list longer than `MAX_IMAGES` is sent to the LVM server, a shortened image list will be sent to the LLaVA service. If the image list
> needs to be shortened, the most recent images (the ones at the end of the list) are prioritized to send to the LLaVA service. Some LLaVA models have not
> been trained with multiple images and may lead to inaccurate results. If `MAX_IMAGES` is not set, it will default to `1`.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

### 1. Build embedding-multimodal-bridgetower Image

Build embedding-multimodal-bridgetower docker image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build --no-cache -t opea/embedding-multimodal-bridgetower:latest --build-arg EMBEDDER_PORT=$EMM_BRIDGETOWER_PORT --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/third_parties/bridgetower/src/Dockerfile .
```

Build embedding microservice image

```bash
docker build --no-cache -t opea/embedding:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/src/Dockerfile .
```

### 2. Build retriever-multimodal-redis Image

```bash
docker build --no-cache -t opea/retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
```

### 3. Build LVM Images

Build TGI Gaudi image

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:2.0.6
```

Build lvm microservice image

```bash
docker build --no-cache -t opea/lvm:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/src/Dockerfile .
```

### 4. Build dataprep-multimodal-redis Image

```bash
docker build --no-cache -t opea/dataprep:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/src/Dockerfile .
```

### 5. Build Whisper Server Image

Build whisper server image

```bash
docker build --no-cache -t opea/whisper:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/src/integrations/dependency/whisper/Dockerfile .
```

### 6. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the [multimodalqna.py](../../../../multimodalqna.py) Python script. Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/MultimodalQnA
docker build --no-cache -t opea/multimodalqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 6. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd  GenAIExamples/MultimodalQnA/ui/
docker build --no-cache -t opea/multimodalqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following 11 Docker Images:

1. `opea/dataprep:latest`
2. `opea/lvm:latest`
3. `ghcr.io/huggingface/tgi-gaudi:2.0.6`
4. `opea/retriever:latest`
5. `opea/whisper:latest`
6. `opea/redis-vector-db`
7. `opea/embedding:latest`
8. `opea/embedding-multimodal-bridgetower:latest`
9. `opea/multimodalqna:latest`
10. `opea/multimodalqna-ui:latest`

## 🚀 Start Microservices

### Required Models

By default, the multimodal-embedding and LVM models are set to a default value as listed below:

| Service   | Model                                       |
| --------- | ------------------------------------------- |
| embedding | BridgeTower/bridgetower-large-itm-mlm-gaudi |
| LVM       | llava-hf/llava-v1.6-vicuna-13b-hf           |

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/MultimodalQnA/docker_compose/intel/hpu/gaudi/
docker compose -f compose.yaml up -d
```

### Validate Microservices

1. embedding-multimodal-bridgetower

```bash
curl http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example"}'
```

```bash
curl http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'
```

2. embedding

```bash
curl http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"text" : "This is some sample text."}'
```

```bash
curl http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"text": {"text" : "This is some sample text."}, "image" : {"url": "https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true"}}'
```

3. retriever-multimodal-redis

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
curl http://${host_ip}:7000/v1/multimodal_retrieval \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"test\",\"embedding\":${your_embedding}}"
```

4. whisper

```bash
curl ${WHISPER_SERVER_ENDPOINT} \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"audio" : "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}'
```

5. TGI LLaVA Gaudi Server

```bash
curl http://${host_ip}:${LLAVA_SERVER_PORT}/generate \
    -X POST \
    -d '{"inputs":"![](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/rabbit.png)What is this a picture of?\n\n","parameters":{"max_new_tokens":16, "seed": 42}}' \
    -H 'Content-Type: application/json'
```

6. lvm

```bash
curl http://${host_ip}:${LVM_PORT}/v1/lvm \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [{"b64_img_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "transcript_for_inference": "yellow image", "video_id": "8c7461df-b373-4a00-8696-9a2234359fe0", "time_of_frame_ms":"37000000", "source_video":"WeAreGoingOnBullrun_8c7461df-b373-4a00-8696-9a2234359fe0.mp4"}], "chat_template":"The caption of the image is: '\''{context}'\''. {question}"}'
```

```bash
curl http://${host_ip}:${LVM_PORT}/v1/lvm  \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?"}'
```

Also, validate LVM TGI Gaudi Server with empty retrieval results

```bash
curl http://${host_ip}:${LVM_PORT}/v1/lvm \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [], "chat_template":"The caption of the image is: '\''{context}'\''. {question}"}'
```

7. Multimodal Dataprep Microservice

Download a sample video, image, PDF, and audio file and create a caption

```bash
export video_fn="WeAreGoingOnBullrun.mp4"
wget http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4 -O ${video_fn}

export image_fn="apple.png"
wget https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true -O ${image_fn}

export pdf_fn="nke-10k-2023.pdf"
wget https://raw.githubusercontent.com/opea-project/GenAIComps/v1.1/comps/retrievers/redis/data/nke-10k-2023.pdf -O ${pdf_fn}

export caption_fn="apple.txt"
echo "This is an apple."  > ${caption_fn}

export audio_fn="AudioSample.wav"
wget https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav -O ${audio_fn}
```

Test dataprep microservice with generating transcript. This command updates a knowledge base by uploading a local video .mp4 and an audio .wav file.

```bash
curl --silent --write-out "HTTPSTATUS:%{http_code}" \
    ${DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT} \
    -H 'Content-Type: multipart/form-data' \
    -X POST \
    -F "files=@./${video_fn}" \
    -F "files=@./${audio_fn}"
```

Also, test dataprep microservice with generating an image caption using lvm

```bash
curl --silent --write-out "HTTPSTATUS:%{http_code}" \
    ${DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT} \
    -H 'Content-Type: multipart/form-data' \
    -X POST -F "files=@./${image_fn}"
```

Now, test the microservice with posting a custom caption along with an image and a PDF containing images and text.

```bash
curl --silent --write-out "HTTPSTATUS:%{http_code}" \
    ${DATAPREP_INGEST_SERVICE_ENDPOINT} \
    -H 'Content-Type: multipart/form-data' \
    -X POST -F "files=@./${image_fn}" -F "files=@./${caption_fn}" \
    -F "files=@./${pdf_fn}"
```

Also, you are able to get the list of all files that you uploaded:

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"file_path": "all"}' \
    ${DATAPREP_GET_FILE_ENDPOINT}
```

Then you will get the response python-style LIST like this. Notice the name of each uploaded file e.g., `videoname.mp4` will become `videoname_uuid.mp4` where `uuid` is a unique ID for each uploaded file. The same files that are uploaded twice will have different `uuid`.

```bash
[
    "WeAreGoingOnBullrun_7ac553a1-116c-40a2-9fc5-deccbb89b507.mp4",
    "WeAreGoingOnBullrun_6d13cf26-8ba2-4026-a3a9-ab2e5eb73a29.mp4",
    "apple_fcade6e6-11a5-44a2-833a-3e534cbe4419.png",
    "nke-10k-2023_28000757-5533-4b1b-89fe-7c0a1b7e2cd0.pdf",
    "AudioSample_976a85a6-dc3e-43ab-966c-9d81beef780c.wav"
]
```

To delete all uploaded files along with data indexed with `$INDEX_NAME` in REDIS.

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    ${DATAPREP_DELETE_FILE_ENDPOINT}
```

8. MegaService

Test the MegaService with a text query:

```bash
curl http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"messages": "What is the revenue of Nike in 2023?"}'
```

Test the MegaService with an audio query:

```bash
curl http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna  \
    -H "Content-Type: application/json"  \
    -d '{"messages": [{"role": "user", "content": [{"type": "audio", "audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}]}]}'
```

Test the MegaService with a text and image query:

```bash
curl http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna \
    -H "Content-Type: application/json" \
    -d  '{"messages": [{"role": "user", "content": [{"type": "text", "text": "Green bananas in a tree"}, {"type": "image_url", "image_url": {"url": "http://images.cocodataset.org/test-stuff2017/000000004248.jpg"}}]}]}'
```

Test the MegaService with a back and forth conversation between the user and assistant:

```bash
curl http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna \
	-H "Content-Type: application/json" \
	-d '{"messages": [{"role": "user", "content": [{"type": "text", "text": "hello, "}, {"type": "image_url", "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"}}]}, {"role": "assistant", "content": "opea project! "}, {"role": "user", "content": "chao, "}], "max_tokens": 10}'
```
