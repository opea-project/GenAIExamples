#!/bin/bash


# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Set default values
default_port=8080
default_hw_mode="cpu"
default_model="Intel/neural-chat-7b-v3-3"

# Assign arguments to variables
port_number=${1:-$default_port}
model_name=${2:-$default_model}
hw_mode=${3:-$default_hw_mode}

# Check if all required arguments are provided
if [ "$#" -lt 0 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 [port_number] [model_name] [hw_mode]"
    echo "port_number: The port number assigned to the vLLM CPU endpoint, with the default being 8080."
    echo "model_name: The model name utilized for LLM, with the default set to 'Intel/neural-chat-7b-v3-3'."
    echo "hw_mode: The hardware mode utilized for LLM, with the default set to 'cpu', and the optional selection can be 'hpu'"
    exit 1
fi

# Set the volume variable
volume=$PWD/data

# Build the Docker run command based on hardware mode
if [ "$hw_mode" = "hpu" ]; then
    docker run -it --runtime=habana --rm --name="ChatQnA_server" -p $port_number:$port_number -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy -e HF_TOKEN=${HF_TOKEN} vllm:hpu /bin/bash -c "export VLLM_CPU_KVCACHE_SPACE=40 && python3 -m vllm.entrypoints.openai.api_server --enforce-eager --model $model_name --host 0.0.0.0 --port $port_number"
else
    docker run -it --rm --name="ChatQnA_server" -p $port_number:$port_number --network=host -v $volume:/data -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy -e HF_TOKEN=${HF_TOKEN} vllm:cpu /bin/bash -c "cd / && export VLLM_CPU_KVCACHE_SPACE=40 && python3 -m vllm.entrypoints.openai.api_server --enforce-eager --model $model_name --host 0.0.0.0 --port $port_number"
fi
