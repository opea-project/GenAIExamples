# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

docker run -d --rm \
    --name="llm-ray-server" \
    -p 9000:9000 \
    --ipc=host \
    -e http_proxy=$http_proxy \
    -e https_proxy=$https_proxy \
    -e RAY_Serve_ENDPOINT=$RAY_Serve_ENDPOINT \
    -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
    -e LLM_MODEL=$LLM_MODEL \
    opea/llm-ray:latest
