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
export DocSum_COMPONENT_NAME="OpeaDocSumTgi"

#Set no proxy
export no_proxy="$no_proxy,tgi_service_codegen,llm_codegen,tei-embedding-service,tei-reranking-service,chatqna-xeon-backend-server,retriever,tgi-service,redis-vector-db,whisper,llm-docsum-tgi,docsum-xeon-backend-server,mongo,codegen"
