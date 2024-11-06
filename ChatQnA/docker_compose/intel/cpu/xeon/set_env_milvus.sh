export host_ip=$(hostname -i)
export DOCKER_VOLUME_DIRECTORY="~/OPEA/tmp"
export http_proxy=${http_proxy}
export https_proxy=${http_proxy}
export no_proxy=${no_proxy},chatqna-xeon-ui-server,chatqna-xeon-backend-server,tei-embedding-service,tei-reranking-service,tgi-service,vllm_service,retriever-service,dataprep-milvus-service
export MILVUS_HOST=${host_ip}
export MILVUS_PORT=19530
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"

