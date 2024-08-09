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
    docker build -t opea/retriever-redis:latest -f comps/retrievers/langchain/redis/docker/Dockerfile .
    docker build -t opea/reranking-tei:latest -f comps/reranks/tei/docker/Dockerfile .
    docker build -t opea/llm-tgi:latest -f comps/llms/text-generation/tgi/Dockerfile .
    docker build -t opea/dataprep-redis:latest -f comps/dataprep/redis/langchain/docker/Dockerfile .
    docker build -t opea/guardrails-tgi:latest -f comps/guardrails/llama_guard/docker/Dockerfile .

#    cd ..
#    git clone https://github.com/huggingface/tei-gaudi
#    cd tei-gaudi/
#    docker build --no-cache -f Dockerfile-hpu -t opea/tei-gaudi:latest .

    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.1
    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5

    cd $WORKPATH/docker
    docker build --no-cache -t opea/chatqna-guardrails:latest -f Dockerfile_guardrails .

    cd $WORKPATH/docker/ui
    docker build --no-cache -t opea/chatqna-ui:latest -f docker/Dockerfile .

    docker images
}

function start_services() {
    # build tei-gaudi for each test instead of pull from local registry
    cd $WORKPATH
    git clone https://github.com/huggingface/tei-gaudi
    cd tei-gaudi/
    docker build --no-cache -q -f Dockerfile-hpu -t opea/tei-gaudi:latest .

    cd $WORKPATH/docker/gaudi
    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export RERANK_MODEL_ID="BAAI/bge-reranker-base"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:8090"
    export TEI_RERANKING_ENDPOINT="http://${ip_address}:8808"
    export TGI_LLM_ENDPOINT="http://${ip_address}:8008"
    export REDIS_URL="redis://${ip_address}:6379"
    export INDEX_NAME="rag-redis"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export EMBEDDING_SERVICE_HOST_IP=${ip_address}
    export RETRIEVER_SERVICE_HOST_IP=${ip_address}
    export RERANK_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export GUARDRAIL_SERVICE_HOST_IP=${ip_address}
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:8888/v1/chatqna"
    export DATAPREP_SERVICE_ENDPOINT="http://${ip_address}:6007/v1/dataprep"
    export GURADRAILS_MODEL_ID="meta-llama/Meta-Llama-Guard-2-8B"
    export SAFETY_GUARD_MODEL_ID="meta-llama/Meta-Llama-Guard-2-8B"
    export SAFETY_GUARD_ENDPOINT="http://${ip_address}:8088"

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

    if [[ "$IMAGE_REPO" != "" ]]; then
        # Replace the container name with a test-specific name
        echo "using image repository $IMAGE_REPO and image tag $IMAGE_TAG"
        sed -i "s#image: opea/chatqna-guardrails:latest#image: opea/chatqna:${IMAGE_TAG}#g" compose_guardrails.yaml
        sed -i "s#image: opea/chatqna-ui:latest#image: opea/chatqna-ui:${IMAGE_TAG}#g" compose_guardrails.yaml
        sed -i "s#image: opea/chatqna-conversation-ui:latest#image: opea/chatqna-conversation-ui:${IMAGE_TAG}#g" compose_guardrails.yaml
        sed -i "s#image: opea/*#image: ${IMAGE_REPO}opea/#g" compose_guardrails.yaml
        sed -i "s#image: ${IMAGE_REPO}opea/tei-gaudi:latest#image: opea/tei-gaudi:latest#g" compose_guardrails.yaml
        echo "cat compose_guardrails.yaml"
        cat compose_guardrails.yaml
    fi

    # Start Docker Containers
    docker compose -f compose_guardrails.yaml up -d
    n=0
    until [[ "$n" -ge 400 ]]; do
        docker logs tgi-gaudi-server > tgi_service_start.log
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

    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

        local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
            exit 1
        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
        exit 1
    fi
    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # tei for embedding service
    validate_services \
        "${ip_address}:8090/embed" \
        "\[\[" \
        "tei-embedding" \
        "tei-embedding-gaudi-server" \
        '{"inputs":"What is Deep Learning?"}'

    # embedding microservice
    validate_services \
        "${ip_address}:6000/v1/embeddings" \
        '"text":"What is Deep Learning?","embedding":\[' \
        "embedding" \
        "embedding-tei-server" \
        '{"text":"What is Deep Learning?"}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # retrieval microservice
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_services \
        "${ip_address}:7000/v1/retrieval" \
        " " \
        "retrieval" \
        "retriever-redis-server" \
        "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}"

    # tei for rerank microservice
    validate_services \
        "${ip_address}:8808/rerank" \
        '{"index":1,"score":' \
        "tei-rerank" \
        "tei-reranking-gaudi-server" \
        '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'

    # rerank microservice
    validate_services \
        "${ip_address}:8000/v1/reranking" \
        "Deep learning is..." \
        "rerank" \
        "reranking-tei-gaudi-server" \
        '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}'

    # tgi for llm service
    validate_services \
        "${ip_address}:8008/generate" \
        "generated_text" \
        "tgi-llm" \
        "tgi-gaudi-server" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # llm microservice
    validate_services \
        "${ip_address}:9000/v1/chat/completions" \
        "data: " \
        "llm" \
        "llm-tgi-gaudi-server" \
        '{"query":"What is Deep Learning?"}'

    # tgi for guardrails service
    validate_services \
        "${ip_address}:8008/generate" \
        "generated_text" \
        "tgi-guardrails" \
        "tgi-guardrails-server" \
        '{"inputs":"How do you buy a tiger in the US?","parameters":{"max_new_tokens":32}}'

    # guardrails microservice
    validate_services \
        "${ip_address}:9090/v1/guardrails" \
        "Violated policies" \
        "guardrails" \
        "guardrails-tgi-gaudi-server" \
        '{"text":"How do you buy a tiger in the US?"}'

}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${ip_address}:8888/v1/chatqna" \
        "billion" \
        "mega-chatqna" \
        "chatqna-gaudi-guardrails-server" \
        '{"messages": "What is the revenue of Nike in 2023?"}'

}

function validate_frontend() {
    cd $WORKPATH/docker/ui/svelte
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
#    conda remove -n ${conda_env_name} --all -y
#    conda create -n ${conda_env_name} python=3.12 -y
    source activate ${conda_env_name}

    sed -i "s/localhost/$ip_address/g" playwright.config.ts

#    conda install -c conda-forge nodejs -y
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
    cd $WORKPATH/docker/gaudi
    docker compose -f compose_guardrails.yaml down
}

function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "" ]]; then build_docker_images; fi
    start_time=$(date +%s)
    start_services
    end_time=$(date +%s)
    duration=$((end_time-start_time))
    echo "Mega service start duration is $duration s"

    validate_microservices
    validate_megaservice
    # validate_frontend

    stop_docker
    echo y | docker system prune

}

main
