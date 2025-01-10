#!/bin/bash

# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "Script directory: $SCRIPT_DIR"
cd $SCRIPT_DIR

# Set default values
default_hw_mode="cpu"

# Assign arguments to variable
hw_mode=${1:-$default_hw_mode}

# Check if all required arguments are provided
if [ "$#" -lt 0 ] || [ "$#" -gt 1 ]; then
    echo "Usage: $0 [hw_mode]"
    echo "Please customize the arguments you want to use.
    - hw_mode: The hardware mode for the Ray Gaudi endpoint, with the default being 'cpu', and the optional selection can be 'cpu' and 'hpu'."
    exit 1
fi

# Build the docker image for vLLM based on the hardware mode
if [ "$hw_mode" = "hpu" ]; then
    git clone https://github.com/HabanaAI/vllm-fork.git
    cd ./vllm-fork/
    git checkout 3c39626
    docker build -f Dockerfile.hpu -t opea/vllm-gaudi:latest --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
    cd ..
    rm -rf vllm-fork
else
    git clone https://github.com/vllm-project/vllm.git
    cd ./vllm/
    docker build -f Dockerfile.cpu -t opea/vllm-cpu:latest --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
    cd ..
    rm -rf vllm
fi
