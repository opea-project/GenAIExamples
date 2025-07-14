#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export host_ip=${ip_address}
export no_proxy=$no_proxy,$host_ip,dbqna-xeon-react-ui-server,text2sql-service,tgi-service,postgres-container
export HF_TOKEN=${HF_TOKEN}
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpwd
export POSTGRES_DB=chinook
export TGI_PORT=8008
export TEXT2SQL_PORT=9090
export TGI_LLM_ENDPOINT="http://${host_ip}:${TGI_PORT}"
export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
