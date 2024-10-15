# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CURRENT_DIR=$(pwd)

# Go to top level directory of this repo and build the image
cd "$(git rev-parse --show-toplevel)"

docker build \
    -f comps/llms/text-generation/vllm/ray/dependency/Dockerfile \
    -t opea/vllm_ray:habana \
    --network=host \
    --build-arg http_proxy=${http_proxy} \
    --build-arg https_proxy=${https_proxy} \
    --build-arg no_proxy=${no_proxy} .

cd $CURRENT_DIR
