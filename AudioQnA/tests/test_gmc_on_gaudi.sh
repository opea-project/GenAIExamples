#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-}

function install_audioqa() {
    kubectl create ns $APP_NAMESPACE
    sed -i "s|namespace: audioqa|namespace: $APP_NAMESPACE|g"  ./audioQnA_gaudi.yaml
    kubectl apply -f ./audioQnA_gaudi.yaml

    # Wait until the router service is ready
    echo "Waiting for the audioqa router service to be ready..."
    wait_until_pod_ready "audioqa router" $APP_NAMESPACE "router-service"
    output=$(kubectl get pods -n $APP_NAMESPACE)
    echo $output
}

function validate_audioqa() {
    # deploy client pod for testing
    kubectl create deployment client-test -n $APP_NAMESPACE --image=python:3.8.13 -- sleep infinity

    # wait for client pod ready
    wait_until_pod_ready "client-test" $APP_NAMESPACE "client-test"
    # giving time to populating data
    sleep 60

    kubectl get pods -n $APP_NAMESPACE
    # send request to audioqa
    export CLIENT_POD=$(kubectl get pod -n $APP_NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})
    echo "$CLIENT_POD"
    accessUrl=$(kubectl get gmc -n $APP_NAMESPACE -o jsonpath="{.items[?(@.metadata.name=='audioqa')].status.accessUrl}")
    byte_str=$(kubectl exec "$CLIENT_POD" -n $APP_NAMESPACE -- curl $accessUrl -s -X POST  -d '{"byte_str": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "parameters":{"max_new_tokens":64, "do_sample": true, "streaming":false}}' -H 'Content-Type: application/json' | jq .byte_str)
    echo "$byte_str" > $LOG_PATH/curl_audioqa.log
    if [ -z "$byte_str" ]; then
	echo "audioqa failed, please check the logs in ${LOG_PATH}!"
        exit 1
    fi
    echo "Audioqa response check succeed!"
}

function wait_until_pod_ready() {
    echo "Waiting for the $1 to be ready..."
    max_retries=30
    retry_count=0
    while ! is_pod_ready $2 $3; do
        if [ $retry_count -ge $max_retries ]; then
            echo "$1 is not ready after waiting for a significant amount of time"
            get_gmc_controller_logs
            exit 1
        fi
        echo "$1 is not ready yet. Retrying in 10 seconds..."
        sleep 10
        output=$(kubectl get pods -n $2)
        echo $output
        retry_count=$((retry_count + 1))
    done
}

function is_pod_ready() {
    if [ "$2" == "gmc-controller" ]; then
      pod_status=$(kubectl get pods -n $1 -o jsonpath='{.items[].status.conditions[?(@.type=="Ready")].status}')
    else
      pod_status=$(kubectl get pods -n $1 -l app=$2 -o jsonpath='{.items[].status.conditions[?(@.type=="Ready")].status}')
    fi
    if [ "$pod_status" == "True" ]; then
        return 0
    else
        return 1
    fi
}

function get_gmc_controller_logs() {
    # Fetch the name of the pod with the app-name gmc-controller in the specified namespace
    pod_name=$(kubectl get pods -n $SYSTEM_NAMESPACE -l control-plane=gmc-controller -o jsonpath='{.items[0].metadata.name}')

    # Check if the pod name was found
    if [ -z "$pod_name" ]; then
        echo "No pod found with app-name gmc-controller in namespace $SYSTEM_NAMESPACE"
        return 1
    fi

    # Get the logs of the found pod
    echo "Fetching logs for pod $pod_name in namespace $SYSTEM_NAMESPACE..."
    kubectl logs $pod_name -n $SYSTEM_NAMESPACE
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <function_name>"
    exit 1
fi

case "$1" in
    install_AudioQnA)
        pushd AudioQnA/kubernetes
        install_audioqa
        popd
        ;;
    validate_AudioQnA)
        pushd AudioQnA/kubernetes
        validate_audioqa
        popd
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
