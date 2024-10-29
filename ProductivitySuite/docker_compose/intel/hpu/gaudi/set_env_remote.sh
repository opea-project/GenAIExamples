# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#!/bin/bash

# Check if the model_configs.json file exists
if [ -f model_configs.json ]; then
    # If the file exists, set the MODEL_CONFIGS environment variable using the content of the file
    export MODEL_CONFIGS=$(jq -c . model_configs.json)
fi
export MONGO_HOST=${host_ip}
export MONGO_PORT=27017
export DB_NAME="opea"
export COLLECTION_NAME="Conversations"
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-70B-Instruct"
export LLM_MODEL_ID_CODEGEN="meta-llama/CodeLlama-7b-hf"
export TEI_EMBEDDING_ENDPOINT="${remote_host}/${embedding_endpoint}"
export TEI_RERANKING_ENDPOINT="${remote_host}/${reranking_endpoint}"
export TGI_LLM_ENDPOINT="${remote_host}/${tgi_endpoint}"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=${hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP_DOCSUM=${host_ip}
export LLM_SERVICE_HOST_IP_FAQGEN=${host_ip}
export LLM_SERVICE_HOST_IP_CODEGEN=${host_ip}
export LLM_SERVICE_HOST_IP_CHATQNA=${host_ip}
export TGI_LLM_ENDPOINT_CHATQNA="${remote_host}/${tgi_endpoint}"
export TGI_LLM_ENDPOINT_CODEGEN="${remote_host}/${tgi_endpoint}"
export TGI_LLM_ENDPOINT_FAQGEN="${remote_host}/${tgi_endpoint}"
export TGI_LLM_ENDPOINT_DOCSUM="${remote_host}/${tgi_endpoint}"
export BACKEND_SERVICE_ENDPOINT_CHATQNA="http://${host_ip}:8888/v1/chatqna"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/delete_file"
export BACKEND_SERVICE_ENDPOINT_FAQGEN="http://${host_ip}:8889/v1/faqgen"
export BACKEND_SERVICE_ENDPOINT_CODEGEN="http://${host_ip}:7778/v1/codegen"
export BACKEND_SERVICE_ENDPOINT_DOCSUM="http://${host_ip}:8890/v1/docsum"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_file"
export CHAT_HISTORY_CREATE_ENDPOINT="http://${host_ip}:6012/v1/chathistory/create"
export CHAT_HISTORY_CREATE_ENDPOINT="http://${host_ip}:6012/v1/chathistory/create"
export CHAT_HISTORY_DELETE_ENDPOINT="http://${host_ip}:6012/v1/chathistory/delete"
export CHAT_HISTORY_GET_ENDPOINT="http://${host_ip}:6012/v1/chathistory/get"
export PROMPT_SERVICE_GET_ENDPOINT="http://${host_ip}:6018/v1/prompt/get"
export PROMPT_SERVICE_CREATE_ENDPOINT="http://${host_ip}:6018/v1/prompt/create"
export KEYCLOAK_SERVICE_ENDPOINT="http://${host_ip}:8080"
export LLM_SERVICE_HOST_PORT_FAQGEN=9002
export LLM_SERVICE_HOST_PORT_CODEGEN=9001
export LLM_SERVICE_HOST_PORT_DOCSUM=9003
export PROMPT_COLLECTION_NAME="prompt"
export CLIENTID=${clientid}
export CLIENT_SECRET=${client_secret}
export TOKEN_URL=${token_url}