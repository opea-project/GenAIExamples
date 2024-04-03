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

#!/bin/bash
# Set default values
default_port=8080
default_model="neural-chat-7b-v3-3"

# Check if all required arguments are provided
if [ "$#" -lt 0 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 [num_cards] [port_number] [model_name]"
    exit 1
fi

# Assign arguments to variables
port_number=${2:-$default_port}
model_name_file=${3:-$default_model}.yaml

# Pull the llm-on-ray repo
git submodule update --init --recursive

# Build the Docker run command
cd serving/ray_gaudi/llm-on-ray/dev/docker && docker build -f Dockerfile.habana ../../  -t llm-ray-habana:latest --network=host --build-arg no_proxy="127.0.0.1,localhost" 

# Build the Docker run command based on the number of cards
if [ "$num_cards" -eq 1 ]; then
cd ../../../ && docker run -p $port_number:$port_number --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy --cap-add=sys_nice --net=host --ipc=host -v $PWD/llm-on-ray:/root/llm-on-ray --name="llm-ray-habana" \
llm-ray-habana:latest /bin/bash -c "ray start --head --port 8002 --dashboard-host='0.0.0.0' --dashboard-port=8265 && llm_on_ray-serve --config_file /root/llm-on-ray/llm_on_ray/inference/models/hpu/$model_name_file --port $port_number --keep_serve_terminal"
else
cd ../../../ && docker run -p $port_number:$port_number --runtime=habana -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy --cap-add=sys_nice --net=host --ipc=host -v $PWD/llm-on-ray:/root/llm-on-ray --name="llm-ray-habana" \
llm-ray-habana:latest /bin/bash -c "ray start --head --port 8002 --dashboard-host='0.0.0.0' --dashboard-port=8265 && llm_on_ray-serve --config_file /root/llm-on-ray/llm_on_ray/inference/models/hpu/$model_name_file --port $port_number --keep_serve_terminal"
fi