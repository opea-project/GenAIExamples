# vLLM Endpoint Serve

[vLLM](https://github.com/vllm-project/vllm) is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc.. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html), Gaudi accelerators support will be added soon. This guide provides an example on how to launch vLLM serving endpoint on CPU.

## Getting Started

### Launch vLLM CPU Service

#### Launch a local server instance:

```bash
bash ./serving/vllm/launch_vllm_service.sh
```

For gated models such as `LLAMA-2`, you will have to pass -e HUGGING_FACE_HUB_TOKEN=\<token\> to the docker run command above with a valid Hugging Face Hub read token.

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
```

And then you can make requests like below to check the service status:

```bash
curl http://127.0.0.1:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": <model_name>,
  "prompt": "What is Deep Learning?",
  "max_tokens": 32,
  "temperature": 0
  }'
```

#### Customize vLLM CPU Service

The `./serving/vllm/launch_vllm_service.sh` script accepts two parameters:

- port_number: The port number assigned to the vLLM CPU endpoint, with the default being 8080.
- model_name: The model name utilized for LLM, with the default set to "mistralai/Mistral-7B-v0.1".

You have the flexibility to customize two parameters according to your specific needs. Additionally, you can set the vLLM CPU endpoint by exporting the environment variable `vLLM_LLM_ENDPOINT`:

```bash
export vLLM_LLM_ENDPOINT="http://xxx.xxx.xxx.xxx:8080"
export LLM_MODEL=<model_name> # example: export LLM_MODEL="mistralai/Mistral-7B-v0.1"
```
