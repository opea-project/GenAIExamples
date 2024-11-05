# CodeGen Benchmarking

This folder contains a collection of scripts to enable inference benchmarking by leveraging a comprehensive benchmarking tool, [GenAIEval](https://github.com/opea-project/GenAIEval/blob/main/evals/benchmark/README.md), that enables throughput analysis to assess inference performance.

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

Results will be displayed in the terminal and saved as CSV file named `1_testspec.yaml`.

## Getting Started

We recommend using Kubernetes to deploy the CodeGen service, as it offers benefits such as load balancing and improved scalability. However, you can also deploy the service using Docker if that better suits your needs.

### Prerequisites

- Install Kubernetes by following [this guide](https://github.com/opea-project/docs/blob/main/guide/installation/k8s_install/k8s_install_kubespray.md).

- Every node has direct internet access
- Set up kubectl on the master node with access to the Kubernetes cluster.
- Install Python 3.8+ on the master node for running GenAIEval.
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

### Test Steps

Please deploy CodeGen service before benchmarking.

#### Run Benchmark Test

Before the benchmark, we can configure the number of test queries and test output directory by:

```bash
export USER_QUERIES="[128, 128, 128, 128]"
export TEST_OUTPUT_DIR="/tmp/benchmark_output"
```

And then run the benchmark by:

```bash
bash benchmark.sh -n <node_count>
```

The argument `-n` refers to the number of test nodes.

#### Data collection

All the test results will come to this folder `/tmp/benchmark_output` configured by the environment variable `TEST_OUTPUT_DIR` in previous steps.
