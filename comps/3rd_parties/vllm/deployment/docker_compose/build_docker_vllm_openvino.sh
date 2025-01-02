#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Set default values
default_hw_mode="cpu"

# Assign arguments to variable
hw_mode=${1:-$default_hw_mode}

# Check if all required arguments are provided
if [ "$#" -lt 0 ] || [ "$#" -gt 1 ]; then
    echo "Usage: $0 [hw_mode]"
    echo "Please customize the arguments you want to use.
    - hw_mode: The hardware mode for the vLLM endpoint, with the default being 'cpu', and the optional selection can be 'cpu' and 'gpu'."
    exit 1
fi

# Build the docker image for vLLM based on the hardware mode
if [ "$hw_mode" = "gpu" ]; then
    docker build -f Dockerfile.intel_gpu -t opea/vllm-arc:latest . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
else
    BASEDIR="$( cd "$( dirname "$0" )" && pwd )"
    git clone https://github.com/vllm-project/vllm.git vllm
    cd ./vllm/ && git checkout v0.6.1
    docker build -t vllm-openvino:latest -f Dockerfile.openvino . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
    cd $BASEDIR && rm -rf vllm
fi
