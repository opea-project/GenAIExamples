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
docker run -it --rm --name="ChatQnA_server" -p $port_number:$port_number --network=host -v $volume:/data -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy vllm-cpu-env /bin/bash -c "cd / && export VLLM_CPU_KVCACHE_SPACE=40 && python3 -m vllm.entrypoints.openai.api_server --model $model_name --port $port_number"
