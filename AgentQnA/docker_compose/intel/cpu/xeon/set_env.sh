# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

if [[ -z "${WORKDIR}" ]]; then
	echo "Please set WORKDIR environment variable"
	exit 0
fi
echo "WORKDIR=${WORKDIR}"
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
export ip_address=$(hostname -I | awk '{print $1}')
export recursion_limit_worker=12
export recursion_limit_supervisor=10
export model="gpt-4o-mini-2024-07-18"
export temperature=0
export max_new_tokens=4096
export OPENAI_API_KEY=${OPENAI_API_KEY}
export WORKER_AGENT_URL="http://${ip_address}:9095/v1/chat/completions"
export SQL_AGENT_URL="http://${ip_address}:9096/v1/chat/completions"
export RETRIEVAL_TOOL_URL="http://${ip_address}:8889/v1/retrievaltool"
export CRAG_SERVER=http://${ip_address}:8080
export db_name=Chinook
export db_path="sqlite:////home/user/chinook-db/Chinook_Sqlite.sqlite"

if [ ! -f $WORKDIR/GenAIExamples/AgentQnA/tests/Chinook_Sqlite.sqlite ]; then
    echo "Download Chinook_Sqlite!"
    wget  -O $WORKDIR/GenAIExamples/AgentQnA/tests/Chinook_Sqlite.sqlite  https://raw.githubusercontent.com/lerocha/chinook-database/refs/heads/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite
fi

# retriever
export host_ip=$(hostname -I | awk '{print $1}')
export HF_CACHE_DIR=${HF_CACHE_DIR}
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export no_proxy=${no_proxy}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6006"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export RERANK_TYPE="tei"
export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8889/v1/retrievaltool"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/ingest"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6008/v1/dataprep/get"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:6009/v1/dataprep/delete"


export no_proxy="$no_proxy,rag-agent-endpoint,sql-agent-endpoint,react-agent-endpoint,agent-ui"

#docker compose -f $WORKDIR/GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml -f compose.yaml up -d
