#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
echo "IMAGE_REPO=${IMAGE_REPO}"

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/embedding-tei:latest -f comps/embeddings/langchain/docker/Dockerfile .
    docker build -t opea/retriever-qdrant:latest -f comps/retrievers/haystack/qdrant/docker/Dockerfile .
    docker build -t opea/reranking-tei:latest -f comps/reranks/tei/docker/Dockerfile .
    docker build -t opea/llm-tgi:latest -f comps/llms/text-generation/tgi/Dockerfile .
    docker build -t opea/dataprep-qdrant:latest -f comps/dataprep/qdrant/docker/Dockerfile .

    cd $WORKPATH/docker
    docker build --no-cache -t opea/chatqna:latest -f Dockerfile .

    cd $WORKPATH/docker/ui
    docker build --no-cache -t opea/chatqna-ui:latest -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/docker/xeon

    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export RERANK_MODEL_ID="BAAI/bge-reranker-base"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:6040"
    export TEI_RERANKING_ENDPOINT="http://${ip_address}:6041"
    export TGI_LLM_ENDPOINT="http://${ip_address}:6042"
    export QDRANT_HOST=${ip_address}
    export QDRANT_PORT=6333
    export INDEX_NAME="rag-qdrant"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export EMBEDDING_SERVICE_HOST_IP=${ip_address}
    export RETRIEVER_SERVICE_HOST_IP=${ip_address}
    export RERANK_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export EMBEDDING_SERVICE_PORT=6044
    export RETRIEVER_SERVICE_PORT=6045
    export RERANK_SERVICE_PORT=6046
    export LLM_SERVICE_PORT=6047
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:8912/v1/chatqna"
    export DATAPREP_SERVICE_ENDPOINT="http://${ip_address}:6043/v1/dataprep"

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

    if [[ "$IMAGE_REPO" != "" ]]; then
        # Replace the container name with a test-specific name
        echo "using image repository $IMAGE_REPO and image tag $IMAGE_TAG"
        sed -i "s#image: opea/chatqna:latest#image: opea/chatqna:${IMAGE_TAG}#g" compose_qdrant.yaml
        sed -i "s#image: opea/chatqna-ui:latest#image: opea/chatqna-ui:${IMAGE_TAG}#g" compose_qdrant.yaml
        sed -i "s#image: opea/chatqna-conversation-ui:latest#image: opea/chatqna-conversation-ui:${IMAGE_TAG}#g" compose_qdrant.yaml
        sed -i "s#image: opea/*#image: ${IMAGE_REPO}opea/#g" compose_qdrant.yaml
        cat compose_qdrant.yaml
    fi

    # Start Docker Containers
    docker compose -f compose_qdrant.yaml up -d
    n=0
    until [[ "$n" -ge 200 ]]; do
        docker logs tgi-service > tgi_service_start.log
        if grep -q Connected tgi_service_start.log; then
            break
        fi
        sleep 1s
        n=$((n+1))
    done
}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    if [[ $SERVICE_NAME == *"dataprep_upload_file"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_upload_link"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'link_list=["https://www.ces.tech/"]' "$URL")
    else
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    fi
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

    docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log

    # check response status
    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *"$EXPECTED_RESULT"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # tei for embedding service
    validate_services \
        "${ip_address}:6040/embed" \
        "[[" \
        "tei-embedding" \
        "tei-embedding-server" \
        '{"inputs":"What is Deep Learning?"}'

    # embedding microservice
    validate_services \
        "${ip_address}:6044/v1/embeddings" \
        '"text":"What is Deep Learning?","embedding":[' \
        "embedding" \
        "embedding-tei-server" \
        '{"text":"What is Deep Learning?"}'

    # test /v1/dataprep upload file
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt
    validate_services \
        "${ip_address}:6043/v1/dataprep" \
        "Data preparation succeeded" \
        "dataprep_upload_file" \
        "dataprep-qdrant-server"

    # test upload link
    validate_services \
        "${ip_address}:6043/v1/dataprep" \
        "Data preparation succeeded" \
        "dataprep_upload_link" \
        "dataprep-qdrant-server"

    # retrieval microservice
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_services \
        "${ip_address}:6045/v1/retrieval" \
        "retrieved_docs" \
        "retrieval" \
        "retriever-qdrant-server" \
        "{\"text\":\"What is Deep Learning?\",\"embedding\":${test_embedding}}"

    # tei for rerank microservice
    validate_services \
        "${ip_address}:6041/rerank" \
        '{"index":1,"score":' \
        "tei-rerank" \
        "tei-reranking-server" \
        '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'

    # rerank microservice
    validate_services \
        "${ip_address}:6046/v1/reranking" \
        "Deep learning is..." \
        "rerank" \
        "reranking-tei-xeon-server" \
        '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}'

    # tgi for llm service
    validate_services \
        "${ip_address}:6042/generate" \
        "generated_text" \
        "tgi-llm" \
        "tgi-service" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # llm microservice
    validate_services \
        "${ip_address}:6047/v1/chat/completions" \
        "data: " \
        "llm" \
        "llm-tgi-server" \
        '{"query":"Deep Learning"}'

}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${ip_address}:8912/v1/chatqna" \
        "data: " \
        "mega-chatqna" \
        "chatqna-xeon-backend-server" \
        '{"messages": "What is the revenue of Nike in 2023?"}'

}

function validate_frontend() {
    cd $WORKPATH/docker/ui/svelte
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
    source activate ${conda_env_name}

    sed -i "s/localhost/$ip_address/g" playwright.config.ts

    npm install && npm ci && npx playwright install --with-deps
    node -v && npm -v && pip list

    exit_status=0
    npx playwright test || exit_status=$?

    if [ $exit_status -ne 0 ]; then
        echo "[TEST INFO]: ---------frontend test failed---------"
        exit $exit_status
    else
        echo "[TEST INFO]: ---------frontend test passed---------"
    fi
}

function stop_docker() {
    cd $WORKPATH/docker/xeon
    docker compose -f compose_qdrant.yaml stop && docker compose -f compose_qdrant.yaml rm -f
}

function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "" ]]; then build_docker_images; fi
    start_time=$(date +%s)
    start_services
    end_time=$(date +%s)
    duration=$((end_time-start_time))
    echo "Mega service start duration is $duration s" && sleep 1s

    validate_microservices
    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
