# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

docker run -d --rm \
    --name="hallucination-detection" \
    -p 9080:9000 \
    --ipc=host \
    -e http_proxy=$http_proxy \
    -e https_proxy=$https_proxy \
    -e vLLM_ENDPOINT=$vLLM_ENDPOINT \
    -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
    -e LLM_MODEL=$LLM_MODEL \
    -e LOGFLAG=$LOGFLAG \
    opea/guardrails-hallucination-detection:latest
