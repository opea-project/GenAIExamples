# vLLM Endpoint Service

[vLLM](https://github.com/vllm-project/vllm) is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc.. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html) and [Gaudi accelerators](https://habana.ai/products). This guide provides an example on how to launch vLLM serving endpoint on CPU and Gaudi accelerators.

## 🚀1. Set up Environment Variables

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
export vLLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL="meta-llama/Meta-Llama-3-8B-Instruct"
```

For gated models such as `LLAMA-2`, you will have to pass the environment HUGGINGFACEHUB_API_TOKEN. Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

## 🚀2. Set up vLLM Service

First of all, go to the server folder for vllm.

```bash
cd dependency
```

### 2.1 vLLM on CPU

First let's enable VLLM on CPU.

#### Build docker

```bash
bash ./build_docker_vllm.sh
```

The `build_docker_vllm` accepts one parameter `hw_mode` to specify the hardware mode of the service, with the default being `cpu`, and the optional selection can be `hpu`.

#### Launch vLLM service

```bash
bash ./launch_vllm_service.sh
```

If you want to customize the port or model_name, can run:

```bash
bash ./launch_vllm_service.sh ${port_number} ${model_name}
```

### 2.2 vLLM on Gaudi

Then we show how to enable VLLM on Gaudi.

#### Build docker

```bash
bash ./build_docker_vllm.sh hpu
```

Set `hw_mode` to `hpu`.

#### Launch vLLM service on single node

For small model, we can just use single node.

```bash
bash ./launch_vllm_service.sh ${port_number} ${model_name} hpu 1
```

Set `hw_mode` to `hpu` and `parallel_number` to 1.

The `launch_vllm_service.sh` script accepts 7 parameters:

- port_number: The port number assigned to the vLLM CPU endpoint, with the default being 8008.
- model_name: The model name utilized for LLM, with the default set to 'meta-llama/Meta-Llama-3-8B-Instruct'.
- hw_mode: The hardware mode utilized for LLM, with the default set to "cpu", and the optional selection can be "hpu".
- parallel_number: parallel nodes number for 'hpu' mode
- block_size: default set to 128 for better performance on HPU
- max_num_seqs: default set to 256 for better performance on HPU
- max_seq_len_to_capture: default set to 2048 for better performance on HPU

If you want to get more performance tuning tips, can refer to [Performance tuning](https://github.com/HabanaAI/vllm-fork/blob/habana_main/README_GAUDI.md#performance-tips).

#### Launch vLLM service on multiple nodes

For large model such as `meta-llama/Meta-Llama-3-70b`, we need to launch on multiple nodes.

```bash
bash ./launch_vllm_service.sh ${port_number} ${model_name} hpu ${parallel_number}
```

For example, if we run `meta-llama/Meta-Llama-3-70b` with 8 cards, we can use following command.

```bash
bash ./launch_vllm_service.sh 8008 meta-llama/Meta-Llama-3-70b hpu 8
```

### 2.3 vLLM with OpenVINO (on Intel GPU and CPU)

vLLM powered by OpenVINO supports all LLM models from [vLLM supported models list](https://github.com/vllm-project/vllm/blob/main/docs/source/models/supported_models.rst) and can perform optimal model serving on Intel GPU and all x86-64 CPUs with, at least, AVX2 support, as well as on both integrated and discrete Intel® GPUs (starting from Intel® UHD Graphics generation). OpenVINO vLLM backend supports the following advanced vLLM features:

- Prefix caching (`--enable-prefix-caching`)
- Chunked prefill (`--enable-chunked-prefill`)

#### Build Docker Image

To build the docker image for Intel CPU, run the command

```bash
bash ./build_docker_vllm_openvino.sh
```

Once it successfully builds, you will have the `vllm-openvino` image. It can be used to spawn a serving container with OpenAI API endpoint or you can work with it interactively via bash shell.

To build the docker image for Intel GPU, run the command

```bash
bash ./build_docker_vllm_openvino.sh gpu
```

Once it successfully builds, you will have the `opea/vllm-arc:latest` image. It can be used to spawn a serving container with OpenAI API endpoint or you can work with it interactively via bash shell.

#### Launch vLLM service

For gated models, such as `LLAMA-2`, you will have to pass -e HUGGING_FACE_HUB_TOKEN=\<token\> to the docker run command above with a valid Hugging Face Hub read token.

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get an access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
```

To start the model server for Intel CPU:

```bash
bash launch_vllm_service_openvino.sh
```

To start the model server for Intel GPU:

```bash
bash launch_vllm_service_openvino.sh -d gpu
```

#### Performance tips

vLLM OpenVINO backend environment variables

- `VLLM_OPENVINO_DEVICE` to specify which device utilize for the inference. If there are multiple GPUs in the system, additional indexes can be used to choose the proper one (e.g, `VLLM_OPENVINO_DEVICE=GPU.1`). If the value is not specified, CPU device is used by default.

- `VLLM_OPENVINO_ENABLE_QUANTIZED_WEIGHTS=ON` enables U8 weights compression during model loading stage. By default, compression is turned off. You can also export model with different compression techniques using `optimum-cli` and pass exported folder as `<model_id>`

##### CPU performance tips

vLLM OpenVINO backend uses the following environment variables to control behavior:

- `VLLM_OPENVINO_KVCACHE_SPACE` to specify the KV Cache size (e.g, `VLLM_OPENVINO_KVCACHE_SPACE=40` means 40 GB space for KV cache), larger setting will allow vLLM running more requests in parallel. This parameter should be set based on the hardware configuration and memory management pattern of users.

- `VLLM_OPENVINO_CPU_KV_CACHE_PRECISION=u8` to control KV cache precision. By default, FP16 / BF16 is used depending on platform.

- `VLLM_OPENVINO_ENABLE_QUANTIZED_WEIGHTS=ON` to enable U8 weights compression during model loading stage. By default, compression is turned off.

To enable better TPOT / TTFT latency, you can use vLLM's chunked prefill feature (`--enable-chunked-prefill`). Based on the experiments, the recommended batch size is `256` (`--max-num-batched-tokens`)

OpenVINO best known configuration is:

    $ VLLM_OPENVINO_KVCACHE_SPACE=100 VLLM_OPENVINO_CPU_KV_CACHE_PRECISION=u8 VLLM_OPENVINO_ENABLE_QUANTIZED_WEIGHTS=ON \
        python3 vllm/benchmarks/benchmark_throughput.py --model meta-llama/Llama-2-7b-chat-hf --dataset vllm/benchmarks/ShareGPT_V3_unfiltered_cleaned_split.json --enable-chunked-prefill --max-num-batched-tokens 256

##### GPU performance tips

GPU device implements the logic for automatic detection of available GPU memory and, by default, tries to reserve as much memory as possible for the KV cache (taking into account `gpu_memory_utilization` option). However, this behavior can be overridden by explicitly specifying the desired amount of memory for the KV cache using `VLLM_OPENVINO_KVCACHE_SPACE` environment variable (e.g, `VLLM_OPENVINO_KVCACHE_SPACE=8` means 8 GB space for KV cache).

Currently, the best performance using GPU can be achieved with the default vLLM execution parameters for models with quantized weights (8 and 4-bit integer data types are supported) and `preemption-mode=swap`.

OpenVINO best known configuration for GPU is:

    $ VLLM_OPENVINO_DEVICE=GPU VLLM_OPENVINO_ENABLE_QUANTIZED_WEIGHTS=ON \
        python3 vllm/benchmarks/benchmark_throughput.py --model meta-llama/Llama-2-7b-chat-hf --dataset vllm/benchmarks/ShareGPT_V3_unfiltered_cleaned_split.json

### 2.4 Query the service

And then you can make requests like below to check the service status:

```bash
curl http://${host_ip}:9009/v1/chat/completions \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}]}'
```

## 🚀3. Set up LLM microservice

Then we warp the VLLM service into LLM microservice.

### Build docker

```bash
bash build_docker_microservice.sh
```

### Launch the microservice

```bash
bash launch_microservice.sh
```

### Consume the microservice

#### Check microservice status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'

# Output
# {"Service Title":"opea_service@llm_vllm/MicroService","Service Description":"OPEA Microservice Infrastructure"}
```

#### Consume vLLM Service

User can set the following model parameters according to needs:

- max_tokens: Total output token
- streaming(true/false): return text response in streaming mode or non-streaming mode

```bash
# 1. Non-streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_tokens":17,"top_p":1,"temperature":0.7,"frequency_penalty":0,"presence_penalty":0, "streaming":false}' \
  -H 'Content-Type: application/json'

# 2. Streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'

# 3. Custom chat template with streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true, "chat_template":"### You are a helpful, respectful and honest assistant to help the user with questions.\n### Context: {context}\n### Question: {question}\n### Answer:"}' \
  -H 'Content-Type: application/json'

4. #  Chat with SearchedDoc (Retrieval context)
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"initial_query":"What is Deep Learning?","retrieved_docs":[{"text":"Deep Learning is a ..."},{"text":"Deep Learning is b ..."}]}' \
  -H 'Content-Type: application/json'
```

For parameters, can refer to [LangChain VLLMOpenAI API](https://api.python.langchain.com/en/latest/llms/langchain_community.llms.vllm.VLLMOpenAI.html)
