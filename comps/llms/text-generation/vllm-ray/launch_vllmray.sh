#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Set default values
default_port=8006
default_model=$LLM_MODEL
default_parallel_number=2
default_enforce_eager=False

# Assign arguments to variables
port_number=${1:-$default_port}
model_name=${2:-$default_model}
parallel_number=${3:-$default_parallel_number}
enforce_eager=${4:-$default_enforce_eager}

# Check if all required arguments are provided
if [ "$#" -lt 0 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 [port_number] [model_name] [parallel_number] [enforce_eager]"
    echo "Please customize the arguments you want to use.
    - port_number: The port number assigned to the Ray Gaudi endpoint, with the default being 8080.
    - model_name: The model name utilized for LLM, with the default set to meta-llama/Llama-2-7b-chat-hf.
    - parallel_number: The number of HPUs specifies the number of HPUs per worker process.
    - enforce_eager: Whether to enforce eager execution, default to be True."
    exit 1
fi

# Build the Docker run command based on the number of cards
docker run -d --rm \
    --name="vllm-ray-service" \
    --runtime=habana \
    -v $PWD/data:/data \
    -e HABANA_VISIBLE_DEVICES=all \
    -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
    --cap-add=sys_nice \
    --ipc=host \
    -p $port_number:8000 \
    -e HTTPS_PROXY=$https_proxy \
    -e HTTP_PROXY=$https_proxy \
    -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
    vllm_ray:habana \
    /bin/bash -c "ray start --head && python vllm_ray_openai.py --port_number 8000 --model_id_or_path $model_name --tensor_parallel_size $parallel_number --enforce_eager $enforce_eager"
