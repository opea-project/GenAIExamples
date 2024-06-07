# Use vLLM with OpenVINO

## Build Docker Image

To build the docker image, run the command

```bash
bash ./build_vllm_openvino.sh
```

Once it successfully builds, you will have the `vllm:openvino` image. It can be used to spawn a serving container with OpenAI API endpoint or you can work with it interactively via bash shell.

## Use vLLM serving with OpenAI API

### Start The Server:

For gated models, such as `LLAMA-2`, you will have to pass -e HUGGING_FACE_HUB_TOKEN=\<token\> to the docker run command above with a valid Hugging Face Hub read token.

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get an access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
```

To start the model server:

```bash
bash launch_model_server.sh
```

### Request Completion With Curl:

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": "meta-llama/Llama-2-7b-hf",
  "prompt": "What is the key advantage of Openvino framework?",
  "max_tokens": 300,
  "temperature": 0.7
  }'
```

#### Customize vLLM-OpenVINO Service

The `launch_model_server.sh` script accepts two parameters:

- port: The port number assigned to the vLLM CPU endpoint, with the default being 8000.
- model: The model name utilized for LLM, with the default set to "meta-llama/Llama-2-7b-hf".

You have the flexibility to customize the two parameters according to your specific needs. Below is a sample reference, if you wish to specify a different model and port number

` bash launch_model_server.sh -m meta-llama/Llama-2-7b-chat-hf -p 8123`

Additionally, you can set the vLLM CPU endpoint by exporting the environment variable `vLLM_LLM_ENDPOINT`:

```bash
export vLLM_LLM_ENDPOINT="http://xxx.xxx.xxx.xxx:8000"
export LLM_MODEL=<model_name> # example: export LLM_MODEL="meta-llama/Llama-2-7b-hf"
```

## Use Int-8 Weights Compression

Weights int-8 compression is disabled by default. For better performance and lower memory consumption, the weights compression can be enabled by setting the environment variable `VLLM_OPENVINO_ENABLE_QUANTIZED_WEIGHTS=1`.
To pass the variable in docker, use `-e VLLM_OPENVINO_ENABLE_QUANTIZED_WEIGHTS=1` as an additional argument to `docker run` command in the examples above.

The variable enables weights compression logic described in [optimum-intel 8-bit weights quantization](https://huggingface.co/docs/optimum/intel/optimization_ov#8-bit).
Hence, even if the variable is enabled, the compression is applied only for models starting with a certain size and avoids compression of too small models due to a significant accuracy drop.

## Use UInt-8 KV cache Compression

KV cache uint-8 compression is disabled by default. For better performance and lower memory consumption, the KV cache compression can be enabled by setting the environment variable `VLLM_OPENVINO_CPU_KV_CACHE_PRECISION=u8`.
To pass the variable in docker, use `-e VLLM_OPENVINO_CPU_KV_CACHE_PRECISION=u8` as an additional argument to `docker run` command in the examples above.
