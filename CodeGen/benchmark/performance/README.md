# CodeGen Performance Benchmark

## Table of Contents

- [Purpose](#purpose)
- [Benchmarking Tool](#benchmarking-tool)
- [Metrics Measured](#metrics-measured)
- [Prerequisites](#prerequisites)
- [Running the Performance Benchmark](#running-the-performance-benchmark)
- [Data Collection](#data-collection)

## Purpose

This guide describes how to benchmark the inference performance (throughput and latency) of a deployed CodeGen service. The results help understand the service's capacity under load and compare different deployment configurations or models. This benchmark primarily targets Kubernetes deployments but can be adapted for Docker.

## Benchmarking Tool

We use the [GenAIEval](https://github.com/opea-project/GenAIEval/blob/main/evals/benchmark/README.md) tool for performance benchmarking, which simulates concurrent users sending requests to the service endpoint.

## Metrics Measured

The benchmark reports several key performance indicators:

- **Concurrency:** Number of concurrent requests simulated.
- **End-to-End Latency:** Time from request submission to final response received (P50, P90, P99 in ms).
- **End-to-End First Token Latency:** Time from request submission to first token received (P50, P90, P99 in ms).
- **Average Next Token Latency:** Average time between subsequent generated tokens (in ms).
- **Average Token Latency:** Average time per generated token (in ms).
- **Requests Per Second (RPS):** Throughput of the service.
- **Output Tokens Per Second:** Rate of token generation.
- **Input Tokens Per Second:** Rate of token consumption.

## Prerequisites

- A running CodeGen service accessible via an HTTP endpoint. Refer to the main [CodeGen README](../../README.md) for deployment options (Kubernetes recommended for load balancing/scalability).
- **If using Kubernetes:**
  - A working Kubernetes cluster (refer to OPEA K8s setup guides if needed).
  - `kubectl` configured to access the cluster from the node where the benchmark will run (typically the master node).
  - Ensure sufficient `ulimit` for network connections on worker nodes hosting the service pods (e.g., `LimitNOFILE=65536` or higher in containerd/docker config).
- **General:**
  - Python 3.8+ on the node running the benchmark script.
  - Network access from the benchmark node to the CodeGen service endpoint.

## Running the Performance Benchmark

1.  **Deploy CodeGen Service:** Ensure your CodeGen service is deployed and accessible. Note the service endpoint URL (e.g., obtained via `kubectl get svc` or your ingress configuration if using Kubernetes, or `http://{host_ip}:{port}` for Docker).

2.  **Configure Benchmark Parameters (Optional):**
    Set environment variables to customize the test queries and output directory. The `USER_QUERIES` variable defines the number of concurrent requests for each test run.

    ```bash
    # Example: Four runs with 128 concurrent requests each
    export USER_QUERIES="[128, 128, 128, 128]"
    # Example: Output directory
    export TEST_OUTPUT_DIR="/tmp/benchmark_output"
    # Set the target endpoint URL
    export CODEGEN_ENDPOINT_URL="http://{your_service_ip_or_hostname}:{port}/v1/codegen"
    ```

    _Replace `{your_service_ip_or_hostname}:{port}` with the actual accessible URL of your CodeGen gateway service._

3.  **Execute the Benchmark Script:**
    Run the script, optionally specifying the number of Kubernetes nodes involved if relevant for reporting context (the script itself runs from one node).
    ```bash
    # Clone GenAIExamples if you haven't already
    # cd GenAIExamples/CodeGen/benchmark/performance
    bash benchmark.sh # Add '-n <node_count>' if desired for logging purposes
    ```
    _Ensure the `benchmark.sh` script is adapted to use `CODEGEN_ENDPOINT_URL` and potentially `USER_QUERIES`, `TEST_OUTPUT_DIR`._

## Data Collection

Benchmark results will be displayed in the terminal upon completion. Detailed results, typically including raw data and summary statistics, will be saved in the directory specified by `TEST_OUTPUT_DIR` (defaulting to `/tmp/benchmark_output`). CSV files (e.g., `1_testspec.yaml.csv`) containing metrics for each run are usually generated here.
