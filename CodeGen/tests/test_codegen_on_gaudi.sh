# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/llm-tgi:latest -f comps/llms/text-generation/tgi/Dockerfile .

    docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1

    cd $WORKPATH
    docker build --no-cache -t opea/codegen:latest -f Dockerfile .

    cd $WORKPATH/ui
    docker build --no-cache -t opea/codegen-ui:latest -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/docker-composer/gaudi

    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TGI_LLM_ENDPOINT="http://${ip_address}:8028"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:6666/v1/codegen"

    # Start Docker Containers
    # TODO: Replace the container name with a test-specific name
    docker compose -f docker_compose.yaml up -d

    sleep 2m # Waits 2 minutes
}

function validate_microservices() {
    # Check if the microservices are running correctly.
    # TODO: Any results check required??

    export PATH="${HOME}/miniforge3/bin:$PATH"

    curl http://${ip_address}:8028/generate \
        -X POST \
        -d '{"inputs":"def print_hello_world():","parameters":{"max_new_tokens":1024, "do_sample": true}}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/generate.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs tgi-gaudi-server >> ${LOG_PATH}/generate.log
        exit 1
    fi
    sleep 5s

    curl http://${ip_address}:9000/v1/chat/completions \
        -X POST \
        -d '{"text":"def print_hello_world():"}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/completions.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs llm-tgi-gaudi-server >> ${LOG_PATH}/completions.log
        exit 1
    fi
    sleep 5s
}

function validate_megaservice() {
    # Curl the Mega Service
    curl http://${ip_address}:6666/v1/codegen -H "Content-Type: application/json" -d '{
        "model": "ise-uiuc/Magicoder-S-DS-6.7B",
        "messages": "def print_hello_world():"}' > ${LOG_PATH}/curl_megaservice.log

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOG_PATH/curl_megaservice.log ]] && \
    [[ $(grep -c "Hello" $LOG_PATH/curl_megaservice.log) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        exit 1
    else
        echo "Response check succeed!"
    fi

    echo "Checking response format, make sure the output format is acceptable for UI."
    # TODO
}

function stop_docker() {
    cd $WORKPATH/docker-composer/gaudi
    container_list=$(cat docker_compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    done
}

function main() {

    stop_docker

    build_docker_images
    start_services

    validate_microservices
    validate_megaservice

    stop_docker
    echo y | docker system prune

}

main
