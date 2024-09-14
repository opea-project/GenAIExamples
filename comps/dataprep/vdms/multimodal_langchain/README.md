# Multimodal Dataprep Microservice with VDMS

For dataprep microservice, we currently provide one framework: `Langchain`.

## 🚀1. Start Microservice with Python (Option 1)

### 1.1 Install Requirements

- option 1: Install Single-process version (for 1-10 files processing)

  ```bash
  apt-get update
  apt-get install -y default-jre tesseract-ocr libtesseract-dev poppler-utils
  pip install -r requirements.txt
  ```

### 1.2 Start VDMS Server

```bash
docker run -d --name="vdms-vector-db" -p 55555:55555 intellabs/vdms:latest
```

### 1.3 Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export host_ip=$(hostname -I | awk '{print $1}')
export VDMS_HOST=${host_ip}
export VDMS_PORT=55555
export INDEX_NAME="rag-vdms"
export your_hf_api_token="{your_hf_token}"
export PYTHONPATH=${path_to_comps}
```

### 1.4 Start Data Preparation Microservice for VDMS with Python Script

Start document preparation microservice for VDMS with below command.

```bash
python ingest_videos.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Start VDMS Server

```bash
docker run -d --name="vdms-vector-db" -p 55555:55555 intellabs/vdms:latest
```

### 2.1 Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export host_ip=$(hostname -I | awk '{print $1}')
export VDMS_HOST=${host_ip}
export VDMS_PORT=55555
export INDEX_NAME="rag-vdms"
export your_hf_api_token="{your_hf_token}"
```

### 2.3 Build Docker Image

- Build docker image

  ```bash
  cd ../../../
  docker build -t opea/dataprep-vdms:latest --network host --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/vdms/multimodal_langchain/Dockerfile .

  ```

### 2.4 Run Docker Compose

```bash
docker compose -f comps/dataprep/vdms/multimodal_langchain/docker-compose-dataprep-vdms.yaml up -d
```

## 🚀3. Status Microservice

```bash
docker container logs -f dataprep-vdms-server
```

## 🚀4. Consume Microservice

Once data preparation microservice for VDMS is started, user can use below command to invoke the microservice to convert the videos to embedding and save to the database.

Make sure the file path after `files=@` is correct.

- Single file upload

  ```bash
  curl -X POST \
       -H "Content-Type: multipart/form-data" \
       -F "files=@./file1.mp4" \
       http://localhost:6007/v1/dataprep
  ```

- Multiple file upload

  ```bash
  curl -X POST \
       -H "Content-Type: multipart/form-data" \
       -F "files=@./file1.mp4" \
       -F "files=@./file2.mp4" \
       -F "files=@./file3.mp4" \
       http://localhost:6007/v1/dataprep
  ```

- List of uploaded files

  ```bash
  curl -X GET http://localhost:6007/v1/dataprep/get_videos
  ```

- Download uploaded files

  Use the file name from the list

  ```bash
  curl -X GET http://localhost:6007/v1/dataprep/get_file/${filename}
  ```
