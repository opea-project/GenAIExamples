#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


# Set default values


default_port=8008
default_model="meta-llama/Llama-2-7b-hf"
default_device="cpu"
swap_space=50
image="vllm:openvino"

while getopts ":hm:p:d:" opt; do
  case $opt in
    h)
      echo "Usage: $0 [-h] [-m model] [-p port] [-d device]"
      echo "Options:"
      echo "  -h         Display this help message"
      echo "  -m model   Model (default: meta-llama/Llama-2-7b-hf for cpu"
      echo "             meta-llama/Llama-3.2-3B-Instruct for gpu)"
      echo "  -p port    Port (default: 8000)"
      echo "  -d device  Target Device (Default: cpu, optional selection can be 'cpu' and 'gpu')"
      exit 0
      ;;
    m)
      model=$OPTARG
      ;;
    p)
      port=$OPTARG
      ;;
    d)
      device=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Assign arguments to variables
model_name=${model:-$default_model}
port_number=${port:-$default_port}
device=${device:-$default_device}


# Set the Huggingface cache directory variable
HF_CACHE_DIR=$HOME/.cache/huggingface
if [ "$device" = "gpu" ]; then
  docker_args="-e VLLM_OPENVINO_DEVICE=GPU  --device /dev/dri -v /dev/dri/by-path:/dev/dri/by-path"
  vllm_args="--max_model_len=1024"
  model_name="meta-llama/Llama-3.2-3B-Instruct"
  image="opea/vllm-arc:latest"
fi
# Start the model server using Openvino as the backend inference engine.
# Provide the container name that is unique and meaningful, typically one that includes the model name.

docker run -d --rm --name="vllm-openvino-server" \
  -p $port_number:80 \
  --ipc=host \
  $docker_args \
  -e HTTPS_PROXY=$https_proxy \
  -e HTTP_PROXY=$https_proxy \
  -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  $image /bin/bash -c "\
    cd / && \
    export VLLM_CPU_KVCACHE_SPACE=50 && \
    python3 -m vllm.entrypoints.openai.api_server \
      --model \"$model_name\" \
      $vllm_args \
      --host 0.0.0.0 \
      --port 80"
