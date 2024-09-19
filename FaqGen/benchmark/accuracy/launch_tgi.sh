# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

max_input_tokens=3072
max_total_tokens=4096
port_number=8082
model_name="mistralai/Mixtral-8x7B-Instruct-v0.1"
volume="./data"
docker run -it --rm \
    --name="tgi_Mixtral" \
    -p $port_number:80 \
    -v $volume:/data \
    --runtime=habana \
    --restart always \
    -e HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN \
    -e HABANA_VISIBLE_DEVICES=all \
    -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
    -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true \
    --cap-add=sys_nice \
    --ipc=host \
    -e HTTPS_PROXY=$https_proxy \
    -e HTTP_PROXY=$https_proxy \
    ghcr.io/huggingface/tgi-gaudi:2.0.1 \
    --model-id $model_name \
    --max-input-tokens $max_input_tokens \
    --max-total-tokens $max_total_tokens \
    --sharded true \
    --num-shard 2
