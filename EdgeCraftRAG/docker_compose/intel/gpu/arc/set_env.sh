#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export MODEL_PATH=${MODEL_PATH}
export DOC_PATH=${DOC_PATH}
export TMPFILE_PATH=${TMPFILE_PATH}
export HOST_IP=${HOST_IP}
export LLM_MODEL=${LLM_MODEL}
export HF_ENDPOINT=${HF_ENDPOINT}
export vLLM_ENDPOINT=${vLLM_ENDPOINT}
export HF_TOKEN=${HF_TOKEN}
export no_proxy="localhost, 127.0.0.1, 192.168.1.1"
export UI_UPLOAD_PATH=${UI_UPLOAD_PATH}
export LLM_MODEL_PATH=${LLM_MODEL_PATH}

export VLLM_SERVICE_PORT_B60=${VLLM_SERVICE_PORT_B60}
export VLLM_SERVICE_PORT_A770=${VLLM_SERVICE_PORT_A770}
export TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE}

export vLLM_ENDPOINT=${vLLM_ENDPOINT}
export MAX_NUM_SEQS=${MAX_NUM_SEQS}
export MAX_NUM_BATCHED_TOKENS=${MAX_NUM_BATCHED_TOKENS}
export MAX_MODEL_LEN=${MAX_MODEL_LEN}
export LOAD_IN_LOW_BIT=${LOAD_IN_LOW_BIT}
export CCL_DG2_USM=${CCL_DG2_USM}
export ZE_AFFINITY_MASK=${ZE_AFFINITY_MASK}
