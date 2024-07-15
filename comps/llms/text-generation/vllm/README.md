# vLLM Endpoint Serve

[vLLM](https://github.com/vllm-project/vllm) is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc.. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html) and [Gaudi accelerators](https://habana.ai/products). This guide provides an example on how to launch vLLM serving endpoint on CPU and Gaudi accelerators.

## set up environment variables

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
export vLLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL="meta-llama/Meta-Llama-3-8B-Instruct"
```

For gated models such as `LLAMA-2`, you will have to pass the environment HUGGINGFACEHUB_API_TOKEN. Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

## Set up VLLM Ray Service

### vLLM on CPU

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

### vLLM on Gaudi

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

### Query the service

And then you can make requests like below to check the service status:

```bash
curl http://${your_ip}:8008/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": "meta-llama/Meta-Llama-3-8B-Instruct",
  "prompt": "What is Deep Learning?",
  "max_tokens": 32,
  "temperature": 0
  }'
```

## Set up OPEA microservice

Then we warp the VLLM service into OPEA microcervice.

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
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_p":0.95,"temperature":0.01,"streaming":false}' \
  -H 'Content-Type: application/json
```
