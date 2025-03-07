#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
export host_ip=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}
    # If the opea_branch isn't main, replace the git clone branch in Dockerfile.
    if [[ "${opea_branch}" != "main" ]]; then
        cd $WORKPATH
        OLD_STRING="RUN git clone --depth 1 https://github.com/opea-project/GenAIComps.git"
        NEW_STRING="RUN git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git"
        find . -type f -name "Dockerfile*" | while read -r file; do
            echo "Processing file: $file"
            sed -i "s|$OLD_STRING|$NEW_STRING|g" "$file"
        done
    fi

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/tgi-gaudi:2.3.1
    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

    export TEI_EMBEDDER_PORT=11633
    export LLM_ENDPOINT_PORT=11634
    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
    export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-8B-Instruct"
    export OPENAI_LLM_MODEL="gpt-4o"
    export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:${TEI_EMBEDDER_PORT}"
    export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-8B-Instruct"
    export TGI_LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
    export NEO4J_PORT1=11631
    export NEO4J_PORT2=11632
    export NEO4J_URI="bolt://${host_ip}:${NEO4J_PORT2}"
    export NEO4J_URL="bolt://${host_ip}:${NEO4J_PORT2}"
    export NEO4J_USERNAME="neo4j"
    export NEO4J_PASSWORD="neo4jtest"
    export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:5000/v1/dataprep/ingest"
    export LOGFLAG=True
    export MAX_INPUT_TOKENS=4096
    export MAX_TOTAL_TOKENS=8192
    export DATAPREP_PORT=11103
    export RETRIEVER_PORT=11635
    export MEGA_SERVICE_PORT=8888
    unset OPENAI_API_KEY

    # Start Docker Containers
    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs tgi-gaudi-server > ${LOG_PATH}/tgi_service_start.log
        if grep -q Connected ${LOG_PATH}/tgi_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
}

