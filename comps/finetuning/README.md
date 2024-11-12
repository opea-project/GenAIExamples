# Fine-tuning Microservice

Fine-tuning microservice involves adapting a model to a specific task or dataset to improve its performance on that task, we currently supported instruction tuning for LLMs, finetuning for reranking and embedding models.

## 🚀1. Start Microservice with Python (Option 1)

### 1.1 Install Requirements

```bash
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install intel-extension-for-pytorch
python -m pip install oneccl_bind_pt --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/cpu/us/
pip install -r requirements.txt
```

### 1.2 Start Finetuning Service with Python Script

#### 1.2.1 Start Ray Cluster

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

#### 1.2.2 Start Finetuning Service

```bash
export HF_TOKEN=${your_huggingface_token}
python finetuning_service.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Setup on CPU

#### 2.1.1 Build Docker Image

Build docker image with below command:

```bash
export HF_TOKEN=${your_huggingface_token}
cd ../../
docker build -t opea/finetuning:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg HF_TOKEN=$HF_TOKEN -f comps/finetuning/Dockerfile .
```

#### 2.1.2 Run Docker with CLI

Start docker container with below command:

```bash
docker run -d --name="finetuning-server" -p 8015:8015 --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/finetuning:latest
```

### 2.2 Setup on Gaudi2

#### 2.2.1 Build Docker Image

Build docker image with below command:

```bash
cd ../../
docker build -t opea/finetuning-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/finetuning/Dockerfile.intel_hpu .
```

#### 2.2.2 Run Docker with CLI

Start docker container with below command:

```bash
export HF_TOKEN=${your_huggingface_token}
docker run --runtime=habana -e HABANA_VISIBLE_DEVICES=all -p 8015:8015 -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --net=host --ipc=host -e https_proxy=$https_proxy -e http_proxy=$http_proxy -e no_proxy=$no_proxy -e HF_TOKEN=$HF_TOKEN opea/finetuning-gaudi:latest
```

## 🚀3. Consume Finetuning Service

### 3.1 Upload a training file

Download a training file, such as `alpaca_data.json` for instruction tuning and upload it to the server with below command, this file can be downloaded in [here](https://github.com/tatsu-lab/stanford_alpaca/blob/main/alpaca_data.json):

```bash
# upload a training file
curl http://${your_ip}:8015/v1/files -X POST -H "Content-Type: multipart/form-data" -F "file=@./alpaca_data.json" -F purpose="fine-tune"
```

For reranking and embedding models finetuning, the training file [toy_finetune_data.jsonl](https://github.com/FlagOpen/FlagEmbedding/blob/1.1/examples/finetune/toy_finetune_data.jsonl) is an toy example.

### 3.2 Create fine-tuning job

#### 3.2.1 Instruction Tuning

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

#### 3.2.2 Reranking Model Training

Use the following command to launch a finetuning job for reranking model finetuning, such as `BAAI/bge-reranker-large`:

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

#### 3.2.3 Embedding Model Training

Use the following command to launch a finetuning job for embedding model finetuning, such as `BAAI/bge-base-en-v1.5`:

```bash
# create a finetuning job
curl http://${your_ip}:8015/v1/fine_tuning/jobs \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "training_file": "toy_finetune_data.jsonl",
    "model": "BAAI/bge-base-en-v1.5",
    "General":{
      "task":"embedding",
      "lora_config":null
    }
  }'


# If training on Gaudi2, we need to set --padding "max_length" and the value of --query_max_len is same with --passage_max_len for static shape during training. For example:
curl http://${your_ip}:8015/v1/fine_tuning/jobs \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "training_file": "toy_finetune_data.jsonl",
    "model": "BAAI/bge-base-en-v1.5",
    "General":{
      "task":"embedding",
      "lora_config":null
    },
    "Dataset":{
      "query_max_len":128,
      "passage_max_len":128,
      "padding":"max_length"
    }
  }'


```

#### 3.2.4 LLM Pretraining

Use the following command to launch a job for LLM pretraining, such as `meta-llama/Llama-2-7b-hf`:

```bash
# create a finetuning job
curl http://${your_ip}:8015/v1/fine_tuning/jobs \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "training_file": "test_data.json",
    "model": "meta-llama/Llama-2-7b-hf",
    "General":{
      "task":"pretraining",
      "lora_config":null
    }
  }'
