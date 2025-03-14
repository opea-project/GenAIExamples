#/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Function to prompt for input and set environment variables
prompt_for_env_var() {
  local var_name="$1"
  local prompt_message="$2"
  local default_value="$3"
  local mandatory="$4"

  if [[ "$mandatory" == "true" ]]; then
    while [[ -z "$value" ]]; do
      read -p "$prompt_message [default: \"${default_value}\"]: " value
      if [[ -z "$value" ]]; then
        echo "Input cannot be empty. Please try again."
      fi
    done
  else
    read -p "$prompt_message [default: \"${default_value}\"]: " value
  fi

  if [[ "$value" == "" ]]; then
      export "$var_name"="$default_value"
  else
      export "$var_name"="$value"
  fi
}

pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

# Prompt the user for each required environment variable
prompt_for_env_var "EMBEDDING_MODEL_ID" "Enter the EMBEDDING_MODEL_ID" "BAAI/bge-base-en-v1.5" false
prompt_for_env_var "HUGGINGFACEHUB_API_TOKEN" "Enter the HUGGINGFACEHUB_API_TOKEN" "" true
prompt_for_env_var "RERANK_MODEL_ID" "Enter the RERANK_MODEL_ID" "BAAI/bge-reranker-base" false
prompt_for_env_var "LLM_MODEL_ID" "Enter the LLM_MODEL_ID" "meta-llama/Meta-Llama-3-8B-Instruct" false
prompt_for_env_var "INDEX_NAME" "Enter the INDEX_NAME" "rag-redis" false
prompt_for_env_var "NUM_CARDS" "Enter the number of Gaudi devices" "1" false
prompt_for_env_var "host_ip" "Enter the host_ip" "$(curl ifconfig.me)" false

#Query for enabling http_proxy
prompt_for_env_var "http_proxy" "Enter the http_proxy." "" false

#Query for enabling https_proxy
prompt_for_env_var "https_proxy" "Enter the https_proxy." "" false

#Query for enabling no_proxy
prompt_for_env_var "no_proxy" "Enter the no_proxy." "" false

# Query for enabling logging
read -p "Enable logging? (yes/no): " logging && logging=$(echo "$logging" | tr '[:upper:]' '[:lower:]')
if [[ "$logging" == "yes" || "$logging" == "y" ]]; then
  export LOGFLAG=true
else
  export LOGFLAG=false
fi

# Query for enabling OpenTelemetry Tracing Endpoint
read -p "Enable OpenTelemetry Tracing Endpoint? (yes/no): " telemetry && telemetry=$(echo "$telemetry" | tr '[:upper:]' '[:lower:]')
if [[ "$telemetry" == "yes" || "$telemetry" == "y" ]]; then
    export JAEGER_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K[^ ]+')
    export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=grpc://$JAEGER_IP:4317
    export TELEMETRY_ENDPOINT=http://$JAEGER_IP:4318/v1/traces
    telemetry_flag=true
else
    telemetry_flag=false
fi

# Generate the .env file
cat <<EOF > .env
#!/bin/bash
# Set all required ENV values
export TAG=${TAG}
export EMBEDDING_MODEL_ID=${EMBEDDING_MODEL_ID}
export HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN
export RERANK_MODEL_ID=${RERANK_MODEL_ID}
export LLM_MODEL_ID=${LLM_MODEL_ID}
export INDEX_NAME=${INDEX_NAME}
export NUM_CARDS=${NUM_CARDS}
export host_ip=${host_ip}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
export no_proxy=${no_proxy}
export LOGFLAG=${LOGFLAG}
export JAEGER_IP=${JAEGER_IP}
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=${OTEL_EXPORTER_OTLP_TRACES_ENDPOINT}
export TELEMETRY_ENDPOINT=${TELEMETRY_ENDPOINT}
EOF

echo ".env file has been created with the following content:"
cat .env
