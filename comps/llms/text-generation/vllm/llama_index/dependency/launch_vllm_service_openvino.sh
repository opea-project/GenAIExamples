#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


# Set default values


default_port=8008
default_model="meta-llama/Llama-2-7b-hf"
swap_space=50

while getopts ":hm:p:" opt; do
  case $opt in
    h)
      echo "Usage: $0 [-h] [-m model] [-p port]"
      echo "Options:"
      echo "  -h         Display this help message"
      echo "  -m model   Model (default: meta-llama/Llama-2-7b-hf)"
      echo "  -p port    Port (default: 8000)"
      exit 0
      ;;
    m)
      model=$OPTARG
      ;;
    p)
      port=$OPTARG
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


# Set the Huggingface cache directory variable
HF_CACHE_DIR=$HOME/.cache/huggingface

# Start the model server using Openvino as the backend inference engine.
# Provide the container name that is unique and meaningful, typically one that includes the model name.

docker run -d --rm --name="vllm-openvino-server" \
  -p $port_number:80 \
  --ipc=host \
  -e HTTPS_PROXY=$https_proxy \
  -e HTTP_PROXY=$https_proxy \
  -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} \
  -v $HOME/.cache/huggingface:/home/user/.cache/huggingface \
  vllm-openvino:latest /bin/bash -c "\
    cd / && \
    export VLLM_CPU_KVCACHE_SPACE=50 && \
    python3 -m vllm.entrypoints.openai.api_server \
      --model \"$model_name\" \
      --host 0.0.0.0 \
      --port 80"
