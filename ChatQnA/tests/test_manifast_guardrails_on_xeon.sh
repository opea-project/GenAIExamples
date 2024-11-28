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
    max_retry=10
    # make sure microservice retriever-usvc is ready
    # try to curl retriever-svc for max_retry times
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    for ((i=1; i<=max_retry; i++))
    do
        endpoint_url=$(bash common/function.sh get_end_point  "chatqna-retriever-usvc" $ns)
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
    # make sure microservice tgi-svc is ready
    for ((i=1; i<=max_retry; i++))
    do
        endpoint_url=$(bash common/function.sh get_end_point  "chatqna-tgi" $ns)
        curl http://$endpoint_url/generate -X POST \
            -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
            -H 'Content-Type: application/json' && break
        sleep 30
    done
    # if i is bigger than max_retry, then exit with error
    if [ $i -gt $max_retry ]; then
        echo "Microservice tgi failed, exit with error."
        return 1
    fi

    # check megaservice works
    # generate a random logfile name to avoid conflict among multiple runners
    LOGFILE=$LOG_PATH/curlmega_$log.log
    endpoint_url=$(bash common/function.sh get_end_point  "chatqna" $ns)
    curl http://$endpoint_url/v1/chatqna -H "Content-Type: application/json" -d '{"messages": "What is the revenue of Nike in 2023?"}' > $LOGFILE
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

function main() {
    echo "Testing manifests chatqna_guardrils"
    local ns=$1
    pushd ChatQnA/kubernetes/intel/cpu/xeon/manifest
    bash common/function.sh _cleanup_ns $ns
    bash common/function.sh init_chatqna
    kubectl create namespace $ns
    # install guardrail
    kubectl apply -f chatqna-guardrails.yaml -n $ns
    # Sleep enough time for chatqna_guardrail to be ready
    sleep 60
    if kubectl rollout status deployment -n "$ns" --timeout "$ROLLOUT_TIMEOUT_SECONDS"; then
        echo "Waiting for chatqna_guardrail pod ready done!"
    else
        echo "Timeout waiting for chatqna_guardrail pod ready!"
        exit 1
    fi

    # validate guardrail
    validate_chatqna $ns chatqna-guardrails
    local ret=$?
    if [ $ret -ne 0 ]; then
        exit 1
    fi
    popd
}

main $1