function validate_service() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    if [[ $SERVICE_NAME == *"extract_graph_neo4j"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
        echo $HTTP_RESPONSE
    elif [[ $SERVICE_NAME == *"neo4j-apoc"* ]]; then
         HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" "$URL")
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
    if [[ "$SERVICE_NAME" == "neo4j-apoc" ]]; then
        echo "[ $SERVICE_NAME ] Skipping content check for neo4j-apoc."
    else
        if [[ "$RESPONSE_BODY" != *"$EXPECTED_RESULT"* ]]; then
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
            exit 1
        else
            echo "[ $SERVICE_NAME ] Content is as expected."
        fi
    fi

    sleep 5s
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # validate neo4j-apoc
    validate_service \
        "${host_ip}:${NEO4J_PORT1}" \
        "200 OK" \
        "neo4j-apoc" \
        "neo4j-apoc" \
        ""

    # tei for embedding service
    validate_service \
        "${host_ip}:${TEI_EMBEDDER_PORT}/embed" \
        "[[" \
        "tei-embedding-service" \
        "tei-embedding-serving" \
        '{"inputs":"What is Deep Learning?"}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # tgi for llm service
    validate_service \
        "${host_ip}:${LLM_ENDPOINT_PORT}/generate" \
        "generated_text" \
        "tgi-gaudi-service" \
        "tgi-gaudi-server" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # test /v1/dataprep/ingest graph extraction
    echo "Like many companies in the O&G sector, the stock of Chevron (NYSE:CVX) has declined about 10% over the past 90-days despite the fact that Q2 consensus earnings estimates have risen sharply (~25%) during that same time frame. Over the years, Chevron has kept a very strong balance sheet. FirstEnergy (NYSE:FE – Get Rating) posted its earnings results on Tuesday. The utilities provider reported $0.53 earnings per share for the quarter, topping the consensus estimate of $0.52 by $0.01, RTT News reports. FirstEnergy had a net margin of 10.85% and a return on equity of 17.17%. The Dáil was almost suspended on Thursday afternoon after Sinn Féin TD John Brady walked across the chamber and placed an on-call pager in front of the Minister for Housing Darragh O’Brien during a debate on retained firefighters. Mr O’Brien said Mr Brady had taken part in an act of theatre that was obviously choreographed.Around 2,000 retained firefighters around the country staged a second day of industrial action on Tuesday and are due to start all out-strike action from next Tuesday. The mostly part-time workers, who keep the services going outside of Ireland’s larger urban centres, are taking industrial action in a dispute over pay and working conditions. Speaking in the Dáil, Sinn Féin deputy leader Pearse Doherty said firefighters had marched on Leinster House today and were very angry at the fact the Government will not intervene. Reintroduction of tax relief on mortgages needs to be considered, O’Brien says. Martin withdraws comment after saying People Before Profit would ‘put the jackboot on people’ Taoiseach ‘propagated fears’ farmers forced to rewet land due to nature restoration law – Cairns An intervention is required now. I’m asking you to make an improved offer in relation to pay for retained firefighters, Mr Doherty told the housing minister.I’m also asking you, and challenging you, to go outside after this Order of Business and meet with the firefighters because they are just fed up to the hilt in relation to what you said.Some of them have handed in their pagers to members of the Opposition and have challenged you to wear the pager for the next number of weeks, put up with an €8,600 retainer and not leave your community for the two and a half kilometres and see how you can stand over those type of pay and conditions. At this point, Mr Brady got up from his seat, walked across the chamber and placed the pager on the desk in front of Mr O’Brien. Ceann Comhairle Seán Ó Fearghaíl said the Sinn Féin TD was completely out of order and told him not to carry out a charade in this House, adding it was absolutely outrageous behaviour and not to be encouraged.Mr O’Brien said Mr Brady had engaged in an act of theatre here today which was obviously choreographed and was then interrupted with shouts from the Opposition benches. Mr Ó Fearghaíl said he would suspend the House if this racket continues.Mr O’Brien later said he said he was confident the dispute could be resolved and he had immense regard for firefighters. The minister said he would encourage the unions to re-engage with the State’s industrial relations process while also accusing Sinn Féin of using the issue for their own political gain." > $LOG_PATH/dataprep_file.txt
    validate_service \
        "http://${host_ip}:${DATAPREP_PORT}/v1/dataprep/ingest" \
        "Data preparation succeeded" \
        "extract_graph_neo4j" \
        "dataprep-neo4j-llamaindex"

    sleep 2m

    # retrieval microservice
    validate_service \
        "${host_ip}:${RETRIEVER_PORT}/v1/retrieval" \
        "documents" \
        "retriever_community_answers_neo4j" \
        "retriever-neo4j" \
        "{\"messages\": [{\"role\": \"user\",\"content\": \"Who is John Brady and has he had any confrontations?\"}]}"

    }

function validate_megaservice() {
    # Curl the Mega Service
    validate_service \
        "${host_ip}:${MEGA_SERVICE_PORT}/v1/graphrag" \
        "data: " \
        "graphrag-megaservice" \
        "graphrag-gaudi-backend-server" \
        "{\"model\": \"gpt-4o-mini\",\"messages\": [{\"role\": \"user\",\"content\": \"Who is John Brady and has he had any confrontations?\"}]}"

}

function validate_frontend() {
    cd $WORKPATH/ui/svelte
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
    if conda info --envs | grep -q "$conda_env_name"; then
        echo "$conda_env_name exist!"
    else
        conda create -n ${conda_env_name} python=3.12 -y
    fi
    source activate ${conda_env_name}

    sed -i "s/localhost/$host_ip/g" playwright.config.ts

    conda install -c conda-forge nodejs=22.6.0 -y
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
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose  -f compose.yaml stop && docker compose -f compose.yaml rm -f
}

function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_time=$(date +%s)
    start_services
    end_time=$(date +%s)
    duration=$((end_time-start_time))
    echo "Mega service start duration is $duration s"

    validate_microservices
    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
