    #!/bin/bash
    # Copyright (C) 2024 Intel Corporation
    # SPDX-License-Identifier: Apache-2.0

    # for test

    set -xe

    WORKPATH=$(dirname "$PWD")
    LOG_PATH="$WORKPATH/tests"
    ip_address=$(hostname -I | awk '{print $1}')

    function build_docker_images() {
        cd $WORKPATH
        git clone https://github.com/opea-project/GenAIComps.git
        cd GenAIComps

        docker build --no-cache -t opea/embedding-tei:latest  -f comps/embeddings/langchain/docker/Dockerfile .
        docker build --no-cache -t opea/web-retriever-chroma:latest  -f comps/web_retrievers/langchain/chroma/docker/Dockerfile .
        docker build --no-cache -t opea/reranking-tei:latest  -f comps/reranks/tei/docker/Dockerfile .
        docker build --no-cache -t opea/llm-tgi:latest  -f comps/llms/text-generation/tgi/Dockerfile .

        cd ..
        git clone https://github.com/huggingface/tei-gaudi
        cd tei-gaudi/
        docker build --no-cache -f Dockerfile-hpu -t opea/tei-gaudi:latest .

        docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.2
        docker pull ghcr.io/huggingface/tgi-gaudi:2.0.1
        cd $WORKPATH/docker
        docker build --no-cache -t opea/searchqna:latest -f Dockerfile .

        cd $WORKPATH/docker/ui
        docker build --no-cache -t opea/searchqna-ui:latest -f docker/Dockerfile .

        docker images
    }

    function start_services() {
        cd $WORKPATH/docker/gaudi
        export GOOGLE_CSE_ID=$GOOGLE_CSE_ID
        export GOOGLE_API_KEY=$GOOGLE_API_KEY
        export HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN

        export EMBEDDING_MODEL_ID=BAAI/bge-base-en-v1.5
        export TEI_EMBEDDING_ENDPOINT=http://$ip_address:3001
        export RERANK_MODEL_ID=BAAI/bge-reranker-base
        export TEI_RERANKING_ENDPOINT=http://$ip_address:3004

        export TGI_LLM_ENDPOINT=http://$ip_address:3006
        export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

        export MEGA_SERVICE_HOST_IP=${ip_address}
        export EMBEDDING_SERVICE_HOST_IP=${ip_address}
        export WEB_RETRIEVER_SERVICE_HOST_IP=${ip_address}
        export RERANK_SERVICE_HOST_IP=${ip_address}
        export LLM_SERVICE_HOST_IP=${ip_address}

        export EMBEDDING_SERVICE_PORT=3002
        export WEB_RETRIEVER_SERVICE_PORT=3003
        export RERANK_SERVICE_PORT=3005
        export LLM_SERVICE_PORT=3007
        export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:3008/v1/searchqna"


        sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

        # Start Docker Containers
        docker compose -f docker_compose.yaml up -d
        
        sleep 2m # Waits 2 minutes

    }


    function validate_megaservice() {
        result=$(http_proxy="" curl http://${ip_address}:3008/v1/searchqna -XPOST -d '{"messages": "What is the latest news? Give me also the source link", "stream": "False"}' -H 'Content-Type: application/json')
        echo $result

        if [[ $result == *"news"* ]]; then
            echo "Result correct."
        else
            docker logs web-retriever-chroma-server > ${LOG_PATH}/web-retriever-chroma-server.log
            docker logs searchqna-gaudi-backend-server > ${LOG_PATH}/searchqna-gaudi-backend-server.log
            docker logs tei-embedding-gaudi-server > ${LOG_PATH}/tei-embedding-gaudi-server.log
            docker logs embedding-tei-server > ${LOG_PATH}/embedding-tei-server.log
            echo "Result wrong."
            exit 1
        fi

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
        container_list=$(cat docker_compose.yaml | grep container_name | cut -d':' -f2)
        for container_name in $container_list; do
            cid=$(docker ps -aq --filter "name=$container_name")
            if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
        done
    }

    function main() {

        stop_docker
        build_docker_images
        # begin_time=$(date +%s)
        start_services
        # end_time=$(date +%s)
        # maximal_duration=$((end_time-begin_time))
        # echo "Mega service start duration is "$maximal_duration"s" && sleep 1s

        validate_megaservice
        validate_frontend

        stop_docker
        echo y | docker system prune

    }

    main
