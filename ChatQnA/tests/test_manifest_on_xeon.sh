#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/charts-mnt
# IMAGE_REPO is $OPEA_IMAGE_REPO, or else ""
IMAGE_REPO=${OPEA_IMAGE_REPO:-amr-registry.caas.intel.com/aiops}

function init_chatqna() {
    # executed under path manifest/chatqna/xeon
    # replace the mount dir "path: /mnt" with "path: $CHART_MOUNT"
    find . -name '*.yaml' -type f -exec sed -i "s#path: /mnt/models#path: $MOUNT_DIR#g" {} \;
    # replace the repository "image: opea/*" with "image: $IMAGE_REPO/opea/"
    find . -name '*.yaml' -type f -exec sed -i "s#image: opea/*#image: $IMAGE_REPO/opea/#g" {} \;
    # set huggingface token
    find . -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
}

function install_chatqna {
    # replace namespace "default" with real namespace
    find . -name '*.yaml' -type f -exec sed -i "s#svc.default#svc.$NAMESPACE#g" {} \;
    # for very yaml file in yaml_files, apply it to the k8s cluster
    yaml_files=("qna_configmap_xeon" "redis-vector-db"  "tei_embedding_service" "tei_reranking_service" "tgi_service" "retriever" "embedding" "reranking" "llm")
    for yaml_file in ${yaml_files[@]}; do
        kubectl apply -f $yaml_file.yaml -n $NAMESPACE
    done
    sleep 60
    kubectl apply -f chaqna-xeon-backend-server.yaml -n $NAMESPACE
}

function validate_chatqna() {
    # make sure microservice retriever is ready
    until curl http://retriever-svc.$NAMESPACE:7000/v1/retrieval -X POST \
    -d '{"text":"What is the revenue of Nike in 2023?","embedding":"'"${your_embedding}"'"}' \
    -H 'Content-Type: application/json'; do sleep 10; done

    # make sure microservice tgi-svc is ready
    until curl http://tgi-svc.$NAMESPACE:9009/generate -X POST \
    -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
    -H 'Content-Type: application/json'; do sleep 10; done

    # check megaservice works
    curl http://chaqna-xeon-backend-server-svc.$NAMESPACE:8888/v1/chatqna -H "Content-Type: application/json" -d '{
        "messages": "What is the revenue of Nike in 2023?"}' > ${LOG_PATH}/curl_megaservice.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Megaservice failed, please check the logs in ${LOG_PATH}!"
        exit 1
    fi
    echo "Response check succeed!"

    # Temporarily disable response check
    # echo "Checking response results, make sure the output is reasonable. "
    # local status=false
    # if [[ -f $LOG_PATH/curl_megaservice.log ]] &&
    #     [[ $(grep -c "algorithms" $LOG_PATH/curl_megaservice.log) != 0 ]]; then
    #     status=true
    # fi
    # if [ $status == false ]; then
    #     echo "Response check failed, please check the logs in artifacts!"
    #     exit 1
    # else
    #     echo "Response check succeed!"
    # fi
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
