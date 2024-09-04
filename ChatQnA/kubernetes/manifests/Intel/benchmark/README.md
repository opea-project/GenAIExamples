# ChatQnA Benchmarking

This folder contains a collection of Kubernetes manifest files for deploying the ChatQnA service across scalable nodes. It includes a comprehensive [benchmarking tool](https://github.com/opea-project/GenAIEval/blob/main/evals/benchmark/README.md) that enables throughput analysis to assess inference performance.

By following this guide, you can run benchmarks on your deployment and share the results with the OPEA community.

# Purpose

We aim to run these benchmarks and share them with the OPEA community for three primary reasons:

- To offer insights on inference throughput in real-world scenarios, helping you choose the best service or deployment for your needs.
- To establish a baseline for validating optimization solutions across different implementations, providing clear guidance on which methods are most effective for your use case.
- To inspire the community to build upon our benchmarks, allowing us to better quantify new solutions in conjunction with current leading llms, serving frameworks etc.

# Metrics

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

# Getting Started

## Prerequisites

- Install Kubernetes by following [this guide](https://github.com/opea-project/docs/blob/main/guide/installation/k8s_install/k8s_install_kubespray.md).

- Every node has direct internet access
- Set up kubectl on the master node with access to the Kubernetes cluster.
- Install Python 3.8+ on the master node for running the stress tool.
- Ensure all nodes have a local /mnt/models folder, which will be mounted by the pods.

## Kubernetes Cluster Example

```bash
$ kubectl get nodes
NAME                STATUS   ROLES           AGE   VERSION
k8s-master          Ready    control-plane   35d   v1.29.6
k8s-work1           Ready    <none>          35d   v1.29.5
k8s-work2           Ready    <none>          35d   v1.29.6
k8s-work3           Ready    <none>          35d   v1.29.6
```

## Manifest preparation

We have created the [BKC manifest](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/benchmark) for single node, two nodes and four nodes K8s cluster. In order to apply, we need to check out and configure some values.

```bash
# on k8s-master node
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA/benchmark

# replace the image tag from latest to v0.9 since we want to test with v0.9 release
IMAGE_TAG=v0.9
find . -name '*.yaml' -type f -exec sed -i "s#image: opea/\(.*\):latest#image: opea/\1:${IMAGE_TAG}#g" {} \;

# set the huggingface token
HUGGINGFACE_TOKEN=<your token>
find . -name '*.yaml' -type f -exec sed -i "s#\${HF_TOKEN}#${HUGGINGFACE_TOKEN}#g" {} \;

# set models
LLM_MODEL_ID=Intel/neural-chat-7b-v3-3
EMBEDDING_MODEL_ID=BAAI/bge-base-en-v1.5
RERANK_MODEL_ID=BAAI/bge-reranker-base
find . -name '*.yaml' -type f -exec sed -i "s#\$(LLM_MODEL_ID)#${LLM_MODEL_ID}#g" {} \;
find . -name '*.yaml' -type f -exec sed -i "s#\$(EMBEDDING_MODEL_ID)#${EMBEDDING_MODEL_ID}#g" {} \;
find . -name '*.yaml' -type f -exec sed -i "s#\$(RERANK_MODEL_ID)#${RERANK_MODEL_ID}#g" {} \;
```

## Benchmark tool preparation

The test uses the [benchmark tool](https://github.com/opea-project/GenAIEval/tree/main/evals/benchmark) to do performance test. We need to set up benchmark tool at the master node of Kubernetes which is k8s-master.

```bash
# on k8s-master node
git clone https://github.com/opea-project/GenAIEval.git
cd GenAIEval
python3 -m venv stress_venv
source stress_venv/bin/activate
pip install -r requirements.txt
```

## Test Configurations

Workload configuration:

| Key      | Value   |
| -------- | ------- |
| Workload | ChatQnA |
| Tag      | V0.9    |

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

## Test Steps

### Single node test

#### 1. Preparation

We add label to 1 Kubernetes node to make sure all pods are scheduled to this node:

```bash
kubectl label nodes k8s-worker1 node-type=chatqna-opea
```

#### 2. Install ChatQnA

Go to [BKC manifest](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/benchmark/single_gaudi) and apply to K8s.

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/single_gaudi
kubectl apply -f .
```

#### 3. Run tests

##### 3.1 Upload Retrieval File

Before running tests, upload a specified file to make sure the llm input have the token length of 1k.

Run the following command to check the cluster ip of dataprep.

```bash
kubectl get svc
```

Substitute the `${cluster_ip}` into the real cluster ip of dataprep microservice as below.

```log
dataprep-svc   ClusterIP   xx.xx.xx.xx    <none>   6007/TCP   5m   app=dataprep-deploy
```

Run the cURL command to upload file:

```bash
cd GenAIEval/evals/benchmark/data
# RAG with Rerank
curl -X POST "http://${cluster_ip}:6007/v1/dataprep" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@./upload_file.txt" \
     -F "chunk_size=3800"
# RAG without Rerank
curl -X POST "http://${cluster_ip}:6007/v1/dataprep" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@./upload_file_no_rerank.txt"
```

##### 3.2 Run Benchmark Test

We copy the configuration file [benchmark.yaml](./benchmark.yaml) to `GenAIEval/evals/benchmark/benchmark.yaml` and config `test_suite_config.user_queries` and `test_suite_config.test_output_dir`.

```bash
export USER_QUERIES="[4, 8, 16, 640]"
export TEST_OUTPUT_DIR="/home/sdp/benchmark_output/node_1"
envsubst < ./benchmark.yaml > GenAIEval/evals/benchmark/benchmark.yaml
```

And then run the benchmark tool by:

```bash
cd GenAIEval/evals/benchmark
python benchmark.py
```

#### 4. Data collection

All the test results will come to this folder `/home/sdp/benchmark_output/node_1` configured by the environment variable `TEST_OUTPUT_DIR` in previous steps.

#### 5. Clean up

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/single_gaudi
kubectl delete -f .
kubectl label nodes k8s-worker1 node-type-
```

### Two node test

#### 1. Preparation

We add label to 2 Kubernetes node to make sure all pods are scheduled to this node:

```bash
kubectl label nodes k8s-worker1 k8s-worker2 node-type=chatqna-opea
```

#### 2. Install ChatQnA

Go to [BKC manifest](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/benchmark/two_gaudi) and apply to K8s.

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/two_gaudi
kubectl apply -f .
```

#### 3. Run tests

We copy the configuration file [benchmark.yaml](./benchmark.yaml) to `GenAIEval/evals/benchmark/benchmark.yaml` and config `test_suite_config.user_queries` and `test_suite_config.test_output_dir`.

```bash
export USER_QUERIES="[4, 8, 16, 1280]"
export TEST_OUTPUT_DIR="/home/sdp/benchmark_output/node_2"
envsubst < ./benchmark.yaml > GenAIEval/evals/benchmark/benchmark.yaml
```

And then run the benchmark tool by:

```bash
cd GenAIEval/evals/benchmark
python benchmark.py
```

#### 4. Data collection

All the test results will come to this folder `/home/sdp/benchmark_output/node_2` configured by the environment variable `TEST_OUTPUT_DIR` in previous steps.

#### 5. Clean up

```bash
# on k8s-master node
kubectl delete -f .
kubectl label nodes k8s-worker1 k8s-worker2 node-type-
```

### Four node test

#### 1. Preparation

We add label to 4 Kubernetes node to make sure all pods are scheduled to this node:

```bash
kubectl label nodes k8s-master k8s-worker1 k8s-worker2 k8s-worker3 node-type=chatqna-opea
```

#### 2. Install ChatQnA

Go to [BKC manifest](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/benchmark/four_gaudi) and apply to K8s.

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/four_gaudi
kubectl apply -f .
```

#### 3. Run tests

We copy the configuration file [benchmark.yaml](./benchmark.yaml) to `GenAIEval/evals/benchmark/benchmark.yaml` and config `test_suite_config.user_queries` and `test_suite_config.test_output_dir`.

```bash
export USER_QUERIES="[4, 8, 16, 2560]"
export TEST_OUTPUT_DIR="/home/sdp/benchmark_output/node_4"
envsubst < ./benchmark.yaml > GenAIEval/evals/benchmark/benchmark.yaml
```

And then run the benchmark tool by:

```bash
cd GenAIEval/evals/benchmark
python benchmark.py
```

#### 4. Data collection

All the test results will come to this folder `/home/sdp/benchmark_output/node_4` configured by the environment variable `TEST_OUTPUT_DIR` in previous steps.

#### 5. Clean up

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/single_gaudi
kubectl delete -f .
kubectl label nodes k8s-master k8s-worker1 k8s-worker2 k8s-worker3 node-type-
```

### Example Result

The following is a summary of the test result, with files saved at `TEST_OUTPUT_DIR`.

```none
Concurrency       : 512
Max request count : 2560
Http timeout      : 60000

Benchmark target  : chatqnafixed

=================Total statistics=====================
Succeed Response:  2560 (Total 2560, 100.0% Success), Duration: 26.44s, Input Tokens: 61440, Output Tokens: 255985, RPS: 96.82, Input Tokens per Second: 2323.71, Output Tokens per Second: 9681.57
End to End latency(ms),    P50: 3576.34,   P90: 4242.19,   P99: 5252.23,   Avg: 3581.55
First token latency(ms),   P50: 726.64,   P90: 1128.27,   P99: 1796.09,   Avg: 769.58
Average Next token latency(ms): 28.41
Average token latency(ms)     : 35.85
======================================================
```

```none
benchmarkresult:
  Average_Next_token_latency: '28.41'
  Average_token_latency: '35.85'
  Duration: '26.44'
  End_to_End_latency_Avg: '3581.55'
  End_to_End_latency_P50: '3576.34'
  End_to_End_latency_P90: '4242.19'
  End_to_End_latency_P99: '5252.23'
  First_token_latency_Avg: '769.58'
  First_token_latency_P50: '726.64'
  First_token_latency_P90: '1128.27'
  First_token_latency_P99: '1796.09'
  Input_Tokens: '61440'
  Input_Tokens_per_Second: '2323.71'
  Onput_Tokens: '255985'
  Output_Tokens_per_Second: '9681.57'
  RPS: '96.82'
  Succeed_Response: '2560'
  locust_P50: '160'
  locust_P99: '810'
  locust_num_failures: '0'
  locust_num_requests: '2560'
benchmarkspec:
  bench-target: chatqnafixed
  endtest_time: '2024-08-25T14:19:25.955973'
  host: http://10.110.105.197:8888
  llm-model: Intel/neural-chat-7b-v3-3
  locustfile: /home/sdp/lvl/GenAIEval/evals/benchmark/stresscli/locust/aistress.py
  max_requests: 2560
  namespace: default
  processes: 2
  run_name: benchmark
  runtime: 60m
  starttest_time: '2024-08-25T14:18:50.366514'
  stop_timeout: 120
  tool: locust
  users: 512
hardwarespec:
  aise-gaudi-00:
    architecture: amd64
    containerRuntimeVersion: containerd://1.7.18
    cpu: '160'
    habana.ai/gaudi: '8'
    kernelVersion: 5.15.0-92-generic
    kubeProxyVersion: v1.29.7
    kubeletVersion: v1.29.7
    memory: 1056375272Ki
    operatingSystem: linux
    osImage: Ubuntu 22.04.3 LTS
  aise-gaudi-01:
    architecture: amd64
    containerRuntimeVersion: containerd://1.7.18
    cpu: '160'
    habana.ai/gaudi: '8'
    kernelVersion: 5.15.0-92-generic
    kubeProxyVersion: v1.29.7
    kubeletVersion: v1.29.7
    memory: 1056375256Ki
    operatingSystem: linux
    osImage: Ubuntu 22.04.3 LTS
  aise-gaudi-02:
    architecture: amd64
    containerRuntimeVersion: containerd://1.7.18
    cpu: '160'
    habana.ai/gaudi: '8'
    kernelVersion: 5.15.0-92-generic
    kubeProxyVersion: v1.29.7
    kubeletVersion: v1.29.7
    memory: 1056375260Ki
    operatingSystem: linux
    osImage: Ubuntu 22.04.3 LTS
  aise-gaudi-03:
    architecture: amd64
    containerRuntimeVersion: containerd://1.6.8
    cpu: '160'
    habana.ai/gaudi: '8'
    kernelVersion: 5.15.0-112-generic
    kubeProxyVersion: v1.29.7
    kubeletVersion: v1.29.7
    memory: 1056374404Ki
    operatingSystem: linux
    osImage: Ubuntu 22.04.4 LTS
workloadspec:
  aise-gaudi-00:
    chatqna-backend-server-deploy:
      replica: 1
      resources:
        limits:
          cpu: '8'
          memory: 4000Mi
        requests:
          cpu: '8'
          memory: 4000Mi
    embedding-dependency-deploy:
      replica: 1
      resources:
        limits:
          cpu: '80'
          memory: 20000Mi
        requests:
          cpu: '80'
          memory: 20000Mi
    embedding-deploy:
      replica: 1
    llm-dependency-deploy:
      replica: 8
      resources:
        limits:
          habana.ai/gaudi: '1'
        requests:
          habana.ai/gaudi: '1'
    llm-deploy:
      replica: 1
    retriever-deploy:
      replica: 1
      resources:
        limits:
          cpu: '8'
          memory: 2500Mi
        requests:
          cpu: '8'
          memory: 2500Mi
  aise-gaudi-01:
    chatqna-backend-server-deploy:
      replica: 1
      resources:
        limits:
          cpu: '8'
          memory: 4000Mi
        requests:
          cpu: '8'
          memory: 4000Mi
    embedding-dependency-deploy:
      replica: 1
      resources:
        limits:
          cpu: '80'
          memory: 20000Mi
        requests:
          cpu: '80'
          memory: 20000Mi
    embedding-deploy:
      replica: 1
    llm-dependency-deploy:
      replica: 8
      resources:
        limits:
          habana.ai/gaudi: '1'
        requests:
          habana.ai/gaudi: '1'
    llm-deploy:
      replica: 1
    prometheus-operator:
      replica: 1
      resources:
        limits:
          cpu: 200m
          memory: 200Mi
        requests:
          cpu: 100m
          memory: 100Mi
    retriever-deploy:
      replica: 1
      resources:
        limits:
          cpu: '8'
          memory: 2500Mi
        requests:
          cpu: '8'
          memory: 2500Mi
  aise-gaudi-02:
    chatqna-backend-server-deploy:
      replica: 1
      resources:
        limits:
          cpu: '8'
          memory: 4000Mi
        requests:
          cpu: '8'
          memory: 4000Mi
    embedding-dependency-deploy:
      replica: 1
      resources:
        limits:
          cpu: '80'
          memory: 20000Mi
        requests:
          cpu: '80'
          memory: 20000Mi
    embedding-deploy:
      replica: 1
    llm-dependency-deploy:
      replica: 8
      resources:
        limits:
          habana.ai/gaudi: '1'
        requests:
          habana.ai/gaudi: '1'
    llm-deploy:
      replica: 1
    retriever-deploy:
      replica: 1
      resources:
        limits:
          cpu: '8'
          memory: 2500Mi
        requests:
          cpu: '8'
          memory: 2500Mi
  aise-gaudi-03:
    chatqna-backend-server-deploy:
      replica: 1
      resources:
        limits:
          cpu: '8'
          memory: 4000Mi
        requests:
          cpu: '8'
          memory: 4000Mi
    dataprep-deploy:
      replica: 1
    embedding-dependency-deploy:
      replica: 1
      resources:
        limits:
          cpu: '80'
          memory: 20000Mi
        requests:
          cpu: '80'
          memory: 20000Mi
    embedding-deploy:
      replica: 1
    llm-dependency-deploy:
      replica: 8
      resources:
        limits:
          habana.ai/gaudi: '1'
        requests:
          habana.ai/gaudi: '1'
    llm-deploy:
      replica: 1
    retriever-deploy:
      replica: 1
      resources:
        limits:
          cpu: '8'
          memory: 2500Mi
        requests:
          cpu: '8'
          memory: 2500Mi
    vector-db:
      replica: 1
```
