# ChatQnA Benchmarking

## Purpose

We aim to run these benchmarks and share them with the OPEA community for three primary reasons:

- To offer insights on inference throughput in real-world scenarios, helping you choose the best service or deployment for your needs.
- To establish a baseline for validating optimization solutions across different implementations, providing clear guidance on which methods are most effective for your use case.
- To inspire the community to build upon our benchmarks, allowing us to better quantify new solutions in conjunction with current leading LLMs, serving frameworks etc.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Overview](#overview)
  - [Using deploy_and_benchmark.py](#using-deploy_and_benchmark.py-recommended)
- [Data Preparation](#data-preparation)
- [Configuration](#configuration)

## Prerequisites

Before running the benchmarks, ensure you have:

1. **Kubernetes Environment**

   - Kubernetes installation: Use [kubespray](https://github.com/opea-project/docs/blob/main/guide/installation/k8s_install/k8s_install_kubespray.md) or other official Kubernetes installation guides
   - (Optional) [Kubernetes set up guide on Intel Gaudi product](https://github.com/opea-project/GenAIInfra/blob/main/README.md#setup-kubernetes-cluster)

2. **Configuration YAML**
   The configuration file (e.g., `./ChatQnA/benchmark_chatqna.yaml`) consists of two main sections: deployment and benchmarking. Required fields must be filled with valid values (like the Hugging Face token). For all other fields, you can either customize them according to your needs or leave them empty ("") to use the default values from the [helm charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts).

## Data Preparation

Before running benchmarks, you need to:

1. **Prepare Test Data**

   - Download the retrieval file:
     ```bash
     wget https://github.com/opea-project/GenAIEval/tree/main/evals/benchmark/data/upload_file.txt
     ```
   - For the `chatqna_qlist_pubmed` test case, prepare `pubmed_${max_lines}.txt` by following this [README](https://github.com/opea-project/GenAIEval/blob/main/evals/benchmark/stresscli/README_Pubmed_qlist.md)

2. **Prepare Model Files (Recommended)**
   ```bash
   pip install -U "huggingface_hub[cli]"
   sudo mkdir -p /mnt/models
   sudo chmod 777 /mnt/models
   huggingface-cli download --cache-dir /mnt/models Intel/neural-chat-7b-v3-3
   ```

## Overview

The benchmarking process consists of two main components: deployment and benchmarking. We provide `deploy_and_benchmark.py` as a unified entry point that combines both steps.

### Using deploy_and_benchmark.py (Recommended)

The script `deploy_and_benchmark.py` serves as the main entry point. Here's an example using ChatQnA configuration (you can replace it with any other example's configuration YAML file):

1. For a specific number of nodes:

   ```bash
   python deploy_and_benchmark.py ./ChatQnA/benchmark_chatqna.yaml --target-node 1
   ```

2. For all node configurations:
   ```bash
   python deploy_and_benchmark.py ./ChatQnA/benchmark_chatqna.yaml
   ```
   This will iterate through the node list in your configuration YAML file, performing deployment and benchmarking for each node count.
