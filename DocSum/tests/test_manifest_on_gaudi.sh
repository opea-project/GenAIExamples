#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-}
IMAGE_TAG=${IMAGE_TAG:-latest}

function init_docsum() {
    # executed under path manifest/docsum/xeon
    # replace the mount dir "path: /mnt/model" with "path: $CHART_MOUNT"
    find . -name '*.yaml' -type f -exec sed -i "s#path: /mnt/opea-models#path: $MOUNT_DIR#g" {} \;
    if [ $CONTEXT == "CI" ]; then
        # replace megaservice image tag
        find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/docsum:latest#image: \"opea/docsum:${IMAGE_TAG}#g" {} \;
    else
        # replace microservice image tag
        find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/\(.*\):latest#image: \"opea/\1:${IMAGE_TAG}#g" {} \;
    fi
    # replace the repository "image: opea/*" with "image: $IMAGE_REPO/opea/"
    find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/*#image: \"${IMAGE_REPO}opea/#g" {} \;
    # set huggingface token
    find . -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
}

function install_docsum {
    echo "namespace is $NAMESPACE"
    kubectl apply -f . -n $NAMESPACE
}

function validate_docsum() {
    ip_address=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    port=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    echo "try to curl http://${ip_address}:${port}/v1/docsum..."

    # generate a random logfile name to avoid conflict among multiple runners
    LOGFILE=$LOG_PATH/curlmega_$NAMESPACE.log
    # Curl the Mega Service
    curl http://${ip_address}:${port}/v1/docsum \
    -H 'Content-Type: application/json' \
    -d '{"messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' > $LOGFILE
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Megaservice docsum failed, please check the logs in $LOGFILE!"
        exit 1
    fi

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOGFILE ]] && \
    [[ $(grep -c "versatile toolkit" $LOGFILE) != 0 ]]; then
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
    init_DocSum)
        pushd DocSum/kubernetes/manifests/gaudi
        init_docsum
        popd
        ;;
    install_DocSum)
        pushd DocSum/kubernetes/manifests/gaudi
        NAMESPACE=$2
        install_docsum
        popd
        ;;
    validate_DocSum)
        NAMESPACE=$2
        SERVICE_NAME=docsum
        validate_docsum
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
