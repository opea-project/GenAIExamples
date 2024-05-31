#!/bin/bash


# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

git clone https://github.com/vllm-project/vllm.git
cd ./vllm/
docker build -f Dockerfile.cpu -t vllm:cpu --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
