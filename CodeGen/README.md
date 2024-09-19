# Code Generation Application

Code Generation (CodeGen) Large Language Models (LLMs) are specialized AI models designed for the task of generating computer code. Such models undergo training with datasets that encompass repositories, specialized documentation, programming code, relevant web content, and other related data. They possess a deep understanding of various programming languages, coding patterns, and software development concepts. CodeGen LLMs are engineered to assist developers and programmers. When these LLMs are seamlessly integrated into the developer's Integrated Development Environment (IDE), they possess a comprehensive understanding of the coding context, which includes elements such as comments, function names, and variable names. This contextual awareness empowers them to provide more refined and contextually relevant coding suggestions.

The capabilities of CodeGen LLMs include:

- Code Generation: Streamline coding through Code Generation, enabling non-programmers to describe tasks for code creation.
- Code Completion: Accelerate coding by suggesting contextually relevant snippets as developers type.
- Code Translation and Modernization: Translate and modernize code across multiple programming languages, aiding interoperability and updating legacy projects.
- Code Summarization: Extract key insights from codebases, improving readability and developer productivity.
- Code Refactoring: Offer suggestions for code refactoring, enhancing code performance and efficiency.
- AI-Assisted Testing: Assist in creating test cases, ensuring code robustness and accelerating development cycles.
- Error Detection and Debugging: Detect errors in code and provide detailed descriptions and potential fixes, expediting debugging processes.

In this example, we present a Code Copilot application to showcase how code generation can be executed on either Intel Gaudi2 platform or Intel Xeon Processor platform. This CodeGen use case involves code generation utilizing open-source models such as `m-a-p/OpenCodeInterpreter-DS-6.7B` and `deepseek-ai/deepseek-coder-33b-instruct` with Text Generation Inference (TGI) for serving deployment.

The workflow falls into the following architecture:

![architecture](./assets/img/codegen_architecture.png)

## Deploy CodeGen Service

The CodeGen service can be effortlessly deployed on either Intel Gaudi2 or Intel Xeon Scalable Processor.

Currently we support two ways of deploying ChatQnA services with docker compose:

1. Start services using the docker image on `docker hub`:

   ```bash
   docker pull opea/codegen:latest
   ```

2. Start services using the docker images built from source. See the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) or [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) for more information.

### Required Models

By default, the LLM model is set to a default value as listed below:

| Service      | Model                                                                           |
| ------------ | ------------------------------------------------------------------------------- |
| LLM_MODEL_ID | [meta-llama/CodeLlama-7b-hf](https://huggingface.co/meta-llama/CodeLlama-7b-hf) |

[meta-llama/CodeLlama-7b-hf](https://huggingface.co/meta-llama/CodeLlama-7b-hf) is a gated model that requires submitting an access request through Hugging Face. You can replace it with another model.
Change the `LLM_MODEL_ID` below for your needs, such as: [Qwen/CodeQwen1.5-7B-Chat](https://huggingface.co/Qwen/CodeQwen1.5-7B-Chat), [deepseek-ai/deepseek-coder-6.7b-instruct](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct)

If you choose to use `meta-llama/CodeLlama-7b-hf` as LLM model, you will need to visit [here](https://huggingface.co/meta-llama/CodeLlama-7b-hf), click the `Expand to review and access` button to ask for model access.

### Setup Environment Variable

To set up environment variables for deploying ChatQnA services, follow these steps:

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy="Your_No_Proxy"
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPs_Proxy"
   ```

3. Set up other environment variables:

   ```bash
   source ./docker_compose/set_env.sh
   ```

### Deploy CodeGen using Docker

#### Deploy CodeGen on Gaudi

Find the corresponding [compose.yaml](./docker_compose/intel/hpu/gaudi/compose.yaml).

```bash
cd GenAIExamples/CodeGen/docker_compose/intel/hpu/gaudi
docker compose up -d
```

> Notice: Currently only the **Habana Driver 1.16.x** is supported for Gaudi.

Refer to the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) to build docker images from source.

#### Deploy CodeGen on Xeon

Find the corresponding [compose.yaml](./docker_compose/intel/cpu/xeon/compose.yaml).

```bash
cd GenAIExamples/CodeGen/docker_compose/intel/cpu/xeon
docker compose up -d
```

Refer to the [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) for more instructions on building docker images from source.

### Deploy CodeGen using Kubernetes

Refer to the [Kubernetes Guide](./kubernetes/intel/README.md) for instructions on deploying CodeGen into Kubernetes on Xeon & Gaudi.

### Deploy CodeGen into Kubernetes using Helm Chart

Install Helm (version >= 3.15) first. Refer to the [Helm Installation Guide](https://helm.sh/docs/intro/install/) for more information.

Refer to the [CodeGen helm chart](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/codegen) for instructions on deploying CodeGen into Kubernetes on Xeon & Gaudi.

## Consume CodeGen Service

Two ways of consuming CodeGen Service:

1. Use cURL command on terminal

   ```bash
   curl http://${host_ip}:7778/v1/codegen \
       -H "Content-Type: application/json" \
       -d '{"messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."}'
   ```

2. Access via frontend

   To access the frontend, open the following URL in your browser: http://{host_ip}:5173.

   By default, the UI runs on port 5173 internally.

## Troubleshooting

1. If you get errors like "Access Denied", [validate micro service](https://github.com/opea-project/GenAIExamples/tree/main/CodeGen/docker_compose/intel/cpu/xeon#validate-microservices) first. A simple example:

   ```bash
   http_proxy=""
   curl http://${host_ip}:8028/generate \
     -X POST \
     -d '{"inputs":"Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception.","parameters":{"max_tokens":256, "do_sample": true}}' \
     -H 'Content-Type: application/json'
   ```

2. If you get errors like "aiohttp.client_exceptions.ClientConnectorError: Cannot connect to host xx.xx.xx.xx:8028", check the `tgi service` first. If there is "Cannot access gated repo for url
   https://huggingface.co/meta-llama/CodeLlama-7b-hf/resolve/main/config.json." error of `tgi service`, Then you need to ask for model access first. Follow the instruction in the [Required Models](#required-models) section for more information.

3. (Docker only) If all microservices work well, check the port ${host_ip}:7778, the port may be allocated by other users, you can modify the `compose.yaml`.

4. (Docker only) If you get errors like "The container name is in use", change container name in `compose.yaml`.
