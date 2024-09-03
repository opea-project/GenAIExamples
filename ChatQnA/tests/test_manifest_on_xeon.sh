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
    # replace the mount dir "path: /mnt/opea-models" with "path: $CHART_MOUNT"
    find . -name '*.yaml' -type f -exec sed -i "s#path: /mnt/opea-models#path: $MOUNT_DIR#g" {} \;
    if [ $CONTEXT == "CI" ]; then
        # replace megaservice image tag
        find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/chatqna:latest#image: \"opea/chatqna:${IMAGE_TAG}#g" {} \;
    else
        # replace microservice image tag
        find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/\(.*\):latest#image: \"opea/\1:${IMAGE_TAG}#g" {} \;
    fi
    # replace the repository "image: opea/*" with "image: $IMAGE_REPO/opea/"
    find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/*#image: \"${IMAGE_REPO}opea/#g" {} \;
    # set huggingface token
    find . -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
}

function install_chatqna {
    echo "namespace is $NAMESPACE"
    kubectl apply -f . -n $NAMESPACE
    # Sleep enough time for retreiver-usvc to be ready
    sleep 60
}

function validate_chatqna() {
    max_retry=20
    # make sure microservice retriever-usvc is ready
    # try to curl retriever-svc for max_retry times
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    for ((i=1; i<=max_retry; i++))
    do
        curl http://chatqna-retriever-usvc.$NAMESPACE:7000/v1/retrieval -X POST \
            -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}" \
            -H 'Content-Type: application/json' && break
        sleep 30
    done
    # if i is bigger than max_retry, then exit with error
    if [ $i -gt $max_retry ]; then
        echo "Microservice retriever failed, exit with error."
        exit 1
    fi
    # make sure microservice tgi-svc is ready
    for ((i=1; i<=max_retry; i++))
    do
        curl http://chatqna-tgi.$NAMESPACE:80/generate -X POST \
            -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
            -H 'Content-Type: application/json' && break
        sleep 10
    done
    # if i is bigger than max_retry, then exit with error
    if [ $i -gt $max_retry ]; then
        echo "Microservice tgi failed, exit with error."
        exit 1
    fi

    # check megaservice works
    # generate a random logfile name to avoid conflict among multiple runners
    LOGFILE=$LOG_PATH/curlmega_$NAMESPACE.log
    curl http://chatqna.$NAMESPACE:8888/v1/chatqna -H "Content-Type: application/json" -d '{"messages": "What is the revenue of Nike in 2023?"}' > $LOGFILE
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Megaservice failed, please check the logs in $LOGFILE!"
        exit 1
    fi

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOGFILE ]] &&
        [[ $(grep -c "\[DONE\]" $LOGFILE) != 0 ]]; then
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
        pushd ChatQnA/kubernetes/manifests/xeon
        init_chatqna
        popd
        ;;
    install_ChatQnA)
        pushd ChatQnA/kubernetes/manifests/xeon
        NAMESPACE=$2
        install_chatqna
        popd
        ;;
    validate_ChatQnA)
        NAMESPACE=$2
        SERVICE_NAME=chatqna
        validate_chatqna
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
