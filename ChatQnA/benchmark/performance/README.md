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

## Getting Started

We recommend using Kubernetes to deploy the ChatQnA service, as it offers benefits such as load balancing and improved scalability. However, you can also deploy the service using Docker if that better suits your needs. Below is a description of Kubernetes deployment and benchmarking. For instructions on deploying and benchmarking with Docker, please refer to [this section](#benchmark-with-docker).

### Prerequisites

- Install Kubernetes by following [this guide](https://github.com/opea-project/docs/blob/main/guide/installation/k8s_install/k8s_install_kubespray.md).

- Every node has direct internet access
- Set up kubectl on the master node with access to the Kubernetes cluster.
- Install Python 3.8+ on the master node for running the stress tool.
- Ensure all nodes have a local /mnt/models folder, which will be mounted by the pods.
- Ensure that the container's ulimit can meet the the number of requests.

```bash
# The way to modify the containered ulimit:
sudo systemctl edit containerd
# Add two lines:
[Service]
LimitNOFILE=65536:1048576

sudo systemctl daemon-reload; sudo systemctl restart containerd
```

### Kubernetes Cluster Example

```bash
$ kubectl get nodes
NAME                STATUS   ROLES           AGE   VERSION
k8s-master          Ready    control-plane   35d   v1.29.6
k8s-work1           Ready    <none>          35d   v1.29.5
k8s-work2           Ready    <none>          35d   v1.29.6
k8s-work3           Ready    <none>          35d   v1.29.6
```

### Manifest preparation

We have created the [BKC manifest](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/benchmark) for single node, two nodes and four nodes K8s cluster. In order to apply, we need to check out and configure some values.

```bash
# on k8s-master node
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA/benchmark/performance

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

### Benchmark tool preparation

The test uses the [benchmark tool](https://github.com/opea-project/GenAIEval/tree/main/evals/benchmark) to do performance test. We need to set up benchmark tool at the master node of Kubernetes which is k8s-master.

```bash
# on k8s-master node
git clone https://github.com/opea-project/GenAIEval.git
cd GenAIEval
python3 -m venv stress_venv
source stress_venv/bin/activate
pip install -r requirements.txt
```

### Test Configurations

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

### Test Steps

#### Single node test

##### 1. Preparation

We add label to 1 Kubernetes node to make sure all pods are scheduled to this node:

```bash
kubectl label nodes k8s-worker1 node-type=chatqna-opea
```

##### 2. Install ChatQnA

Go to [BKC manifest](./tuned/with_rerank/single_gaudi) and apply to K8s.

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/performance/tuned/with_rerank/single_gaudi
kubectl apply -f .
```

##### 3. Run tests

###### 3.1 Upload Retrieval File

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

###### 3.2 Run Benchmark Test

We copy the configuration file [benchmark.yaml](./benchmark.yaml) to `GenAIEval/evals/benchmark/benchmark.yaml` and config `test_suite_config.deployment_type`, `test_suite_config.service_ip`, `test_suite_config.service_port`, `test_suite_config.user_queries` and `test_suite_config.test_output_dir`.

```bash
export DEPLOYMENT_TYPE="k8s"
export SERVICE_IP = None
export SERVICE_PORT = None
export USER_QUERIES="[640, 640, 640, 640]"
export TEST_OUTPUT_DIR="/home/sdp/benchmark_output/node_1"
envsubst < ./benchmark.yaml > GenAIEval/evals/benchmark/benchmark.yaml
```

And then run the benchmark tool by:

```bash
cd GenAIEval/evals/benchmark
python benchmark.py
```

##### 4. Data collection

All the test results will come to this folder `/home/sdp/benchmark_output/node_1` configured by the environment variable `TEST_OUTPUT_DIR` in previous steps.

##### 5. Clean up

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/performance/tuned/with_rerank/single_gaudi
kubectl delete -f .
kubectl label nodes k8s-worker1 node-type-
```

#### Two node test

##### 1. Preparation

We add label to 2 Kubernetes node to make sure all pods are scheduled to this node:

```bash
kubectl label nodes k8s-worker1 k8s-worker2 node-type=chatqna-opea
```

##### 2. Install ChatQnA

Go to [BKC manifest](./tuned/with_rerank/two_gaudi) and apply to K8s.

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/performance/tuned/with_rerank/two_gaudi
kubectl apply -f .
```

##### 3. Run tests

We copy the configuration file [benchmark.yaml](./benchmark.yaml) to `GenAIEval/evals/benchmark/benchmark.yaml` and config `test_suite_config.deployment_type`, `test_suite_config.service_ip`, `test_suite_config.service_port`, `test_suite_config.user_queries` and `test_suite_config.test_output_dir`.

````bash
export DEPLOYMENT_TYPE="k8s"
export SERVICE_IP = None
export SERVICE_PORT = None
export USER_QUERIES="[1280, 1280, 1280, 1280]"
export TEST_OUTPUT_DIR="/home/sdp/benchmark_output/node_2"
envsubst < ./benchmark.yaml > GenAIEval/evals/benchmark/benchmark.yaml

And then run the benchmark tool by:

```bash
cd GenAIEval/evals/benchmark
python benchmark.py
````

##### 4. Data collection

All the test results will come to this folder `/home/sdp/benchmark_output/node_2` configured by the environment variable `TEST_OUTPUT_DIR` in previous steps.

##### 5. Clean up

```bash
# on k8s-master node
kubectl delete -f .
kubectl label nodes k8s-worker1 k8s-worker2 node-type-
```

#### Four node test

##### 1. Preparation

We add label to 4 Kubernetes node to make sure all pods are scheduled to this node:

```bash
kubectl label nodes k8s-master k8s-worker1 k8s-worker2 k8s-worker3 node-type=chatqna-opea
```

##### 2. Install ChatQnA

Go to [BKC manifest](./tuned/with_rerank/four_gaudi) and apply to K8s.

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/performance/tuned/with_rerank/four_gaudi
kubectl apply -f .
```

##### 3. Run tests

We copy the configuration file [benchmark.yaml](./benchmark.yaml) to `GenAIEval/evals/benchmark/benchmark.yaml` and config `test_suite_config.deployment_type`, `test_suite_config.service_ip`, `test_suite_config.service_port`, `test_suite_config.user_queries` and `test_suite_config.test_output_dir`.

```bash
export DEPLOYMENT_TYPE="k8s"
export SERVICE_IP = None
export SERVICE_PORT = None
export USER_QUERIES="[2560, 2560, 2560, 2560]"
export TEST_OUTPUT_DIR="/home/sdp/benchmark_output/node_4"
envsubst < ./benchmark.yaml > GenAIEval/evals/benchmark/benchmark.yaml
```

And then run the benchmark tool by:

```bash
cd GenAIEval/evals/benchmark
python benchmark.py
```

##### 4. Data collection

All the test results will come to this folder `/home/sdp/benchmark_output/node_4` configured by the environment variable `TEST_OUTPUT_DIR` in previous steps.

##### 5. Clean up

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/performance/tuned/with_rerank/single_gaudi
kubectl delete -f .
kubectl label nodes k8s-master k8s-worker1 k8s-worker2 k8s-worker3 node-type-
```

## Benchmark with Docker

### Deploy ChatQnA service with Docker

In order to set up the environment correctly, you'll need to configure essential environment variables and, if applicable, proxy-related variables.

```bash
# Example: host_ip="192.168.1.1"
export host_ip="External_Public_IP"
# Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
export no_proxy="Your_No_Proxy"
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
```

#### Deploy ChatQnA on Gaudi

```bash
cd GenAIExamples/ChatQnA/docker_compose/intel/hpu/gaudi/
docker compose up -d
```

Refer to the [Gaudi Guide](../../docker_compose/intel/hpu/gaudi/README.md) to build docker images from source.

#### Deploy ChatQnA on Xeon

```bash
cd GenAIExamples/ChatQnA/docker_compose/intel/cpu/xeon/
docker compose up -d
```

Refer to the [Xeon Guide](../../docker_compose/intel/cpu/xeon/README.md) for more instructions on building docker images from source.

#### Deploy ChatQnA on NVIDIA GPU

```bash
cd GenAIExamples/ChatQnA/docker_compose/nvidia/gpu/
docker compose up -d
```

Refer to the [NVIDIA GPU Guide](../../docker_compose/nvidia/gpu/README.md) for more instructions on building docker images from source.

### Run tests

We copy the configuration file [benchmark.yaml](./benchmark.yaml) to `GenAIEval/evals/benchmark/benchmark.yaml` and config `test_suite_config.deployment_type`, `test_suite_config.service_ip`, `test_suite_config.service_port`, `test_suite_config.user_queries` and `test_suite_config.test_output_dir`.

```bash
export DEPLOYMENT_TYPE="docker"
export SERVICE_IP = "ChatQnA Service IP"
export SERVICE_PORT = "ChatQnA Service Port"
export USER_QUERIES="[640, 640, 640, 640]"
export TEST_OUTPUT_DIR="/home/sdp/benchmark_output/docker"
envsubst < ./benchmark.yaml > GenAIEval/evals/benchmark/benchmark.yaml
```

And then run the benchmark tool by:

```bash
cd GenAIEval/evals/benchmark
python benchmark.py
```

### Data collection

All the test results will come to this folder `/home/sdp/benchmark_output/docker` configured by the environment variable `TEST_OUTPUT_DIR` in previous steps.

### Clean up

Take gaudi as example, use the below command to clean up system.

```bash
cd GenAIExamples/docker_compose/intel/hpu/gaudi
docker compose stop && docker compose rm -f
echo y | docker system prune
```
