# VLLM-Ray Endpoint Service

[Ray](https://docs.ray.io/en/latest/serve/index.html) is an LLM serving solution that makes it easy to deploy and manage a variety of open source LLMs, built on [Ray Serve](https://docs.ray.io/en/latest/serve/index.html), has native support for autoscaling and multi-node deployments, which is easy to use for LLM inference serving on Intel Gaudi2 accelerators. The Intel Gaudi2 accelerator supports both training and inference for deep learning models in particular for LLMs. Please visit [Habana AI products](<(https://habana.ai/products)>) for more details.

[vLLM](https://github.com/vllm-project/vllm) is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc.. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html) and [Gaudi accelerators](https://habana.ai/products).

This guide provides an example on how to launch vLLM with Ray serve endpoint on Gaudi accelerators.

## Set up environment

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export vLLM_RAY_ENDPOINT="http://${your_ip}:8006"
export LLM_MODEL=${your_hf_llm_model}
```

For gated models such as `LLAMA-2`, you will have to pass the environment HUGGINGFACEHUB_API_TOKEN. Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

## Set up VLLM Ray Gaudi Service

First of all, go to the server folder for vllm.

```bash
cd dependency
```

### Build docker

```bash
bash ./build_docker_vllmray.sh
```

### Launch the service

```bash
bash ./launch_vllmray.sh
```

The `launch_vllmray.sh` script accepts three parameters:

- port_number: The port number assigned to the Ray Gaudi endpoint, with the default being 8006.
- model_name: The model name utilized for LLM, with the default set to meta-llama/Llama-2-7b-chat-hf.
- parallel_number: The number of HPUs specifies the number of HPUs per worker process, the default is set to 2.
- enforce_eager: Whether to enforce eager execution, default to be False.

If you want to customize the setting, can run:

```bash
bash ./launch_vllmray.sh ${port_number} ${model_name} ${parallel_number} False/True
```

### Query the service

And then you can make requests with the OpenAI-compatible APIs like below to check the service status:

```bash
curl http://${your_ip}:8006/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": $LLM_MODEL, "messages": [{"role": "user", "content": "How are you?"}]}'
```

For more information about the OpenAI APIs, you can checkeck the [OpenAI official document](https://platform.openai.com/docs/api-reference/).

## Set up OPEA microservice

Then we warp the VLLM Ray service into OPEA microcervice.

### Build docker

```bash
bash ./build_docker_microservice.sh
```

### Launch the microservice

```bash
bash ./launch_microservice.sh
```

### Query the microservice

```bash
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
  -H 'Content-Type: application/json'
```
