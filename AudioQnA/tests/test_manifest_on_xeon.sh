#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-opea}
IMAGE_TAG=${IMAGE_TAG:-latest}

function init_audioqna() {
    # executed under path manifest/audioqna/xeon
    # replace the mount dir "path: /mnt/model" with "path: $CHART_MOUNT"
    find . -name '*.yaml' -type f -exec sed -i "s#path: /mnt/opea-models#path: $MOUNT_DIR#g" {} \;
    # replace microservice image tag
    find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/\(.*\):latest#image: \"opea/\1:${IMAGE_TAG}#g" {} \;
    # replace the repository "image: opea/*" with "image: $IMAGE_REPO/opea/"
    find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/*#image: \"${IMAGE_REPO}/#g" {} \;
    # set huggingface token
    find . -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
}

function install_audioqna {
    echo "namespace is $NAMESPACE"
    kubectl apply -f audioqna.yaml -n $NAMESPACE
}

function validate_audioqna() {
    ip_address=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    port=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    echo "try to curl http://${ip_address}:${port}/v1/audioqna..."

    # generate a random logfile name to avoid conflict among multiple runners
    LOGFILE=$LOG_PATH/curlmega_$NAMESPACE.log
    # Curl the Mega Service
    curl http://${ip_address}:${port}/v1/audioqna \
    -X POST \
    -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64, "voice":"default"}' \
    -H 'Content-Type: application/json' | sed 's/^"//;s/"$//' | base64 -d > speech.mp3

    if [[ $(file speech.mp3) == *"RIFF"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        return 1
    fi
    return 0
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <function_name>"
    exit 1
fi

case "$1" in
    init_AudioQnA)
        pushd AudioQnA/kubernetes/intel/cpu/xeon/manifest
        init_audioqna
        popd
        ;;
    install_AudioQnA)
        pushd AudioQnA/kubernetes/intel/cpu/xeon/manifest
        NAMESPACE=$2
        install_audioqna
        popd
        ;;
    validate_AudioQnA)
        NAMESPACE=$2
        SERVICE_NAME=audioqna
        validate_audioqna
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
