#!/usr/bin/env bash

# SPDX-License-Identifier: Apache-2.0

export host_ip="192.165.1.21"
export DBQNA_HUGGINGFACEHUB_API_TOKEN="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"
export DBQNA_TGI_SERVICE_PORT=8008
export DBQNA_TGI_LLM_ENDPOINT="http://${host_ip}:${DBQNA_TGI_SERVICE_PORT}"
export DBQNA_LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export MODEL_ID=${DBQNA_LLM_MODEL_ID}
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="testpwd"
export POSTGRES_DB="chinook"
export DBQNA_TEXT_TO_SQL_PORT=18142
export DBQNA_UI_PORT=18143
