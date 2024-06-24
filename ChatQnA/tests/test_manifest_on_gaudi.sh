#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-}
IMAGE_TAG=${IMAGE_TAG:-latest}

function init_chatqna() {
    # replace the mount dir "path: /mnt" with "path: $CHART_MOUNT"
    find . -name '*.yaml' -type f -exec sed -i "s#path: /mnt/models#path: $MOUNT_DIR#g" {} \;
    # replace megaservice image tag
    find . -name '*.yaml' -type f -exec sed -i "s#image: opea/chatqna:latest#image: opea/chatqna:${IMAGE_TAG}#g" {} \;
    # replace the repository "image: opea/*" with "image: $IMAGE_REPO/opea/"
    find . -name '*.yaml' -type f -exec sed -i "s#image: opea/*#image: ${IMAGE_REPO}opea/#g" {} \;
    # set huggingface token
    find . -name '*.yaml' -type f -exec sed -i "s#\${HUGGINGFACEHUB_API_TOKEN}#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
}

function install_chatqna {
    # replace namespace "default" with real namespace
    find . -name '*.yaml' -type f -exec sed -i "s#default.svc#$NAMESPACE.svc#g" {} \;
    # for very yaml file in yaml_files, apply it to the k8s cluster
    yaml_files=("qna_configmap_gaudi" "redis-vector-db"  "tei_embedding_gaudi_service" "tei_reranking_service" "tgi_gaudi_service" "retriever" "embedding" "reranking" "llm")
    for yaml_file in ${yaml_files[@]}; do
        kubectl apply -f $yaml_file.yaml -n $NAMESPACE
    done
    sleep 60
    kubectl apply -f chaqna-xeon-backend-server.yaml -n $NAMESPACE
}

function validate_chatqna() {
    max_retry=20
    # make sure microservice retriever is ready
    # try to curl retriever-svc for max_retry times
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    for ((i=1; i<=max_retry; i++))
    do
        curl http://retriever-svc.$NAMESPACE:7000/v1/retrieval -X POST \
            -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}" \
            -H 'Content-Type: application/json' && break
        sleep 10
    done
    # make sure microservice tgi-svc is ready
    for ((i=1; i<=max_retry; i++))
    do
        curl http://tgi-gaudi-svc.$NAMESPACE:9009/generate -X POST \
            -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
            -H 'Content-Type: application/json' && break
        sleep 10
    done
    # if i is bigger than max_retry, then exit with error
    if [ $i -gt $max_retry ]; then
        echo "Microservice failed, exit with error."
        exit 1
    fi

    # check megaservice works
    # generate a random logfile name to avoid conflict among multiple runners
    LOGFILE=$LOG_PATH/curlmega_$NAMESPACE.log
    curl http://chaqna-xeon-backend-server-svc.$NAMESPACE:8888/v1/chatqna -H "Content-Type: application/json" -d '{
        "messages": "What is the revenue of Nike in 2023?"}' > $LOGFILE
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Megaservice failed, please check the logs in $LOGFILE!"
        exit 1
    fi

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOGFILE ]] &&
        [[ $(grep -c "billion" $LOGFILE) != 0 ]]; then
        status=true
    fi
    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        exit 1
    else
        echo "Response check succeed!"
    fi
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <function_name>"
    exit 1
fi

case "$1" in
    init_ChatQnA)
        pushd ChatQnA/kubernetes/manifests
        init_chatqna
        popd
        ;;
    install_ChatQnA)
        pushd ChatQnA/kubernetes/manifests
        NAMESPACE=$2
        install_chatqna
        popd
        ;;
    validate_ChatQnA)
        NAMESPACE=$2
        SERVICE_NAME=chaqna-xeon-backend-server-svc
        validate_chatqna
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
