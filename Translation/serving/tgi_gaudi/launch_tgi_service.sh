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
default_model="haoranxu/ALMA-13B"
default_num_cards=1

# Check if all required arguments are provided
if [ "$#" -lt 0 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 [num_cards] [port_number] [model_name]"
    exit 1
fi

# Assign arguments to variables
num_cards=${1:-$default_num_cards}
port_number=${2:-$default_port}
model_name=${3:-$default_model}

# Check if num_cards is within the valid range (1-8)
if [ "$num_cards" -lt 1 ] || [ "$num_cards" -gt 8 ]; then
    echo "Error: num_cards must be between 1 and 8."
    exit 1
fi

# Set the volume variable
volume=$PWD/data

# Build the Docker run command based on the number of cards
if [ "$num_cards" -eq 1 ]; then
    docker_cmd="docker run -d --name tgi-gaudi-server-translation -p $port_number:80 -v $volume:/data --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy tgi-gaudi-translation:1.2.1 --model-id $model_name"
else
    docker_cmd="docker run -d --name tgi-gaudi-server-translation -p $port_number:80 -v $volume:/data --runtime=habana -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy tgi-gaudi-translation:1.2.1 --model-id $model_name --sharded true --num-shard $num_cards"
fi

# Execute the Docker run command
eval $docker_cmd
