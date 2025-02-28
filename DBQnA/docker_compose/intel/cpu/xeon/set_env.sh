#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

#export host_ip=$(hostname -I | awk '{print $1}')

if [ -z "${HUGGINGFACEHUB_API_TOKEN}" ]; then
    echo "Error: HUGGINGFACEHUB_API_TOKEN is not set. Please set HUGGINGFACEHUB_API_TOKEN."
fi

if [ -z "${host_ip}" ]; then
    echo "Error: host_ip is not set. Please set host_ip first."
fi
export no_proxy=$no_proxy,$host_ip,dbqna-xeon-react-ui-server,text2sql-service,tgi-service,postgres-container
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export TGI_PORT=8008
export TGI_LLM_ENDPOINT="http://${host_ip}:${TGI_PORT}"
export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpwd
export POSTGRES_DB=chinook
export TEXT2SQL_PORT=9090
"set_env.sh" 27L, 974B
