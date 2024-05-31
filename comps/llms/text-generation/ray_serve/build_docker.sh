#!/bin/bash


# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

cd docker

docker build \
    -f Dockerfile ../../ \
    -t ray_serve:habana \
    --network=host \
    --build-arg http_proxy=${http_proxy} \
    --build-arg https_proxy=${https_proxy} \
    --build-arg no_proxy=${no_proxy}
