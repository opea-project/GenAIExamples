#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-opea}
IMAGE_TAG=${IMAGE_TAG:-latest}

ROLLOUT_TIMEOUT_SECONDS="1800s"
KUBECTL_TIMEOUT_SECONDS="60s"

function init_chatqna() {
    # replace the mount dir "path: /mnt/opea-models" with "path: $CHART_MOUNT"
    find ../../kubernetes/intel/*/*/manifest -name '*.yaml' -type f -exec sed -i "s#path: /mnt/opea-models#path: $MOUNT_DIR#g" {} \;
    # replace microservice image tag
    find ../../kubernetes/intel/*/*/manifest -name '*.yaml' -type f -exec sed -i "s#image: \"opea/\(.*\):latest#image: \"opea/\1:${IMAGE_TAG}#g" {} \;
    # replace the repository "image: opea/*" with "image: $IMAGE_REPO/"
    find ../../kubernetes/intel/*/*/manifest -name '*.yaml' -type f -exec sed -i "s#image: \"opea/*#image: \"${IMAGE_REPO}/#g" {} \;
    # set huggingface token
    find ../../kubernetes/intel/*/*/manifest -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
}

function get_end_point() {
    # $1 is service name, $2 is namespace
    ip_address=$(kubectl get svc $1 -n $2 -o jsonpath='{.spec.clusterIP}')
    port=$(kubectl get svc $1 -n $2 -o jsonpath='{.spec.ports[0].port}')
    echo "$ip_address:$port"
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


if [ $# -eq 0 ]; then
    echo "Usage: $0 <function_name>"
    exit 1
fi

case "$1" in
    init_ChatQnA)
        init_chatqna
        ;;
    get_end_point)
        service=$2
        NAMESPACE=$3
        get_end_point $service $NAMESPACE
        ;;
    _cleanup_ns)
        NAMESPACE=$2
        _cleanup_ns $NAMESPACE
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
