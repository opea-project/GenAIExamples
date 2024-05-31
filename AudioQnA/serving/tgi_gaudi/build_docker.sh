#!/bin/bash


# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

git clone https://github.com/huggingface/tgi-gaudi.git
cd ./tgi-gaudi/
docker build -t ghcr.io/huggingface/tgi-gaudi:1.2.1 . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
