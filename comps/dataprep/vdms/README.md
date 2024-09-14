# Dataprep Microservice with VDMS

For dataprep microservice, we currently provide one framework: `Langchain`.

<!-- We also provide `Langchain_ray` which uses ray to parallel the data prep for multi-file performance improvement(observed 5x - 15x speedup by processing 1000 files/links.). -->

We organized the folders in the same way, so you can use either framework for dataprep microservice with the following constructions.

## 🚀1. Start Microservice with Python (Option 1)

### 1.1 Install Requirements

Install Single-process version (for 1-10 files processing)

```bash
apt-get update
apt-get install -y default-jre tesseract-ocr libtesseract-dev poppler-utils
cd langchain
pip install -r requirements.txt
```

<!-- - option 2: Install multi-process version (for >10 files processing)

```bash
cd langchain_ray; pip install -r requirements_ray.txt
``` -->

### 1.2 Start VDMS Server

Refer to this [readme](../../vectorstores/vdms/README.md).

### 1.3 Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export VDMS_HOST=${host_ip}
export VDMS_PORT=55555
export COLLECTION_NAME=${your_collection_name}
export PYTHONPATH=${path_to_comps}
```

### 1.4 Start Document Preparation Microservice for VDMS with Python Script

Start document preparation microservice for VDMS with below command.

Start single-process version (for 1-10 files processing)

```bash
python prepare_doc_vdms.py
```

<!-- - option 2: Start multi-process version (for >10 files processing)

```bash
python prepare_doc_redis_on_ray.py
``` -->

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Start VDMS Server

Refer to this [readme](../../vectorstores/vdms/README.md).

### 2.2 Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export VDMS_HOST=${host_ip}
export VDMS_PORT=55555
export TEI_ENDPOINT=${your_tei_endpoint}
export COLLECTION_NAME=${your_collection_name}
export SEARCH_ENGINE="FaissFlat"
export DISTANCE_STRATEGY="L2"
export PYTHONPATH=${path_to_comps}
```

### 2.3 Build Docker Image

- Build docker image with langchain

  Start single-process version (for 1-10 files processing)

  ```bash
  cd ../../../
  docker build -t opea/dataprep-vdms:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/vdms/langchain/Dockerfile .
  ```

<!-- - option 2: Start multi-process version (for >10 files processing)

```bash
cd ../../../../
docker build -t opea/dataprep-on-ray-vdms:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/vdms/langchain_ray/Dockerfile . -->

### 2.4 Run Docker with CLI

Start single-process version (for 1-10 files processing)

```bash
docker run -d --name="dataprep-vdms-server" -p 6007:6007 --runtime=runc --ipc=host \
-e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_ENDPOINT=$TEI_ENDPOINT \
-e COLLECTION_NAME=$COLLECTION_NAME -e VDMS_HOST=$VDMS_HOST -e VDMS_PORT=$VDMS_PORT \
opea/dataprep-vdms:latest
```

<!-- - option 2: Start multi-process version (for >10 files processing)

```bash
docker run -d --name="dataprep-vdms-server" -p 6007:6007 --runtime=runc --ipc=host \
-e http_proxy=$http_proxy -e https_proxy=$https_proxy \
-e COLLECTION_NAME=$COLLECTION_NAME -e VDMS_HOST=$VDMS_HOST -e VDMS_PORT=$VDMS_PORT \
-e TIMEOUT_SECONDS=600 opea/dataprep-on-ray-vdms:latest
``` -->

## 🚀3. Status Microservice

```bash
docker container logs -f dataprep-vdms-server
```

## 🚀4. Consume Microservice

Once document preparation microservice for VDMS is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

Make sure the file path after `files=@` is correct.

- Single file upload

  ```bash
  curl -X POST \
       -H "Content-Type: multipart/form-data" \
       -F "files=@./file1.txt" \
       http://localhost:6007/v1/dataprep
  ```

  You can specify `chunk_size` and `chunk_overlap` by the following commands.

  ```bash
  curl -X POST \
       -H "Content-Type: multipart/form-data" \
       -F "files=@./LLAMA2_page6.pdf" \
       -F "chunk_size=1500" \
       -F "chunk_overlap=100" \
       http://localhost:6007/v1/dataprep
  ```

- Multiple file upload

  ```bash
  curl -X POST \
       -H "Content-Type: multipart/form-data" \
       -F "files=@./file1.txt" \
       -F "files=@./file2.txt" \
       -F "files=@./file3.txt" \
       http://localhost:6007/v1/dataprep
  ```

- Links upload (not supported for `llama_index` now)

  ```bash
  curl -X POST \
       -F 'link_list=["https://www.ces.tech/"]' \
       http://localhost:6007/v1/dataprep
  ```

  or

  ```python
  import requests
  import json

  proxies = {"http": ""}
  url = "http://localhost:6007/v1/dataprep"
  urls = [
      "https://towardsdatascience.com/no-gpu-no-party-fine-tune-bert-for-sentiment-analysis-with-vertex-ai-custom-jobs-d8fc410e908b?source=rss----7f60cf5620c9---4"
  ]
  payload = {"link_list": json.dumps(urls)}

  try:
      resp = requests.post(url=url, data=payload, proxies=proxies)
      print(resp.text)
      resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
      print("Request successful!")
  except requests.exceptions.RequestException as e:
      print("An error occurred:", e)
  ```
