# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

cd ../../../../

docker build \
    -f comps/llms/text-generation/vllm/ray/server/docker/Dockerfile \
    -t opea/vllm_ray:habana \
    --network=host \
    --build-arg http_proxy=${http_proxy} \
    --build-arg https_proxy=${https_proxy} \
    --build-arg no_proxy=${no_proxy} .
