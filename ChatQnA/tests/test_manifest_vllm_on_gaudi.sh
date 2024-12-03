#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-opea}
IMAGE_TAG=${IMAGE_TAG:-latest}

ROLLOUT_TIMEOUT_SECONDS="1800s"
KUBECTL_TIMEOUT_SECONDS="60s"

function validate_chatqna() {
    local ns=$1
    local log=$2
    max_retry=20
    # make sure microservice retriever-usvc is ready
    # try to curl retriever-svc for max_retry times
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    for ((i=1; i<=max_retry; i++))
    do
        endpoint_url=$(bash ChatQnA/tests/common/_test_manifast_utils.sh get_end_point  "chatqna-retriever-usvc" $ns)
        curl http://$endpoint_url/v1/retrieval -X POST \
            -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}" \
            -H 'Content-Type: application/json' && break
        sleep 30
    done
    # if i is bigger than max_retry, then exit with error
    if [ $i -gt $max_retry ]; then
        echo "Microservice retriever failed, exit with error."
        return 1
    fi

    # make sure microservice vllm-svc is ready
    for ((i=1; i<=max_retry; i++))
    do
        endpoint_url=$(bash ChatQnA/tests/common/_test_manifast_utils.sh get_end_point  "chatqna-vllm" $ns)
        curl http://$endpoint_url/v1/chat/completions -X POST \
            -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}]}' \
            -H 'Content-Type: application/json' && break
        sleep 30
    done
    # if i is bigger than max_retry, then exit with error
    if [ $i -gt $max_retry ]; then
        echo "Microservice vllm failed, exit with error."
        return 1
    fi

    # check megaservice works
    # generate a random logfile name to avoid conflict among multiple runners
    LOGFILE=$LOG_PATH/curlmega_$log.log
    endpoint_url=$(bash ChatQnA/tests/common/_test_manifast_utils.sh get_end_point  "chatqna" $ns)
    curl http://$endpoint_url/v1/chatqna -H "Content-Type: application/json" -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": "What is the revenue of Nike in 2023?"}' > $LOGFILE
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Megaservice failed, please check the logs in $LOGFILE!"
        return ${exit_code}
    fi

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOGFILE ]] &&
        [[ $(grep -c "\[DONE\]" $LOGFILE) != 0 ]]; then
        status=true
    fi
    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        return 1
    else
        echo "Response check succeed!"
    fi
    return 0
}

function install_chatqna() {
    echo "Testing manifests chatqna_vllm"
    local ns=$1
    bash ChatQnA/tests/common/_test_manifast_utils.sh _cleanup_ns $ns
    kubectl create namespace $ns
    # install guardrail
    pushd ChatQnA/kubernetes/intel/hpu/gaudi/manifest
    kubectl apply -f chatqna-vllm.yaml -n $ns
    # Sleep enough time for chatqna_vllm to be ready, vllm warmup takes about 5 minutes
    sleep 280
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <function_name>"
    exit 1
fi

case "$1" in
    init_ChatQnA)
        pushd ChatQnA/tests/common
        bash _test_manifast_utils.sh init_ChatQnA
        popd
        ;;
    install_ChatQnA)
        NAMESPACE=$2
        install_chatqna $NAMESPACE
        popd
        ;;
    validate_ChatQnA)
        NAMESPACE=$2
        SERVICE_NAME=chatqna-vllm
        validate_chatqna $NAMESPACE chatqna-vllm
        ret=$?
        if [ $ret -ne 0 ]; then
            exit $ret
        fi
        ;;

    *)
        echo "Unknown function: $1"
        ;;
esac
