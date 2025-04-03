# ChatQnA Benchmarking

## Purpose

We aim to run these benchmarks and share them with the OPEA community for three primary reasons:

- To offer insights on inference throughput in real-world scenarios, helping you choose the best service or deployment for your needs.
- To establish a baseline for validating optimization solutions across different implementations, providing clear guidance on which methods are most effective for your use case.
- To inspire the community to build upon our benchmarks, allowing us to better quantify new solutions in conjunction with current leading LLMs, serving frameworks etc.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Data Preparation](#data-preparation)
- [Running Deploy and Benchmark Tests](#running-deploy-and-benchmark-tests)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before running the benchmarks, ensure you have:

1. **Kubernetes Environment**

   - Kubernetes installation: Use [kubespray](https://github.com/opea-project/docs/blob/main/guide/installation/k8s_install/k8s_install_kubespray.md) or other official Kubernetes installation guides
   - (Optional) [Kubernetes set up guide on Intel Gaudi product](https://github.com/opea-project/GenAIInfra/blob/main/README.md#setup-kubernetes-cluster)

2. **Configuration YAML**  
   The configuration file (e.g., `./ChatQnA/benchmark_chatqna.yaml`) consists of two main sections: deployment and benchmarking. Required fields with `# mandatory` comment must be filled with valid values, such as `HUGGINGFACEHUB_API_TOKEN`. For all other fields, you can either customize them according to our needs or leave them empty ("") to use the default values from the [helm charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts).

   **Default Models**:

   - LLM: `meta-llama/Meta-Llama-3-8B-Instruct` (Required: must be specified as it's shared between deployment and benchmarking phases)
   - Embedding: `BAAI/bge-base-en-v1.5`
   - Reranking: `BAAI/bge-reranker-base`

   You can customize which models to use by setting the `model_id` field in the corresponding service section. Note that the LLM model must be specified in the configuration as it is used by both deployment and benchmarking processes.

   **Important Notes**:

   - For Gaudi deployments:
     - LLM service runs on Gaudi devices
     - If enabled, the reranking service (teirerank) also runs on Gaudi devices
   - **Llama Model Access**:
     - Downloading Llama models requires both:
       1. HuggingFace API token
       2. Special authorization from Meta
     - Please visit [meta-llama/Meta-Llama-3-8B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) to request access
     - Deployment will fail if model download is unsuccessful due to missing authorization

   **Node and Replica Configuration**:

   ```yaml
   node: [1, 2, 4, 8] # Number of nodes to deploy
   replicaCount: [1, 2, 4, 8] # Must align with node configuration
   ```

   The `replicaCount` values must align with the `node` configuration by index:

   - When deploying on 1 node → uses replicaCount[0] = 1
   - When deploying on 2 nodes → uses replicaCount[1] = 2
   - When deploying on 4 nodes → uses replicaCount[2] = 4
   - When deploying on 8 nodes → uses replicaCount[3] = 8

   Note: Model parameters that accept lists (e.g., `max_batch_size`, `max_num_seqs`) are deployment parameters that affect model service behavior but not the number of service instances. When these parameters are lists, each value will trigger a service upgrade followed by a new round of testing, while maintaining the same number of service instances.

3. **Install required Python packages**
   Run the following command to install all necessary dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

Before running benchmarks, you need to:

1. **Prepare Test Data**

   - Testing for general benchmark target:

     Download the retrieval file using the command below for data ingestion in RAG:

     ```bash
     wget https://github.com/opea-project/GenAIEval/tree/main/evals/benchmark/data/upload_file.txt
     ```

   - Testing for pubmed benchmark target:

     For the `chatqna_qlist_pubmed` test case, prepare `pubmed_${max_lines}.txt` by following this [README](https://github.com/opea-project/GenAIEval/blob/main/evals/benchmark/stresscli/README_Pubmed_qlist.md)

   After the data is prepared, please update the `absolute path` of this file in the benchmark.yaml file. For example, in the `ChatQnA/benchmark_chatqna.yaml` file, `/home/sdp/upload_file.txt` should be replaced by your file path.

2. **Prepare Model Files (Recommended)**
   ```bash
   pip install -U "huggingface_hub[cli]"
   sudo mkdir -p /mnt/models
   sudo chmod 777 /mnt/models
   huggingface-cli download --cache-dir /mnt/models meta-llama/Meta-Llama-3-8B-Instruct
   ```

## Running Deploy and Benchmark Tests

The benchmarking process consists of two main components: deployment and benchmarking. We provide `deploy_and_benchmark.py` as a unified entry point that combines both steps.

### Running the Tests

The script `deploy_and_benchmark.py` serves as the main entry point. You can use any example's configuration YAML file. Here are examples using ChatQnA configuration:

1. For a specific number of nodes:

   ```bash
   # Default OOB (Out of Box) mode
   python deploy_and_benchmark.py ./ChatQnA/benchmark_chatqna.yaml --target-node 1

   # Or specify test mode explicitly
   python deploy_and_benchmark.py ./ChatQnA/benchmark_chatqna.yaml --target-node 1 --test-mode [oob|tune]
   ```

2. For all node configurations:

   ```bash
   # Default OOB (Out of Box) mode
   python deploy_and_benchmark.py ./ChatQnA/benchmark_chatqna.yaml

   # Or specify test mode explicitly
   python deploy_and_benchmark.py ./ChatQnA/benchmark_chatqna.yaml --test-mode [oob|tune]
   ```

   This will process all node configurations defined in your YAML file.

### Test Modes

The script provides two test modes controlled by the `--test-mode` parameter:

1. **OOB (Out of Box) Mode** - Default

   ```bash
   --test-mode oob  # or omit the parameter
   ```

   - Uses enabled configurations only:
     - Resources: Only uses resources when `resources.enabled` is True
     - Model parameters:
       - Uses batch parameters when `batch_params.enabled` is True
       - Uses token parameters when `token_params.enabled` is True
   - Suitable for basic functionality testing with selected optimizations

2. **Tune Mode**
   ```bash
   --test-mode tune
   ```
   - Applies all configurations regardless of enabled status:
     - Resource-related parameters:
       - `resources.cores_per_instance`: CPU cores allocation
       - `resources.memory_capacity`: Memory allocation
       - `resources.cards_per_instance`: GPU/Accelerator cards allocation
     - Model parameters:
       - Batch parameters:
         - `max_batch_size`: Maximum batch size (TGI engine)
         - `max_num_seqs`: Maximum number of sequences (vLLM engine)
       - Token parameters:
         - `max_input_length`: Maximum input sequence length
         - `max_total_tokens`: Maximum total tokens per request
         - `max_batch_total_tokens`: Maximum total tokens in a batch
         - `max_batch_prefill_tokens`: Maximum tokens in prefill phase

Choose "oob" mode when you want to selectively enable optimizations, or "tune" mode when you want to apply all available optimizations regardless of their enabled status.

### Troubleshooting

**Helm Chart Directory Issues**

- During execution, the script downloads and extracts the Helm chart to a directory named after your example
- The directory name is derived from your input YAML file path
  - For example: if your input is `./ChatQnA/benchmark_chatqna.yaml`, the extracted directory will be `chatqna/`
- In some error cases, this directory might not be properly cleaned up
- If you encounter deployment issues, check if there's a leftover Helm chart directory:

  ```bash
  # Example: for ./ChatQnA/benchmark_chatqna.yaml
  ls -la chatqna/

  # Clean up if needed
  rm -rf chatqna/
  ```

- After cleaning up the directory, try running the deployment again

Note: Always ensure there are no leftover Helm chart directories from previous failed runs before starting a new deployment.
