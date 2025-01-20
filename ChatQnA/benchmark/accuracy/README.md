# ChatQnA Accuracy

ChatQnA is a Retrieval-Augmented Generation (RAG) pipeline, which can enhance generative models through external information retrieval.

For evaluating the accuracy, we use 2 latest published datasets and 10+ metrics which are popular and comprehensive:

- Dataset
  - [MultiHop](https://arxiv.org/pdf/2401.15391) (English dataset)
  - [CRUD](https://arxiv.org/abs/2401.17043) (Chinese dataset)
- metrics (measure accuracy of both the context retrieval and response generation)
  - evaluation for retrieval/reranking
    - MRR@10
    - MAP@10
    - Hits@10
    - Hits@4
    - LLM-as-a-Judge
  - evaluation for the generated response from the end-to-end pipeline
    - BLEU
    - ROGUE(L)
    - LLM-as-a-Judge

## Prerequisite

### Environment

```bash
git clone https://github.com/opea-project/GenAIEval
cd GenAIEval
pip install -r requirements.txt
pip install -e .
```

## MultiHop (English dataset)

[MultiHop-RAG](https://arxiv.org/pdf/2401.15391): a QA dataset to evaluate retrieval and reasoning across documents with metadata in the RAG pipelines. It contains 2556 queries, with evidence for each query distributed across 2 to 4 documents. The queries also involve document metadata, reflecting complex scenarios commonly found in real-world RAG applications.

### Launch Service of RAG System

Please refer to this [guide](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/README.md) to launch the service of `ChatQnA`.

### Launch Service of LLM-as-a-Judge

To setup a LLM model, we can use [tgi-gaudi](https://github.com/huggingface/tgi-gaudi) to launch a service. For example, the follow command is to setup the [mistralai/Mixtral-8x7B-Instruct-v0.1](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1) model on 2 Gaudi2 cards:

```
# please set your llm_port and hf_token

docker run -p {your_llm_port}:80 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e HF_TOKEN={your_hf_token} --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:2.0.1 --model-id mistralai/Mixtral-8x7B-Instruct-v0.1 --max-input-tokens 2048 --max-total-tokens 4096 --sharded true --num-shard 2

# for better performance, set `PREFILL_BATCH_BUCKET_SIZE`, `BATCH_BUCKET_SIZE`, `max-batch-total-tokens`, `max-batch-prefill-tokens`
docker run -p {your_llm_port}:80 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e HF_TOKEN={your_hf_token} -e PREFILL_BATCH_BUCKET_SIZE=1 -e BATCH_BUCKET_SIZE=8 --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:2.0.6 --model-id mistralai/Mixtral-8x7B-Instruct-v0.1 --max-input-tokens 2048 --max-total-tokens 4096 --sharded true --num-shard 2 --max-batch-total-tokens 65536 --max-batch-prefill-tokens 2048
```

### Prepare Dataset

We use the evaluation dataset from [MultiHop-RAG](https://github.com/yixuantt/MultiHop-RAG) repo, use the below command to prepare the dataset.

```bash
git clone https://github.com/yixuantt/MultiHop-RAG.git
```

### Evaluation

Use below command to run the evaluation, please note that for the first run, argument `--ingest_docs` should be added in the command to ingest the documents into the vector database, while for the subsequent run, this argument should be omitted. Set `--retrieval_metrics` to get retrieval related metrics (MRR@10/MAP@10/Hits@10/Hits@4). Set `--ragas_metrics` and `--llm_endpoint` to get end-to-end rag pipeline metrics (faithfulness/answer_relevancy/...), which are judged by LLMs. We set `--limits` is 100 as default, which means only 100 examples are evaluated by llm-as-judge as it is very time consuming.

If you are using docker compose to deploy `ChatQnA` system, you can simply run the evaluation as following:

```bash
python eval_multihop.py --docs_path MultiHop-RAG/dataset/corpus.json  --dataset_path MultiHop-RAG/dataset/MultiHopRAG.json --ingest_docs --retrieval_metrics --ragas_metrics --llm_endpoint http://{llm_as_judge_ip}:{llm_as_judge_port}/generate
```

If you are using Kubernetes manifest/helm to deploy `ChatQnA` system, you must specify more arguments as following:

```bash
python eval_multihop.py --docs_path MultiHop-RAG/dataset/corpus.json  --dataset_path MultiHop-RAG/dataset/MultiHopRAG.json --ingest_docs --retrieval_metrics --ragas_metrics --llm_endpoint http://{llm_as_judge_ip}:{llm_as_judge_port}/generate --database_endpoint http://{your_dataprep_ip}:{your_dataprep_port}/v1/dataprep/ingest --embedding_endpoint http://{your_embedding_ip}:{your_embedding_port}/v1/embeddings --tei_embedding_endpoint http://{your_tei_embedding_ip}:{your_tei_embedding_port} --retrieval_endpoint http://{your_retrieval_ip}:{your_retrieval_port}/v1/retrieval --service_url http://{your_chatqna_ip}:{your_chatqna_port}/v1/chatqna
```

The default values for arguments are:
|Argument|Default value|
|--------|-------------|
|service_url|http://localhost:8888/v1/chatqna|
|database_endpoint|http://localhost:6007/v1/dataprep/ingest|
|embedding_endpoint|http://localhost:6000/v1/embeddings|
|tei_embedding_endpoint|http://localhost:8090|
|retrieval_endpoint|http://localhost:7000/v1/retrieval|
|reranking_endpoint|http://localhost:8000/v1/reranking|
|output_dir|./output|
|temperature|0.1|
|max_new_tokens|1280|
|chunk_size|256|
|chunk_overlap|100|
|search_type|similarity|
|retrival_k|10|
|fetch_k|20|
|lambda_mult|0.5|
|dataset_path|None|
|docs_path|None|
|limits|100|

You can check arguments details use below command:

```bash
python eval_multihop.py --help
```

## CRUD (Chinese dataset)

[CRUD-RAG](https://arxiv.org/abs/2401.17043) is a Chinese benchmark for RAG (Retrieval-Augmented Generation) system. This example utilize CRUD-RAG for evaluating the RAG system.

### Prepare Dataset

We use the evaluation dataset from [CRUD-RAG](https://github.com/IAAR-Shanghai/CRUD_RAG) repo, use the below command to prepare the dataset.

```bash
git clone https://github.com/IAAR-Shanghai/CRUD_RAG
mkdir data/
cp CRUD_RAG/data/crud_split/split_merged.json data/
cp -r CRUD_RAG/data/80000_docs/ data/
python process_crud_dataset.py
```

### Launch Service of RAG System

Please refer to this [guide](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/README.md) to launch the service of `ChatQnA` system. For Chinese dataset, you should replace the English emebdding and llm model with Chinese, for example, `EMBEDDING_MODEL_ID="BAAI/bge-base-zh-v1.5"` and `LLM_MODEL_ID=Qwen/Qwen2-7B-Instruct`.

### Evaluation

Use below command to run the evaluation, please note that for the first run, argument `--ingest_docs` should be added in the command to ingest the documents into the vector database, while for the subsequent run, this argument should be omitted.

If you are using docker compose to deploy `ChatQnA` system, you can simply run the evaluation as following:

```bash
python eval_crud.py --dataset_path ./data/split_merged.json --docs_path ./data/80000_docs --ingest_docs

# if you want to get ragas metrics
python eval_crud.py --dataset_path ./data/split_merged.json --docs_path ./data/80000_docs  --contain_original_data --llm_endpoint "http://{llm_as_judge_ip}:{llm_as_judge_port}"  --ragas_metrics
```

If you are using Kubernetes manifest/helm to deploy `ChatQnA` system, you must specify more arguments as following:

```bash
python eval_crud.py --dataset_path ./data/split_merged.json --docs_path ./data/80000_docs --ingest_docs --database_endpoint http://{your_dataprep_ip}:{your_dataprep_port}/v1/dataprep/ingest --embedding_endpoint http://{your_embedding_ip}:{your_embedding_port}/v1/embeddings --retrieval_endpoint http://{your_retrieval_ip}:{your_retrieval_port}/v1/retrieval --service_url http://{your_chatqna_ip}:{your_chatqna_port}/v1/chatqna
```

The default values for arguments are:
|Argument|Default value|
|--------|-------------|
|service_url|http://localhost:8888/v1/chatqna|
|database_endpoint|http://localhost:6007/v1/dataprep/ingest|
|embedding_endpoint|http://localhost:6000/v1/embeddings|
|retrieval_endpoint|http://localhost:7000/v1/retrieval|
|reranking_endpoint|http://localhost:8000/v1/reranking|
|output_dir|./output|
|temperature|0.1|
|max_new_tokens|1280|
|chunk_size|256|
|chunk_overlap|100|
|dataset_path|./data/split_merged.json|
|docs_path|./data/80000_docs|
|tasks|["question_answering"]|

You can check arguments details use below command:

```bash
python eval_crud.py --help
```

## Acknowledgements

This example is mostly adapted from [MultiHop-RAG](https://github.com/yixuantt/MultiHop-RAG) and [CRUD-RAG](https://github.com/IAAR-Shanghai/CRUD_RAG) repo, we thank the authors for their great work!
