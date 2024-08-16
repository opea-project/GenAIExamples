#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/charts-mnt
IMAGE_REPO=${IMAGE_REPO:-}
IMAGE_TAG=${IMAGE_TAG:-latest}

function init_codetrans() {
    # executed under path manifest/codetrans/xeon
    # replace the mount dir "path: /mnt/model" with "path: $CHART_MOUNT"
    find . -name '*.yaml' -type f -exec sed -i "s#path: /mnt/opea-models#path: $MOUNT_DIR#g" {} \;
    if [ $CONTEXT == "CI" ]; then
        # replace megaservice image tag
        find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/codetrans:latest#image: \"opea/codetrans:${IMAGE_TAG}#g" {} \;
    else
        # replace microservice image tag
        find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/\(.*\):latest#image: \"opea/\1:${IMAGE_TAG}#g" {} \;
    fi
    # replace the repository "image: opea/*" with "image: $IMAGE_REPO/opea/"
    find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/*#image: \"${IMAGE_REPO}opea/#g" {} \;
    # set huggingface token
    find . -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
}

function install_codetrans {
    echo "namespace is $NAMESPACE"
    kubectl apply -f . -n $NAMESPACE
}

function validate_codetrans() {
    ip_address=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    port=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    echo "try to curl http://${ip_address}:${port}/v1/codetrans..."

    # generate a random logfile name to avoid conflict among multiple runners
    LOGFILE=$LOG_PATH/curlmega_$NAMESPACE.log
    # Curl the Mega Service
    curl http://${ip_address}:${port}/v1/codetrans \
    -H 'Content-Type: application/json' \
    -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}' > $LOGFILE
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Megaservice codetrans failed, please check the logs in $LOGFILE!"
        exit 1
    fi

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOGFILE ]] && \
    [[ $(grep -c "print" $LOGFILE) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
    else
        echo "Response check succeed!"
    fi
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <function_name>"
    exit 1
fi

case "$1" in
    init_CodeTrans)
        pushd CodeTrans/kubernetes/manifests/xeon
        init_codetrans
        popd
        ;;
    install_CodeTrans)
        pushd CodeTrans/kubernetes/manifests/xeon
        NAMESPACE=$2
        install_codetrans
        popd
        ;;
    validate_CodeTrans)
        NAMESPACE=$2
        SERVICE_NAME=codetrans
        validate_codetrans
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
