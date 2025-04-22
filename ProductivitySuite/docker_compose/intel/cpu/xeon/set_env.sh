# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export DB_NAME="opea"
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export LLM_MODEL_ID_CODEGEN="Intel/neural-chat-7b-v3-3"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export BACKEND_SERVICE_ENDPOINT_CHATQNA="http://${host_ip}:8888/v1/chatqna"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/delete"
export BACKEND_SERVICE_ENDPOINT_CODEGEN="http://${host_ip}:7778/v1/codegen"
export BACKEND_SERVICE_ENDPOINT_DOCSUM="http://${host_ip}:8890/v1/docsum"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/ingest"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get"
export CHAT_HISTORY_CREATE_ENDPOINT="http://${host_ip}:6012/v1/chathistory/create"
export CHAT_HISTORY_CREATE_ENDPOINT="http://${host_ip}:6012/v1/chathistory/create"
export CHAT_HISTORY_DELETE_ENDPOINT="http://${host_ip}:6012/v1/chathistory/delete"
export CHAT_HISTORY_GET_ENDPOINT="http://${host_ip}:6012/v1/chathistory/get"
export PROMPT_SERVICE_GET_ENDPOINT="http://${host_ip}:6018/v1/prompt/get"
export PROMPT_SERVICE_CREATE_ENDPOINT="http://${host_ip}:6018/v1/prompt/create"
export PROMPT_SERVICE_DELETE_ENDPOINT="http://${host_ip}:6018/v1/prompt/delete"
export KEYCLOAK_SERVICE_ENDPOINT="http://${host_ip}:8080"
export DocSum_COMPONENT_NAME="OpeaDocSumTgi"

#Set no proxy
export no_proxy="$no_proxy,tgi_service_codegen,llm_codegen,tei-embedding-service,tei-reranking-service,chatqna-xeon-backend-server,retriever,tgi-service,redis-vector-db,whisper,llm-docsum-tgi,docsum-xeon-backend-server,mongo,codegen"
