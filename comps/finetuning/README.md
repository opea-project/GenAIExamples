# LLM Fine-tuning Microservice

LLM Fine-tuning microservice involves adapting a base model to a specific task or dataset to improve its performance on that task.

# 🚀1. Start Microservice with Python (Optional 1)

## 1.1 Install Requirements

```bash
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install intel-extension-for-pytorch
python -m pip install oneccl_bind_pt --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/cpu/us/
pip install -r requirements.txt
```

## 1.2 Start Finetuning Service with Python Script

### 1.2.1 Start Ray Cluster

OneCCL and Intel MPI libraries should be dynamically linked in every node before Ray starts:

```bash
source $(python -c "import oneccl_bindings_for_pytorch as torch_ccl; print(torch_ccl.cwd)")/env/setvars.sh
```

Start Ray locally using the following command.

```bash
ray start --head
```

For a multi-node cluster, start additional Ray worker nodes with below command.

```bash
ray start --address='${head_node_ip}:6379'
```

### 1.2.2 Start Finetuning Service

```bash
export HF_TOKEN=${your_huggingface_token}
python finetuning_service.py
```

# 🚀2. Start Microservice with Docker (Optional 2)

## 2.1 Setup on CPU

### 2.1.1 Build Docker Image

Build docker image with below command:

```bash
export HF_TOKEN=${your_huggingface_token}
cd ../../
docker build -t opea/finetuning:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg HF_TOKEN=$HF_TOKEN -f comps/finetuning/docker/Dockerfile_cpu .
```

### 2.1.2 Run Docker with CLI

Start docker container with below command:

```bash
docker run -d --name="finetuning-server" -p 8015:8015 --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/finetuning:latest
```

## 2.2 Setup on Gaudi2

### 2.2.1 Build Docker Image

Build docker image with below command:

```bash
cd ../../
docker build -t opea/finetuning-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/finetuning/docker/Dockerfile_hpu .
```

### 2.2.2 Run Docker with CLI

Start docker container with below command:

```bash
export HF_TOKEN=${your_huggingface_token}
docker run --runtime=habana -e HABANA_VISIBLE_DEVICES=all -p 8015:8015 -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --net=host --ipc=host -e https_proxy=$https_proxy -e http_proxy=$http_proxy -e no_proxy=$no_proxy -e HF_TOKEN=$HF_TOKEN opea/finetuning-gaudi:latest
```

# 🚀3. Consume Finetuning Service

## 3.1 Create fine-tuning job

Assuming a training file `alpaca_data.json` is uploaded, it can be downloaded in [here](https://github.com/tatsu-lab/stanford_alpaca/blob/main/alpaca_data.json), the following script launches a finetuning job using `meta-llama/Llama-2-7b-chat-hf` as base model:

```bash
# upload a training file
curl http://${your_ip}:8015/v1/files -X POST -H "Content-Type: multipart/form-data" -F "file=@./alpaca_data.json" -F purpose="fine-tune"

# create a finetuning job
curl http://${your_ip}:8015/v1/fine_tuning/jobs \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "training_file": "alpaca_data.json",
    "model": "meta-llama/Llama-2-7b-chat-hf"
  }'

# list finetuning jobs
curl http://${your_ip}:8015/v1/fine_tuning/jobs   -X GET

# retrieve one finetuning job
curl http://localhost:8015/v1/fine_tuning/jobs/retrieve   -X POST   -H "Content-Type: application/json"   -d '{
    "fine_tuning_job_id": ${fine_tuning_job_id}}'

# cancel one finetuning job
curl http://localhost:8015/v1/fine_tuning/jobs/cancel   -X POST   -H "Content-Type: application/json"   -d '{
    "fine_tuning_job_id": ${fine_tuning_job_id}}'

# list checkpoints of a finetuning job
curl http://${your_ip}:8015/v1/finetune/list_checkpoints -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": ${fine_tuning_job_id}}'


```

# 🚀4. Descriptions for Finetuning parameters

We utilize [OpenAI finetuning parameters](https://platform.openai.com/docs/api-reference/fine-tuning) and extend it with more customizable parameters.
