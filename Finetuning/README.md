# Finetuning

This example includes instruction tuning and rerank model finetuning. Instruction tuning is the process of further training LLMs on a dataset consisting of (instruction, output) pairs in a supervised fashion, which bridges the gap between the next-word prediction objective of LLMs and the users' objective of having LLMs adhere to human instructions. Rerank model finetuning is the process of further training rerank model on a dataset for improving its capability on specific field. The implementation of this example deploys a Ray cluster for the task.

## Deploy Finetuning Service

### Deploy Finetuning Service on Xeon

Refer to the [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) for detail.

### Deploy Finetuning Service on Gaudi

Refer to the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) for detail.

## Consume Finetuning Service

### 1. Upload a training file

#### Instruction tuning dataset example

Download a training file `alpaca_data.json` and upload it to the server with below command, this file can be downloaded in [here](https://github.com/tatsu-lab/stanford_alpaca/blob/main/alpaca_data.json):

```bash
# upload a training file
curl http://${your_ip}:8015/v1/files -X POST -H "Content-Type: multipart/form-data" -F "file=@./alpaca_data.json" -F purpose="fine-tune"
```

#### Rerank model finetuning dataset example

Download a toy example training file `toy_finetune_data.jsonl` and upload it to the server with below command, this file can be downloaded in [here](https://github.com/FlagOpen/FlagEmbedding/blob/JUNJIE99-patch-1/examples/finetune/toy_finetune_data.jsonl):

```bash
# upload a training file
curl http://${your_ip}:8015/v1/files -X POST -H "Content-Type: multipart/form-data" -F "file=@./toy_finetune_data.jsonl" -F purpose="fine-tune"
```

### 2. Create fine-tuning job

#### Instruction tuning

After a training file like `alpaca_data.json` is uploaded, use the following command to launch a finetuning job using `meta-llama/Llama-2-7b-chat-hf` as base model:

```bash
# create a finetuning job
curl http://${your_ip}:8015/v1/fine_tuning/jobs \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "training_file": "alpaca_data.json",
    "model": "meta-llama/Llama-2-7b-chat-hf"
  }'
```

The outputs of the finetune job (adapter_model.safetensors, adapter_config,json... ) are stored in `/home/user/comps/finetuning/src/output` and other execution logs are stored in `/home/user/ray_results`

#### Rerank model finetuning

After a training file `toy_finetune_data.jsonl` is uploaded, use the following command to launch a finetuning job using `BAAI/bge-reranker-large` as base model:

```bash
# create a finetuning job
curl http://${your_ip}:8015/v1/fine_tuning/jobs \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "training_file": "toy_finetune_data.jsonl",
    "model": "BAAI/bge-reranker-large",
    "General":{
      "task":"rerank",
      "lora_config":null
    }
  }'
```

### 3. Manage fine-tuning job

Below commands show how to list finetuning jobs, retrieve a finetuning job, cancel a finetuning job and list checkpoints of a finetuning job.

```bash
# list finetuning jobs
curl http://${your_ip}:8015/v1/fine_tuning/jobs -X GET

# retrieve one finetuning job
curl http://${your_ip}:8015/v1/fine_tuning/jobs/retrieve -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": ${fine_tuning_job_id}}'

# cancel one finetuning job
curl http://${your_ip}:8015/v1/fine_tuning/jobs/cancel -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": ${fine_tuning_job_id}}'

# list checkpoints of a finetuning job
curl http://${your_ip}:8015/v1/finetune/list_checkpoints -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": ${fine_tuning_job_id}}'
```
