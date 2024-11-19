#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Set default values
default_port=8008
default_model=$LLM_MODEL
default_hw_mode="cpu"
default_parallel_number=1
default_block_size=128
default_max_num_seqs=256
default_max_seq_len_to_capture=2048

# Assign arguments to variables
port_number=${1:-$default_port}
model_name=${2:-$default_model}
hw_mode=${3:-$default_hw_mode}
parallel_number=${4:-$default_parallel_number}
block_size=${5:-$default_block_size}
max_num_seqs=${6:-$default_max_num_seqs}
max_seq_len_to_capture=${7:-$default_max_seq_len_to_capture}

# Check if all required arguments are provided
if [ "$#" -lt 0 ] || [ "$#" -gt 4 ]; then
    echo "Usage: $0 [port_number] [model_name] [hw_mode] [parallel_number]"
    echo "port_number: The port number assigned to the vLLM CPU endpoint, with the default being 8080."
    echo "model_name: The model name utilized for LLM, with the default set to 'meta-llama/Meta-Llama-3-8B-Instruct'."
    echo "hw_mode: The hardware mode utilized for LLM, with the default set to 'cpu', and the optional selection can be 'hpu'"
    echo "parallel_number: parallel nodes number for 'hpu' mode"
    echo "block_size: default set to 128 for better performance on HPU"
    echo "max_num_seqs: default set to 256 for better performance on HPU"
    echo "max_seq_len_to_capture: default set to 2048 for better performance on HPU"
    exit 1
fi

# Set the volume variable
volume=$PWD/data

# Build the Docker run command based on hardware mode
if [ "$hw_mode" = "hpu" ]; then
    docker run -d --rm --runtime=habana --name="vllm-service" -p $port_number:80 -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy -e HF_TOKEN=${HF_TOKEN} opea/vllm-gaudi:latest --enforce-eager --model $model_name  --tensor-parallel-size $parallel_number --host 0.0.0.0 --port 80 --block-size $block_size --max-num-seqs  $max_num_seqs --max-seq_len-to-capture $max_seq_len_to_capture
else
    docker run -d --rm --name="vllm-service" -p $port_number:80 --network=host -v $volume:/data -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy -e HF_TOKEN=${HF_TOKEN} -e VLLM_CPU_KVCACHE_SPACE=40 opea/vllm-cpu:latest --model $model_name --host 0.0.0.0 --port 80
fi