```

Below is an example for the format of the pretraining dataset:

```json
{"text": "A girl with a blue tank top sitting watching three dogs."}
{"text": "A boy with a blue tank top sitting watching three dogs."}
```

#### 3.2.5 Direct Preference Optimization (DPO)

Use the following command to launch a job for LLM Direct Preference Optimization, such as `meta-llama/Llama-2-7b-hf`:

```bash
# create a finetuning job
curl http://${your_ip}:8015/v1/fine_tuning/jobs \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "training_file": "test_data.jsonl",
    "model": "meta-llama/Llama-2-7b-hf",
    "General":{
      "task":"dpo"
    }
  }'
```

Below is an example for the format of the DPO dataset:

```json
{"system": "", "question": "You will be given a definition of a task first, then some input of the task.\nThis task is about using the specified sentence and converting the sentence to Resource Description Framework (RDF) triplets of the form (subject, predicate object). The RDF triplets generated must be such that the triplets accurately capture the structure and semantics of the input sentence. The input is a sentence and the output is a list of triplets of the form [subject, predicate, object] that capture the relationships present in the sentence. When a sentence has more than 1 RDF triplet possible, the output must contain all of them.\n\nAFC Ajax (amateurs)'s ground is Sportpark De Toekomst where Ajax Youth Academy also play.\nOutput:", "chosen": "[\n  [\"AFC Ajax (amateurs)\", \"has ground\", \"Sportpark De Toekomst\"],\n  [\"Ajax Youth Academy\", \"plays at\", \"Sportpark De Toekomst\"]\n]", "rejected": " Sure, I'd be happy to help! Here are the RDF triplets for the input sentence:\n\n[AFC Ajax (amateurs), hasGround, Sportpark De Toekomst]\n[Ajax Youth Academy, playsAt, Sportpark De Toekomst]\n\nExplanation:\n\n* AFC Ajax (amateurs) is the subject of the first triplet, and hasGround is the predicate that describes the relationship between AFC Ajax (amateurs) and Sportpark De Toekomst.\n* Ajax Youth Academy is the subject of the second triplet, and playsAt is the predicate that describes the relationship between Ajax Youth Academy and Sportpark De Toekomst.\n\nNote that there may be other possible RDF triplets that could be derived from the input sentence, but the above triplets capture the main relationships present in the sentence."}
{"system": "You are an AI assistant. You will be given a task. You must generate a detailed and long answer.", "question": "Generate an approximately fifteen-word sentence that describes all this data: Midsummer House eatType restaurant; Midsummer House food Chinese; Midsummer House priceRange moderate; Midsummer House customer rating 3 out of 5; Midsummer House near All Bar One", "chosen": "Midsummer House is a moderately priced Chinese restaurant with a 3/5 customer rating, located near All Bar One.", "rejected": " Sure! Here's a sentence that describes all the data you provided:\n\n\"Midsummer House is a moderately priced Chinese restaurant with a customer rating of 3 out of 5, located near All Bar One, offering a variety of delicious dishes.\""}
```

### 3.3 Manage fine-tuning job

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

### 3.4 Leverage fine-tuned model

After fine-tuning job is done, fine-tuned model can be chosen from listed checkpoints, then the fine-tuned model can be used in other microservices. For example, fine-tuned reranking model can be used in [reranks](../reranks/fastrag/README.md) microservice by assign its path to the environment variable `RERANK_MODEL_ID`, fine-tuned embedding model can be used in [embeddings](../embeddings/README.md) microservice by assign its path to the environment variable `model`, LLMs after instruction tuning can be used in [llms](../llms/text-generation/README.md) microservice by assign its path to the environment variable `your_hf_llm_model`.

## 🚀4. Descriptions for Finetuning parameters

We utilize [OpenAI finetuning parameters](https://platform.openai.com/docs/api-reference/fine-tuning) and extend it with more customizable parameters, see the definitions at [finetune_config](https://github.com/opea-project/GenAIComps/blob/main/comps/finetuning/finetune_config.py).
