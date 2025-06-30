# Deploying MultimodalQnA on Intel® Gaudi® Processors

This document outlines the deployment process for a MultimodalQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `multimodal_embedding` that employs [BridgeTower](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) model as embedding model, `multimodal_retriever`, `lvm`, and `multimodal-data-prep`.

## Table of Contents

1. [MultimodalQnA Quick Start Deployment](#multimodalqna-quick-start-deployment)
2. [MultimodalQnA Docker Compose Files](#multimodalqna-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## MultimodalQnA Quick Start Deployment

This section describes how to quickly deploy and test the MultimodalQnA service manually on an Intel® Gaudi® processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExamples repository and access the MultimodalQnA Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/MultimodalQnA
```

Then checkout a released version, such as v1.3:

```bash
git checkout v1.3
```

### Configure the Deployment Environment

To set up environment variables for deploying MultimodalQnA services, set up some parameters specific to the deployment environment and source the `set_env.sh` script in this directory:

```bash
export host_ip="External_Public_IP"           # ip address of the node
export HF_TOKEN="Your_HuggingFace_API_Token"
export http_proxy="Your_HTTP_Proxy"           # http proxy if any
export https_proxy="Your_HTTPs_Proxy"         # https proxy if any
export no_proxy=localhost,127.0.0.1,$host_ip  # additional no proxies if needed
cd docker_compose/intel
source set_env.sh
```

Consult the section on [MultimodalQnA Service configuration](#multimodalqna-docker-compose-files) for information on how service specific configuration parameters affect deployments.

### Deploy the Services Using Docker Compose

To deploy the MultimodalQnA services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute the command below. It uses the 'compose.yaml' file.

```bash
cd hpu/gaudi
docker compose -f compose.yaml up -d
```

Alternatively, to use Milvus vector database instead of Redis:

```bash
export MILVUS_HOST=${host_ip}
export MILVUS_PORT=19530
export MILVUS_RETRIEVER_PORT=7000
export COLLECTION_NAME=mm_rag_milvus

docker compose -f compose_milvus.yaml up -d
```

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment, the following 12 containers should have started:

```
| CONTAINER ID | IMAGE                                               | COMMAND                       | STATUS       | PORTS                                          | NAMES                                  |
| ------------ | --------------------------------------------------- | ----------------------------- | ------------ | ---------------------------------------------- | -------------------------------------- |
| `abcde001`   | redis/redis-stack:7.2.0-v9                          | redis-stack-server            | Up 2 minutes | 0.0.0.0:6379->6379/tcp, 0.0.0.0:8001->8001/tcp | redis-vector-db                        |
| `abcde002`   | opea/whisper\:latest                                | docker-entrypoint.sh          | Up 2 minutes | 0.0.0.0:7066->7066/tcp                         | whisper-service                        |
| `abcde003`   | opea/speecht5\:latest                               | docker-entrypoint.sh          | Up 2 minutes | 0.0.0.0:7055->7055/tcp                         | speecht5-service                       |
| `abcde004`   | opea/dataprep\:latest                               | docker-entrypoint.sh          | Up 2 minutes | 0.0.0.0:6007->5000/tcp                         | dataprep-multimodal-redis              |
| `abcde005`   | opea/embedding-multimodal-bridgetower-gaudi\:latest | python bridgetower\_server.py | Up 2 minutes | 0.0.0.0:7050->7050/tcp                | embedding-multimodal-bridgetower-gaudi |
| `abcde006`   | opea/embedding\:latest                              | docker-entrypoint.sh          | Up 2 minutes | 0.0.0.0:7061->7061/tcp                   | embedding                              |
| `abcde007`   | opea/retriever\:latest                              | docker-entrypoint.sh          | Up 2 minutes | 0.0.0.0:7000->7000/tcp                    | retriever-redis                        |
| `abcde008`   | ghcr.io/huggingface/tgi-gaudi:2.3.1                 | /entrypoint.sh ...            | Up 2 minutes | 0.0.0.0:8399->8399/tcp                  | tgi-llava-gaudi-server                 |
| `abcde009`   | opea/lvm\:latest                                    | docker-entrypoint.sh          | Up 2 minutes | 0.0.0.0:9399->9399/tcp                  | lvm                                    |
| `abcde010`   | opea/multimodalqna\:latest                          | docker-entrypoint.sh          | Up 2 minutes | 0.0.0.0:8888->8888/tcp                   | multimodalqna-backend-server           |
| `abcde011`   | opea/multimodalqna-ui\:latest                       | docker-entrypoint.sh          | Up 2 minutes | 0.0.0.0:5173->5173/tcp                   | multimodalqna-gradio-ui-server         |

```

For the Milvus deployment, the following 13 containers should have started:

```
| CONTAINER ID   | IMAGE                                               | COMMAND                          | STATUS       | PORTS                                            | NAMES                                  |
| -------------- | --------------------------------------------------- | -------------------------------- | ------------ | ------------------------------------------------ | -------------------------------------- |
| `a1c3e7d1a1c1` | opea/multimodalqna-ui\:latest                       | "docker-entrypoint.sh"           | Up 3 minutes | 0.0.0.0:5173->5173/tcp                           | multimodalqna-gradio-ui-server         |
| `a2c3e7d1a2c2` | opea/multimodalqna\:latest                          | "docker-entrypoint.sh"           | Up 3 minutes | 0.0.0.0:8888->8888/tcp                           | multimodalqna-backend-server           |
| `a3c3e7d1a3c3` | opea/lvm\:latest                                    | "docker-entrypoint.sh"           | Up 3 minutes | 0.0.0.0:9399->9399/tcp                           | lvm                                    |
| `a4c3e7d1a4c4` | ghcr.io/huggingface/tgi-gaudi:2.3.1                 | "/start-inference-server.sh"     | Up 3 minutes | 0.0.0.0:8399->8399/tcp                           | tgi-llava-gaudi-server                 |
| `a5c3e7d1a5c5` | opea/retriever\:latest                              | "docker-entrypoint.sh"           | Up 3 minutes | 0.0.0.0:7000->7000/tcp                           | retriever-milvus                       |
| `a6c3e7d1a6c6` | opea/embedding\:latest                              | "docker-entrypoint.sh"           | Up 3 minutes | 0.0.0.0:7061->7061/tcp                           | embedding                              |
| `a7c3e7d1a7c7` | opea/embedding-multimodal-bridgetower-gaudi\:latest | "python bridgetower\_server.py…" | Up 3 minutes | 0.0.0.0:7050->7050/tcp                           | embedding-multimodal-bridgetower-gaudi |
| `a8c3e7d1a8c8` | opea/dataprep\:latest                               | "docker-entrypoint.sh"           | Up 3 minutes | 0.0.0.0:6007->5000/tcp                           | dataprep-multimodal-milvus             |
| `a9c3e7d1a9c9` | milvusdb/milvus\:v2.4.6                             | "milvus run standalone"          | Up 3 minutes | 0.0.0.0:19530->19530/tcp, 0.0.0.0:9091->9091/tcp | milvus-standalone                      |
| `b0c3e7d1b0c0` | minio/minio\:RELEASE.2023-03-20T20-16-18Z           | "minio server /minio\_data …"    | Up 3 minutes | 0.0.0.0:5043->9000/tcp, 0.0.0.0:5044->9001/tcp   | milvus-minio                           |
| `b1c3e7d1b1c1` | quay.io/coreos/etcd\:v3.5.5                         | "etcd -advertise-client-urls…"   | Up 3 minutes | *None exposed*                                   | milvus-etcd                            |
| `b2c3e7d1b2c2` | opea/whisper\:latest                                | "docker-entrypoint.sh"           | Up 3 minutes | 0.0.0.0:7066->7066/tcp                           | whisper-service                        |
```

### Validate the Pipeline

Once the MultimodalQnA services are running, test the pipeline using the following command:

```bash
DATA='{"messages": [{"role": "user", "content": [{"type": "audio", "audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}]}]}'

curl http://${HOST_IP}:8888/v1/multimodalqna \
  -H "Content-Type: application/json" \
  -d "$DATA"
```

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
docker compose -f compose.yaml down
# if used milvus
# docker compose -f compose_milvus.yaml down
```

## MultimodalQnA Docker Compose Files

| File                                         | Description                                               |
| -------------------------------------------- | --------------------------------------------------------- |
| [compose.yaml](./compose.yaml)               | Default pipeline using Redis as vector store.             |
| [compose_milvus.yaml](./compose_milvus.yaml) | Variant using Milvus as vector database instead of Redis. |

## Validate Microservices

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
   curl http://${host_ip}:${REDIS_RETRIEVER_PORT}/v1/retrieval \
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

6. tts

   ```bash
   curl ${TTS_ENDPOINT} \
   -X POST \
   -d '{"text": "Who are you?"}' \
   -H 'Content-Type: application/json'
   ```

7. lvm

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

8. Multimodal Dataprep Microservice

   Download a sample video (.mp4), image (.png, .gif, .jpg), pdf, and audio file (.wav, .mp3) and create a caption

   ```bash
   export video_fn="WeAreGoingOnBullrun.mp4"
   wget http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4 -O ${video_fn}

   export image_fn="apple.png"
   wget https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true -O ${image_fn}

   export pdf_fn="nke-10k-2023.pdf"
   wget https://raw.githubusercontent.com/opea-project/GenAIComps/v1.3/comps/third_parties/pathway/src/data/nke-10k-2023.pdf -O ${pdf_fn}

   export caption_fn="apple.txt"
   echo "This is an apple."  > ${caption_fn}

   export audio_fn="AudioSample.wav"
   wget https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav -O ${audio_fn}
   ```

   Test dataprep microservice with generating transcript. This command updates a knowledge base by uploading a local video .mp4 and an audio .wav or .mp3 file.

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

   Now, test the microservice with posting a custom caption along with an image and a PDF containing images and text. The image caption can be provided as a text (`.txt`) or as spoken audio (`.wav` or `.mp3`).

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
       -d '{"file_path": "all"}' \
       ${DATAPREP_DELETE_FILE_ENDPOINT}
   ```

9. MegaService

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

   Test the MegaService with a back and forth conversation between the user and assistant including a text to speech response from the assistant using `"modalities": ["text", "audio"]'`:

   ```bash
   curl http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna \
       -H "Content-Type: application/json" \
       -d '{"messages": [{"role": "user", "content": [{"type": "text", "text": "hello, "}, {"type": "image_url", "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"}}]}, {"role": "assistant", "content": "opea project! "}, {"role": "user", "content": "chao, "}], "max_tokens": 10, "modalities": ["text", "audio"]}'
   ```

## Conclusion

This guide enables developers to deploy MultimodalQnA on Intel Gaudi processors with minimal setup. Configuration is handled via a single environment script, while modular Docker Compose files provide flexible deployment options across different vector store backends (Redis or Milvus). After deployment, validation can be performed both through direct API calls and the provided user interface.
