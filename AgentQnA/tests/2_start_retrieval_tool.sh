#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')

export HF_CACHE_DIR=$WORKDIR/hf_cache
if [ ! -d "$HF_CACHE_DIR" ]; then
    echo "Creating HF_CACHE directory"
    mkdir -p "$HF_CACHE_DIR"
fi

function start_retrieval_tool() {
    echo "Starting Retrieval tool"
    cd $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool/docker/
    bash launch_retrieval_tool.sh
}

echo "==================== Start retrieval tool ===================="
start_retrieval_tool
sleep 20 # needed for downloading the models
echo "==================== Retrieval tool started ===================="
