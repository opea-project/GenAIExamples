# Ray-Serve Endpoint Service

[Ray](https://docs.ray.io/en/latest/serve/index.html) is an LLM serving solution that makes it easy to deploy and manage a variety of open source LLMs, built on [Ray Serve](https://docs.ray.io/en/latest/serve/index.html), has native support for autoscaling and multi-node deployments, which is easy to use for LLM inference serving on Intel Gaudi2 accelerators. The Intel Gaudi2 accelerator supports both training and inference for deep learning models in particular for LLMs. Please visit [Habana AI products](<(https://habana.ai/products)>) for more details.

## set up environment variables

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
export RAY_Serve_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL="meta-llama/Llama-2-7b-chat-hf"
```

For gated models such as `LLAMA-2`, you will have to pass the environment HUGGINGFACEHUB_API_TOKEN. Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

## Set up Ray Serve Service

### Build docker

```bash
bash build_docker_rayserve.sh
```

### Launch Ray Serve service

```bash
bash launch_ray_service.sh
```

The `launch_vllm_service.sh` script accepts five parameters:

- port_number: The port number assigned to the Ray Gaudi endpoint, with the default being 8008.
- model_name: The model name utilized for LLM, with the default set to meta-llama/Llama-2-7b-chat-hf.
- chat_processor: The chat processor for handling the prompts, with the default set to 'ChatModelNoFormat', and the optional selection can be 'ChatModelLlama', 'ChatModelGptJ" and "ChatModelGemma'.
- num_cpus_per_worker: The number of CPUs specifies the number of CPUs per worker process.
- num_hpus_per_worker: The number of HPUs specifies the number of HPUs per worker process.

If you want to customize the port or model_name, can run:

```bash
bash ./launch_ray_service.sh ${port_number} ${model_name} ${chat_processor} ${num_cpus_per_worker} ${num_hpus_per_worker}
```

### Query the service

And then you can make requests with the OpenAI-compatible APIs like below to check the service status:

```bash
curl http://${your_ip}:8008/v1/chat/completions   \
  -H "Content-Type: application/json"   \
  -d '{"model": "Llama-2-7b-chat-hf", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 32 }'
```

For more information about the OpenAI APIs, you can checkeck the [OpenAI official document](https://platform.openai.com/docs/api-reference/).

## Set up OPEA microservice

Then we warp the Ray Serve service into OPEA microcervice.

### Build docker

```bash
bash build_docker_microservice.sh
```

### Launch the microservice

```bash
bash launch_microservice.sh
```

### Query the microservice

```bash
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
  -H 'Content-Type: application/json'
```
