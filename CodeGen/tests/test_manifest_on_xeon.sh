#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/charts-mnt
# IMAGE_REPO is $OPEA_IMAGE_REPO, or else ""
IMAGE_REPO=${OPEA_IMAGE_REPO:-amr-registry.caas.intel.com/aiops}

function init_codegen() {
    # executed under path manifest/codegen/xeon
    # replace the mount dir "path: /mnt/model" with "path: $CHART_MOUNT"
    find . -name '*.yaml' -type f -exec sed -i "s#path: /mnt#path: $MOUNT_DIR#g" {} \;
    # replace the repository "image: opea/*" with "image: $IMAGE_REPO/opea/"
    find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/*#image: \"$IMAGE_REPO/opea/#g" {} \;
    # set huggingface token
    find . -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
}

function install_codegen {
    echo "namespace is $NAMESPACE"
    kubectl apply -f . -n $NAMESPACE
}

function validate_codegen() {
    ip_address=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    port=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    echo "try to curl http://${ip_address}:${port}/v1/codegen..."
    # Curl the Mega Service
    curl http://${ip_address}:${port}/v1/codegen -H "Content-Type: application/json" -d '{
        "model": "ise-uiuc/Magicoder-S-DS-6.7B",
        "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."}' > curl_megaservice.log

    echo "Checking response results, make sure the output is reasonable. "
    local status=true
    if [[ -f curl_megaservice.log ]] && \
    [[ $(grep -c "billion" curl_megaservice.log) != 0 ]]; then
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
    init_CodeGen)
        pushd CodeGen/kubernetes/manifests/xeon
        init_codegen
        popd
        ;;
    install_CodeGen)
        pushd CodeGen/kubernetes/manifests/xeon
        NAMESPACE=$2
        install_codegen
        popd
        ;;
    validate_CodeGen)
        NAMESPACE=$2
        SERVICE_NAME=codegen
        validate_codegen
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
