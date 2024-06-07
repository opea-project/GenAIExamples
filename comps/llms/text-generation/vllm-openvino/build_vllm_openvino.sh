#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


git clone --branch openvino-model-executor https://github.com/ilya-lavrenov/vllm.git
cd ./vllm/
docker build -t vllm:openvino -f Dockerfile.openvino . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
