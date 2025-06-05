#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

pushd "../../" > /dev/null
ls -l
source .set_env.sh
popd > /dev/null

export host_ip=${ip_address}
export DBQNA_HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
export DBQNA_TGI_SERVICE_PORT=8008
export DBQNA_TGI_LLM_ENDPOINT="http://${host_ip}:${DBQNA_TGI_SERVICE_PORT}"
export DBQNA_LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export MODEL_ID=${DBQNA_LLM_MODEL_ID}
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="testpwd"
export POSTGRES_DB="chinook"
export DBQNA_TEXT_TO_SQL_PORT=9090
export DBQNA_UI_PORT=5174
export build_texttosql_url="${ip_address}:${DBQNA_TEXT_TO_SQL_PORT}/v1"
