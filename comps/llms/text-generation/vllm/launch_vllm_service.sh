#!/bin/bash


# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Set default values
default_port=8080
default_model="mistralai/Mistral-7B-v0.1"

# Assign arguments to variables
port_number=${1:-$default_port}
model_name=${2:-$default_model}

# Check if all required arguments are provided
if [ "$#" -lt 0 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 [port_number] [model_name]"
    exit 1
fi

# Set the volume variable
volume=$PWD/data

# Build the Docker run command based on the number of cards
docker run -it --rm --name="ChatQnA_server" -p $port_number:$port_number --network=host -v $volume:/data -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} vllm:cpu /bin/bash -c "cd / && export VLLM_CPU_KVCACHE_SPACE=40 && python3 -m vllm.entrypoints.openai.api_server --model $model_name --port $port_number"
