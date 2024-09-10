# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

cd ../../../../
docker build  \
    -t opea/llm-vllm:latest \
    --build-arg https_proxy=$https_proxy \
    --build-arg http_proxy=$http_proxy \
    -f comps/llms/text-generation/vllm/docker/Dockerfile .
