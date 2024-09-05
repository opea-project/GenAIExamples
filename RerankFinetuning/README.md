# Rerank Model Finetuning

Rerank model finetuning is the process of further training rerank model on a dataset for improving its capability on specific field.

## Deploy Rerank Model Finetuning Service

### Deploy Rerank Model Finetuning Service on Xeon

Refer to the [Xeon Guide](./docker/xeon/README.md) for detail.

## Consume Rerank Model Finetuning Service

### 1. Upload a training file

Download a toy example training file `toy_finetune_data.jsonl` and upload it to the server with below command, this file can be downloaded in [here](https://github.com/FlagOpen/FlagEmbedding/blob/master/examples/finetune/toy_finetune_data.jsonl):

```bash
# upload a training file
curl http://${your_ip}:8015/v1/files -X POST -H "Content-Type: multipart/form-data" -F "file=@./toy_finetune_data.jsonl" -F purpose="fine-tune"
```

### 2. Create fine-tuning job

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
curl http://localhost:8015/v1/fine_tuning/jobs/retrieve -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": ${fine_tuning_job_id}}'

# cancel one finetuning job
curl http://localhost:8015/v1/fine_tuning/jobs/cancel -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": ${fine_tuning_job_id}}'

# list checkpoints of a finetuning job
curl http://${your_ip}:8015/v1/finetune/list_checkpoints -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": ${fine_tuning_job_id}}'
```
