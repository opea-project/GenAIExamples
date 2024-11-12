#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

BASEDIR="$( cd "$( dirname "$0" )" && pwd )"
git clone https://github.com/vllm-project/vllm.git vllm
cd ./vllm/ && git checkout v0.6.1
docker build -t vllm-openvino:latest -f Dockerfile.openvino . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
cd $BASEDIR && rm -rf vllm
