# CodeGen Accuracy Benchmark

## Table of Contents

- [Purpose](#purpose)
- [Evaluation Framework](#evaluation-framework)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Running the Accuracy Benchmark](#running-the-accuracy-benchmark)
- [Understanding the Results](#understanding-the-results)

## Purpose

This guide explains how to evaluate the accuracy of a deployed CodeGen service using standardized code generation benchmarks. It helps quantify the model's ability to generate correct and functional code based on prompts.

## Evaluation Framework

We utilize the [bigcode-evaluation-harness](https://github.com/bigcode-project/bigcode-evaluation-harness), a framework specifically designed for evaluating code generation models. It supports various standard benchmarks such as [HumanEval](https://huggingface.co/datasets/openai_humaneval), [MBPP](https://huggingface.co/datasets/mbpp), and others.

## Prerequisites

- A running CodeGen service accessible via an HTTP endpoint. Refer to the main [CodeGen README](../../README.md) for deployment options.
- Python 3.8+ environment.
- Git installed.

## Environment Setup

1.  **Clone the Evaluation Repository:**

    ```shell
    git clone https://github.com/opea-project/GenAIEval
    cd GenAIEval
    ```

2.  **Install Dependencies:**
    ```shell
    pip install -r requirements.txt
    pip install -e .
    ```

## Running the Accuracy Benchmark

1.  **Set Environment Variables:**
    Replace `{your_ip}` with the IP address of your deployed CodeGen service and `{your_model_identifier}` with the identifier of the model being tested (e.g., `Qwen/CodeQwen1.5-7B-Chat`).

    ```shell
    export CODEGEN_ENDPOINT="http://{your_ip}:7778/v1/codegen"
    export CODEGEN_MODEL="{your_model_identifier}"
    ```

    _Note: Port `7778` is the default for the CodeGen gateway; adjust if you customized it._

2.  **Execute the Benchmark Script:**
    The script will run the evaluation tasks (e.g., HumanEval by default) against the specified endpoint.

    ```shell
    bash run_acc.sh $CODEGEN_MODEL $CODEGEN_ENDPOINT
    ```

    _Note: Currently, the framework runs the full task set by default. Using 'limit' parameters might affect result comparability._

## Understanding the Results

The results will be printed to the console and saved in `evaluation_results.json`. A key metric is `pass@k`, which represents the percentage of problems solved correctly within `k` generated attempts (e.g., `pass@1` means solved on the first try).

Example output snippet:

```json
{
  "humaneval": {
    "pass@1": 0.7195121951219512
  },
  "config": {
    "model": "Qwen/CodeQwen1.5-7B-Chat",
    "tasks": "humaneval",
    "instruction_tokens": null,
    "batch_size": 1,
    "max_length_generation": 2048,
    "precision": "fp32",
    "load_in_8bit": false,
    "load_in_4bit": false,
    "left_padding": false,
    "limit": null,
    "limit_start": 0,
    "save_every_k_tasks": -1,
    "postprocess": true,
    "allow_code_execution": true,
    "generation_only": false,
    "load_generations_path": null,
    "load_data_path": null,
    "metric_output_path": "evaluation_results.json",
    "save_generations": true,
    "load_generations_intermediate_paths": null,
    "save_generations_path": "generations.json",
    "save_references": true,
    "save_references_path": "references.json",
    "prompt": "prompt",
    "max_memory_per_gpu": null,
    "check_references": false,
    "codegen_url": "http://192.168.123.104:7778/v1/codegen"
  }
}
```

This indicates a `pass@1` score of approximately 72% on the HumanEval benchmark for the specified model via the CodeGen service endpoint.
