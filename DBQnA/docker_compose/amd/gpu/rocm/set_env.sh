#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

export host_ip=""
export DBQNA_HUGGINGFACEHUB_API_TOKEN=""
export DBQNA_TGI_SERVICE_PORT=8008
export DBQNA_TGI_LLM_ENDPOINT="http://${host_ip}:${DBQNA_TGI_SERVICE_PORT}"
export DBQNA_LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export MODEL_ID=${DBQNA_LLM_MODEL_ID}
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="testpwd"
export POSTGRES_DB="chinook"
export DBQNA_TEXT_TO_SQL_PORT=9090
export DBQNA_UI_PORT=5174
