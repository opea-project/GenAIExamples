# vLLM Endpoint Serive

[vLLM](https://github.com/vllm-project/vllm) is a RESTful service that provides a simple way to interact with the vLLM API, which is eerie to use for LLM inference and serving on [Intel products](https://www.intel.com/content/www/us/en/products/overview.html). Currently, the vLLM is supporting Intel CPU, and will be extended to Intel Gaudi accelerators soon.

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
curl http://127.0.0.1::8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": <model_name>,
  "prompt": "What is Deep Learning?",
  "max_tokens": 32,
  "temperature": 0
  }'
```

#### Customize vLLM CPU Service

The ./serving/vllm/launch_vllm_service.sh script accepts two parameters:

- port_number: The port number assigned to the vLLM CPU endpoint, with the default being 8080.
- model_name: The model name utilized for LLM, with the default set to "mistralai/Mistral-7B-v0.1".

You have the flexibility to customize twp parameters according to your specific needs. Additionally, you can set the vLLM CPU endpoint by exporting the environment variable `vLLM_LLM_ENDPOINT`:

```bash
export vLLM_LLM_ENDPOINT="http://xxx.xxx.xxx.xxx:8080"
export LLM_MODEL=<model_name> # example: export LLM_MODEL="mistralai/Mistral-7B-v0.1"
```
