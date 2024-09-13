# Dataprep Microservice for Multimodal Data with Redis

This `dataprep` microservice accepts videos (mp4 files) and their transcripts (optional) from the user and ingests them into Redis vectorstore.

## 🚀1. Start Microservice with Python（Option 1）

### 1.1 Install Requirements

```bash
# Install ffmpeg static build
wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz
mkdir ffmpeg-git-amd64-static
tar -xvf ffmpeg-git-amd64-static.tar.xz -C ffmpeg-git-amd64-static --strip-components 1
export PATH=$(pwd)/ffmpeg-git-amd64-static:$PATH
cp $(pwd)/ffmpeg-git-amd64-static/ffmpeg /usr/local/bin/

pip install -r requirements.txt
```

### 1.2 Start Redis Stack Server

Please refer to this [readme](../../../../vectorstores/redis/README.md).

### 1.3 Setup Environment Variables

```bash
export your_ip=$(hostname -I | awk '{print $1}')
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_redis_index_name}
export PYTHONPATH=${path_to_comps}
```

### 1.4 Start LVM Microservice (Optional)

This is required only if you are going to consume the _generate_captions_ API of this microservice as in [Section 4.3](#43-consume-generate_captions-api).

Please refer to this [readme](../../../../lvms/llava/README.md) to start the LVM microservice.
After LVM is up, set up environment variables.

```bash
export your_ip=$(hostname -I | awk '{print $1}')
export LVM_ENDPOINT="http://${your_ip}:9399/v1/lvm"
```

### 1.5 Start Data Preparation Microservice for Redis with Python Script

Start document preparation microservice for Redis with below command.

```bash
python prepare_videodoc_redis.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Start Redis Stack Server

Please refer to this [readme](../../../../vectorstores/redis/README.md).

### 2.2 Start LVM Microservice (Optional)

This is required only if you are going to consume the _generate_captions_ API of this microservice as described [here](#43-consume-generate_captions-api).

Please refer to this [readme](../../../../lvms/llava/README.md) to start the LVM microservice.
After LVM is up, set up environment variables.

```bash
export your_ip=$(hostname -I | awk '{print $1}')
export LVM_ENDPOINT="http://${your_ip}:9399/v1/lvm"
```

### 2.3 Setup Environment Variables

```bash
export your_ip=$(hostname -I | awk '{print $1}')
export EMBEDDING_MODEL_ID="BridgeTower/bridgetower-large-itm-mlm-itc"
export REDIS_URL="redis://${your_ip}:6379"
export WHISPER_MODEL="base"
export INDEX_NAME=${your_redis_index_name}
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
```

### 2.4 Build Docker Image

```bash
cd ../../../../
docker build -t opea/dataprep-multimodal-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/multimodal/redis/langchain/Dockerfile .
```

### 2.5 Run Docker with CLI (Option A)

```bash
docker run -d --name="dataprep-multimodal-redis" -p 6007:6007 --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e LVM_ENDPOINT=$LVM_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN opea/dataprep-multimodal-redis:latest
```

### 2.6 Run with Docker Compose (Option B - deprecated, will move to genAIExample in future)

```bash
cd comps/dataprep/multimodal/redis/langchain
docker compose -f docker-compose-dataprep-redis.yaml up -d
```

## 🚀3. Status Microservice

```bash
docker container logs -f dataprep-multimodal-redis
```

## 🚀4. Consume Microservice

Once this dataprep microservice is started, user can use the below commands to invoke the microservice to convert videos and their transcripts (optional) to embeddings and save to the Redis vector store.

This mircroservice has provided 3 different ways for users to ingest videos into Redis vector store corresponding to the 3 use cases.

### 4.1 Consume _videos_with_transcripts_ API

**Use case:** This API is used when a transcript file (under `.vtt` format) is available for each video.

**Important notes:**

- Make sure the file paths after `files=@` are correct.
- Every transcript file's name must be identical with its corresponding video file's name (except their extension .vtt and .mp4). For example, `video1.mp4` and `video1.vtt`. Otherwise, if `video1.vtt` is not included correctly in this API call, this microservice will return error `No captions file video1.vtt found for video1.mp4`.

#### Single video-transcript pair upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./video1.mp4" \
    -F "files=@./video1.vtt" \
    http://localhost:6007/v1/videos_with_transcripts
```

#### Multiple video-transcript pair upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./video1.mp4" \
    -F "files=@./video1.vtt" \
    -F "files=@./video2.mp4" \
    -F "files=@./video2.vtt" \
    http://localhost:6007/v1/videos_with_transcripts
```

### 4.2 Consume _generate_transcripts_ API

**Use case:** This API should be used when a video has meaningful audio or recognizable speech but its transcript file is not available.

In this use case, this microservice will use [`whisper`](https://openai.com/index/whisper/) model to generate the `.vtt` transcript for the video.

#### Single video upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./video1.mp4" \
    http://localhost:6007/v1/generate_transcripts
```

#### Multiple video upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./video1.mp4" \
    -F "files=@./video2.mp4" \
    http://localhost:6007/v1/generate_transcripts
```

### 4.3 Consume _generate_captions_ API

**Use case:** This API should be used when a video does not have meaningful audio or does not have audio.

In this use case, transcript either does not provide any meaningful information or does not exist. Thus, it is preferred to leverage a LVM microservice to summarize the video frames.

- Single video upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./video1.mp4" \
    http://localhost:6007/v1/generate_captions
```

- Multiple video upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./video1.mp4" \
    -F "files=@./video2.mp4" \
    http://localhost:6007/v1/generate_captions
```

### 4.4 Consume get_videos API

To get names of uploaded videos, use the following command.

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    http://localhost:6007/v1/dataprep/get_videos
```

### 4.5 Consume delete_videos API

To delete uploaded videos and clear the database, use the following command.

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    http://localhost:6007/v1/dataprep/delete_videos
```
