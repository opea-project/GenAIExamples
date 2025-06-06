# ChatQnA Benchmark Results

## Overview

ChatQnA deployed on a single node with ICX cores as the head node and supporting 8x Gaudi2 cards.
This is based on OPEA v1.3 release helm charts and images using vLLM inferencing platform.

## Methodology

Tests scale concurrent users from 1 to 256, and each user send 4 queries. Measuring end to end (E2E) latency average for each query, time to first token (TTFT) average and time per output token (TPOT) average.

## Hardware and Software Configuration

| **Category**                      | **Details**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **System Summary**                | 1-node, 2x Intel(R) Xeon(R) Platinum 8380 CPU @ 2.30GHz, 40 cores, 270W TDP, HT On, Turbo On, NUMA 2, Integrated Accelerators Available [used]: DLB 0 [0], DSA 0 [0], IAA 0 [0], QAT 0 [0], Total Memory 1024GB (32x32GB DDR4 3200 MT/s [3200 MT/s]), BIOS ETM02, microcode 0xd0003b9, 8x Habana Labs Ltd., 4x MT28800 Family [ConnectX-5 Ex], 4x 7T INTEL SSDPF2KX076TZ, 2x 894.3G SAMSUNG MZ1L2960HCJR-00A07, Ubuntu 22.04.3 LTS, 5.15.0-92-generic. Software: WORKLOAD+VERSION, COMPILER, LIBRARIES, OTHER_SW. |
| **Framework**                     | langchain, vLLM, habana framework                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **Orchestration**                 | k8s/docker                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **Containers and Virtualization** | Kubernetes v1.29.9                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **Drivers**                       | habana driver 1.20.1-366eb9c                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **VM vcpu, Memory**               | 160 vCPUs, 1T memory                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **OPEA Release Version**          | v1.3                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **Dataset**                       | pubmed_10.txt                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Embedding Model**               | BAAI/bge-base-en-v1.5                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **Database**                      | redis                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **LLM Model**                     | meta-llama/Llama-3.1-8B-Instruct                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Precision**                     | bf16                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **Output Length**                 | 1024                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **Command Line Parameters**       | python deploy_and_benchmark.py ./ChatQnA/benchmark_chatqna.yaml --target-node 1 --test-mode oob                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Batch Size**                    | 256                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |

## Benchmark Results

| Users | E2E Latency Avg (ms) | TTFT Avg (ms) | TPOT Avg (ms) |
| ----- | -------------------- | ------------- | ------------- |
| 256   | 35,034.7             | 1,042.8       | 33.1          |
| 128   | 20,996.0             | 529.8         | 19.9          |
| 64    | 16,602.1             | 404.9         | 15.8          |
| 32    | 14,646.5             | 260.1         | 14.0          |
| 16    | 13,669.3             | 193.7         | 13.1          |
| 8     | 13,275.2             | 157.3         | 12.8          |
| 4     | 13,038.8             | 127.7         | 12.5          |
| 2     | 13,059.0             | 129.4         | 12.6          |
| 1     | 12,906.5             | 126.8         | 12.5          |

## Benchmark Config Yaml

<details>
<summary>Click to Check Benchmark Config Yaml</summary>

```yaml
deploy:
  device: gaudi
  version: 1.3.0
  modelUseHostPath: /home/sdp/opea_benchmark/model
  HUGGINGFACEHUB_API_TOKEN: xxx
  node: [1]
  namespace: default
  timeout: 1000 # timeout in seconds for services to be ready, default 30 minutes
  interval: 5 # interval in seconds between service ready checks, default 5 seconds

  services:
    backend:
      resources:
        enabled: False
        cores_per_instance: "16"
        memory_capacity: "8000Mi"
      replicaCount: [1, 2, 4, 8]

    teirerank:
      enabled: False
      model_id: ""
      resources:
        enabled: False
        cards_per_instance: 1
      replicaCount: [1, 1, 1, 1]

    tei:
      model_id: ""
      resources:
        enabled: False
        cores_per_instance: "80"
        memory_capacity: "20000Mi"
      replicaCount: [1, 2, 4, 8]

    llm:
      engine: vllm
      model_id: "meta-llama/Llama-3.1-8B-Instruct" # mandatory
      replicaCount:
        with_teirerank: [7, 15, 31, 63] # When teirerank.enabled is True
        without_teirerank: [8, 16, 32, 64] # When teirerank.enabled is False
      resources:
        enabled: False
        cards_per_instance: 1
      model_params:
        vllm: # VLLM specific parameters
          batch_params:
            enabled: True
            max_num_seqs: [256]
          token_params:
            enabled: False
            max_input_length: ""
            max_total_tokens: ""
            max_batch_total_tokens: ""
            max_batch_prefill_tokens: ""
        tgi: # TGI specific parameters
          batch_params:
            enabled: True
            max_batch_size: [1, 2, 4, 8] # Each value triggers an LLM service upgrade
          token_params:
            enabled: False
            max_input_length: "1280"
            max_total_tokens: "2048"
            max_batch_total_tokens: "65536"
            max_batch_prefill_tokens: "4096"

    data-prep:
      resources:
        enabled: False
        cores_per_instance: ""
        memory_capacity: ""
      replicaCount: [1, 1, 1, 1]

    retriever-usvc:
      resources:
        enabled: False
        cores_per_instance: "8"
        memory_capacity: "8000Mi"
      replicaCount: [1, 2, 4, 8]

    redis-vector-db:
      resources:
        enabled: False
        cores_per_instance: ""
        memory_capacity: ""
      replicaCount: [1, 1, 1, 1]

    chatqna-ui:
      replicaCount: [1, 1, 1, 1]

    nginx:
      replicaCount: [1, 1, 1, 1]

benchmark:
  # http request behavior related fields
  user_queries: [4, 8, 16, 32, 64, 128, 256, 512, 1024]
  concurrency: [1, 2, 4, 8, 16, 32, 64, 128, 256]
  load_shape_type: "constant" # "constant" or "poisson"
  poisson_arrival_rate: 1.0 # only used when load_shape_type is "poisson"
  warmup_iterations: 10
  seed: 1024

  # workload, all of the test cases will run for benchmark
  bench_target: [chatqna_qlist_pubmed]
  dataset: ["/home/sdp/opea_benchmark/pubmed_10.txt"]
  prompt: [10]

  llm:
    # specify the llm output token size
    max_token_size: [1024]
```
