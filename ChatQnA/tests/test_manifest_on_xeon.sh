#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-}
IMAGE_TAG=${IMAGE_TAG:-latest}

ROLLOUT_TIMEOUT_SECONDS="1800s"
KUBECTL_TIMEOUT_SECONDS="60s"

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
    kubectl apply -f chatqna.yaml -n $NAMESPACE
    # Sleep enough time for retreiver-usvc to be ready
    sleep 60
}

function get_end_point() {
    # $1 is service name, $2 is namespace
    ip_address=$(kubectl get svc $1 -n $2 -o jsonpath='{.spec.clusterIP}')
    port=$(kubectl get svc $1 -n $2 -o jsonpath='{.spec.ports[0].port}')
    echo "$ip_address:$port"
}

function validate_chatqna() {
    local ns=$1
    local log=$2
    max_retry=20
    # make sure microservice retriever-usvc is ready
    # try to curl retriever-svc for max_retry times
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    for ((i=1; i<=max_retry; i++))
    do
        endpoint_url=$(get_end_point "chatqna-retriever-usvc" $ns)
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
        endpoint_url=$(get_end_point "chatqna-tgi" $ns)
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
    endpoint_url=$(get_end_point "chatqna" $ns)
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


function _cleanup_ns() {
    local ns=$1
    if kubectl get ns $ns; then
      if ! kubectl delete ns $ns --timeout=$KUBECTL_TIMEOUT_SECONDS; then
        kubectl delete pods --namespace $ns --force --grace-period=0 --all
        kubectl delete ns $ns --force --grace-period=0 --timeout=$KUBECTL_TIMEOUT_SECONDS
      fi
    fi
}

function install_and_validate_chatqna_guardrail() {
    echo "Testing manifests chatqna_guardrils"
    local ns=${NAMESPACE}-gaurdrails
    _cleanup_ns $ns
    kubectl create namespace $ns
    # install guardrail
    kubectl apply -f chatqna-guardrails.yaml -n $ns
    # Sleep enough time for chatqna_guardrail to be ready
    sleep 60
    if kubectl rollout status deployment -n "$ns" --timeout "$ROLLOUT_TIMEOUT_SECONDS"; then
        echo "Waiting for cahtqna_guardrail pod ready done!"
    else
        echo "Timeout waiting for chatqna_guardrail pod ready!"
        _cleanup_ns $ns
        exit 1
    fi

    # validate guardrail
    validate_chatqna $ns chatqna-guardrails
    local ret=$?
    if [ $ret -ne 0 ]; then
        _cleanup_ns $ns
        exit 1
    fi
    _cleanup_ns $ns
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
        validate_chatqna $NAMESPACE chatqna
        ret=$?
        if [ $ret -ne 0 ]; then
            exit $ret
        fi
        pushd ChatQnA/kubernetes/manifests/xeon
        set +e
        install_and_validate_chatqna_guardrail
        popd
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
