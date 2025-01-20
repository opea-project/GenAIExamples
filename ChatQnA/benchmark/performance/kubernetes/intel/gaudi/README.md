# ChatQnA Benchmarking

This folder contains a collection of Kubernetes manifest files for deploying the ChatQnA service across scalable nodes. It includes a comprehensive [benchmarking tool](https://github.com/opea-project/GenAIEval/blob/main/evals/benchmark/README.md) that enables throughput analysis to assess inference performance.

By following this guide, you can run benchmarks on your deployment and share the results with the OPEA community.

## Purpose

We aim to run these benchmarks and share them with the OPEA community for three primary reasons:

- To offer insights on inference throughput in real-world scenarios, helping you choose the best service or deployment for your needs.
- To establish a baseline for validating optimization solutions across different implementations, providing clear guidance on which methods are most effective for your use case.
- To inspire the community to build upon our benchmarks, allowing us to better quantify new solutions in conjunction with current leading llms, serving frameworks etc.

## Metrics

The benchmark will report the below metrics, including:

- Number of Concurrent Requests
- End-to-End Latency: P50, P90, P99 (in milliseconds)
- End-to-End First Token Latency: P50, P90, P99 (in milliseconds)
- Average Next Token Latency (in milliseconds)
- Average Token Latency (in milliseconds)
- Requests Per Second (RPS)
- Output Tokens Per Second
- Input Tokens Per Second

Results will be displayed in the terminal and saved as CSV file named `1_stats.csv` for easy export to spreadsheets.

## Table of Contents

- [Deployment](#deployment)
  - [Prerequisites](#prerequisites)
  - [Deployment Scenarios](#deployment-scenarios)
    - [Case 1: Baseline Deployment with Rerank](#case-1-baseline-deployment-with-rerank)
    - [Case 2: Baseline Deployment without Rerank](#case-2-baseline-deployment-without-rerank)
    - [Case 3: Tuned Deployment with Rerank](#case-3-tuned-deployment-with-rerank)
- [Benchmark](#benchmark)
  - [Test Configurations](#test-configurations)
  - [Test Steps](#test-steps)
    - [Upload Retrieval File](#upload-retrieval-file)
    - [Run Benchmark Test](#run-benchmark-test)
    - [Data collection](#data-collection)
- [Teardown](#teardown)

## Deployment

### Prerequisites

- Kubernetes installation: Use [kubespray](https://github.com/opea-project/docs/blob/main/guide/installation/k8s_install/k8s_install_kubespray.md) or other official Kubernetes installation guides: 
- (Optional) [Kubernetes set up guide on Intel Gaudi product](https://github.com/opea-project/GenAIInfra/blob/main/README.md#setup-kubernetes-cluster) 
- Helm installation: Follow the [Helm documentation](https://helm.sh/docs/intro/install/#helm) to install Helm.
- Setup Hugging Face Token

  To access models and APIs from Hugging Face, set your token as environment variable.
  ```bash
  export HF_TOKEN="insert-your-huggingface-token-here"
  ```
- Prepare Shared Models (Optional but Strongly Recommended)

  Downloading models simultaneously to multiple nodes in your cluster can overload resources such as network bandwidth, memory and storage. To prevent resource exhaustion, it's recommended to preload the models in advance.
  ```bash
  pip install -U "huggingface_hub[cli]"
  sudo mkdir -p /mnt/models
  sudo chmod 777 /mnt/models
  huggingface-cli download --cache-dir /mnt/models Intel/neural-chat-7b-v3-3
  export MODEL_DIR=/mnt/models
  ```
  Once the models are downloaded, you can consider the following methods for sharing them across nodes:
  - Persistent Volume Claim (PVC): This is the recommended approach for production setups. For more details on using PVC, refer to [PVC](https://github.com/opea-project/GenAIInfra/blob/main/helm-charts/README.md#using-persistent-volume).
  - Local Host Path: For simpler testing, ensure that each node involved in the deployment follows the steps above to locally prepare the models. After preparing the models, use `--set global.modelUseHostPath=${MODELDIR}` in the deployment command.

- Label Nodes
  ```base
  python deploy.py --add-label --num-nodes 2
  ```

### Deployment Scenarios

The example below are based on a two-node setup. You can adjust the number of nodes by using the `--num-nodes` option.

By default, these commands use the `default` namespace. To specify a different namespace, use the `--namespace` flag with deploy, uninstall, and kubernetes command. Additionally, update the `namespace` field in `benchmark.yaml` before running the benchmark test.

For additional configuration options, run `python deploy.py --help`

#### Case 1: Baseline Deployment with Rerank

Deploy Command (with node number, Hugging Face token, model directory specified):
```bash
python deploy.py --hf-token $HF_TOKEN --model-dir $MODEL_DIR --num-nodes 2 --with-rerank
```
Uninstall Command:
```bash
python deploy.py --uninstall
```

#### Case 2: Baseline Deployment without Rerank

```bash
python deploy.py --hf-token $HFTOKEN --model-dir $MODELDIR --num-nodes 2
```
#### Case 3: Tuned Deployment with Rerank

```bash
python deploy.py --hf-token $HFTOKEN --model-dir $MODELDIR --num-nodes 2 --with-rerank --tuned
```

## Benchmark

### Test Configurations

| Key      | Value   |
| -------- | ------- |
| Workload | ChatQnA |
| Tag      | V1.1    |

Models configuration
| Key | Value |
| ---------- | ------------------ |
| Embedding | BAAI/bge-base-en-v1.5 |
| Reranking | BAAI/bge-reranker-base |
| Inference | Intel/neural-chat-7b-v3-3 |

Benchmark parameters
| Key | Value |
| ---------- | ------------------ |
| LLM input tokens | 1024 |
| LLM output tokens | 128 |

Number of test requests for different scheduled node number:
| Node count | Concurrency | Query number |
| ----- | -------- | -------- |
| 1 | 128 | 640 |
| 2 | 256 | 1280 |
| 4 | 512 | 2560 |

More detailed configuration can be found in configuration file [benchmark.yaml](./benchmark.yaml).

### Test Steps

Use `kubectl get pods` to confirm that all pods are `READY` before starting the test.

#### Upload Retrieval File

Before testing, upload a specified file to make sure the llm input have the token length of 1k.

Get files:

```bash
wget https://github.com/opea-project/GenAIEval/tree/main/evals/benchmark/data/upload_file.txt
```

Retrieve the `ClusterIP` of the `chatqna-data-prep` service.

```bash
kubectl get svc
```
Expected output:
```log
chatqna-data-prep         ClusterIP   xx.xx.xx.xx    <none>        6007/TCP            51m
```

Use the following `cURL` command to upload file:

```bash
cd GenAIEval/evals/benchmark/data
curl -X POST "http://${cluster_ip}:6007/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F "chunk_size=3800" \
     -F "files=@./upload_file.txt"
```

#### Run Benchmark Test

Run the benchmark test using:
```bash
bash benchmark.sh -n 2
```
The `-n` argument specifies the number of test nodes. Required dependencies will be automatically installed when running the benchmark for the first time.

#### Data collection

All the test results will come to the folder `GenAIEval/evals/benchmark/benchmark_output`.

## Teardown

After completing the benchmark, use the following command to clean up the environment:

Remove Node Labels:
```bash
python deploy.py --delete-label
```
